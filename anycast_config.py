#!/usr/bin/python3

# Copyright 2018 BlueCat Networks. All rights reserved.

import base64
import functools
import getpass
import json
import os.path
import sys
from argparse import ArgumentParser
from http import HTTPStatus

import urllib3
import requests

from requests.auth import HTTPBasicAuth
from flask import session
from .config import conf

urllib3.disable_warnings()

PROG = sys.argv[0]

DAEMONS = ('zebra', 'ospfd', 'bgpd')

DEBUG_INFOS = (
    'zebraSummary', 'bgpSummary', 'bgpNeighbors',
    'ospfNeighbors', 'ospfRoutes', 'routes',
    'interfaces', 'ospfRouterInfo', 'runningConfig',
    'ospfDatabase'
)

DAEMONS_STRING = '{ ' \
                    + functools.reduce(lambda x, y: x + ' | ' + y, DAEMONS) \
                    + ' }'

DEBUG_INFOS_STRING = '{ ' \
                        + functools.reduce(lambda x, y: x + ' | ' + y,
                                           DEBUG_INFOS) \
                        + ' }'

# Argument setup

# Globals

DEFAULT_HTTPS_PORT = 443

# Endpoints

DAEMONS_RUNNING_ENDPOINT \
    = 'https://{}:{}/v1/routing/anycast/configuration/daemons/running'

DAEMONS_STAGED_ENDPOINT \
    = 'https://{}:{}/v1/routing/anycast/configuration/daemons/staged'

CONF_STAGED_ENDPOINT \
    = 'https://{}:{}/v1/routing/anycast/configuration/{}/staged'

CONF_RUNNING_ENDPOINT \
    = 'https://{}:{}/v1/routing/anycast/configuration/{}/running'

APPLY_ENDPOINT = 'https://{}:{}/v1/routing/anycast/configuration/apply'

DEBUG_ENDPOINT = 'https://{}:{}/v1/routing/anycast/debug?{}'

LOGS_ENDPOINT = 'https://{}:{}/v1/routing/anycast/logs/{}'

NETWORKING_ENDPOINT = 'https://{}:{}/v1/routing/networking/configuration/'

# Helpers to handle the minor logic


def get_input(input_name):
    return input(input_name + ':')


def get_secret_key():
    return getpass.getpass('Secret Access Key:')


def write_script_config(content):
    file_path = os.path.join(conf.get('processing_folder'),
                             session['folder_name'],
                             '.script_config')
    print('credentials are written to :', file_path)
    try:
        print('Trying to write a file')
        with open(file_path, 'w') as file:
            file.write(base64.b64encode(
                bytes(content, 'utf-8'))
                        .decode('ascii'))
    except IOError as e:
        print(e)
        raise e


def extract_credentials():
    contents = None
    file_path = os.path.join(conf.get('processing_folder'),
                             session['folder_name'],
                             '.script_config')
    print('extracting credentials for : ', file_path)
    try:
        print('Trying to read the file')
        with open(file_path, 'r') as file:
            base64_contents = file.read()
            contents = base64.standard_b64decode(
                bytes(base64_contents, 'ascii')).decode('ascii').split('\n')
            assert len(contents) == 4
    except (IOError, AssertionError) as e:
        print(e)
        raise e
    contents[-1] = int(contents[-1])
    return contents


def get_file_contents(filename):
    try:
        with open(filename, 'r') as file:
            return file.read()
    except IOError as e:
        raise e


def get_existing_daemons_file(client_id, secret_key, service_point_ip, port):
    """
    Retrieves the appropriate daemons file contents.
    Returns an existing daemons file if there is one,
    checking for staged first.
    If neither exist, it returns a file with all daemons disabled.
    """
    try:
        staged_daemons_file_response = requests.get(
            DAEMONS_STAGED_ENDPOINT.format(service_point_ip, port),
            auth=HTTPBasicAuth(client_id, secret_key),
            verify=False)

        if staged_daemons_file_response.status_code == HTTPStatus.OK:
            return staged_daemons_file_response.text

        running_daemons_file_response = requests.get(
            DAEMONS_RUNNING_ENDPOINT.format(service_point_ip, port),
            auth=HTTPBasicAuth(client_id, secret_key),
            verify=False)

        if running_daemons_file_response.status_code == HTTPStatus.OK:
            return running_daemons_file_response.text
    except (ConnectionError, TimeoutError) as e:
        raise e

    return 'zebra=no\nospfd=no\nbgpd=no'


def generate_daemons_file(client_id, secret_key, service_point_ip,
                          port, daemon, disable):
    """
    Generate the contents of a daemons file.
    This behaviour depends on the existing one and the given daemon
        to activate/deactivate as per the disable flag.
    This will check the staged file before the running one and
        then a default (all daemons set to no).
    """
    try:
        daemons_file_content \
            = get_existing_daemons_file(client_id, secret_key,
                                        service_point_ip, port)
        if not daemons_file_content.strip():
            daemons_file_content = 'zebra=no\nospfd=no\nbgpd=no'
        return daemons_file_content.replace(daemon+'=yes', daemon+'=no')\
            if disable \
            else daemons_file_content.replace(daemon+'=no', daemon+'=yes')
    except (ConnectionError, TimeoutError) as e:
        raise e


def send_get(url, client_id, secret_key):
    response = requests.get(url, auth=HTTPBasicAuth(client_id, secret_key),
                            verify=False)
    print(response)
    return response


def send_put(url, client_id, secret_key, content):
    return requests.put(url, auth=HTTPBasicAuth(client_id, secret_key),
                        verify=False, data=content)


def send_post(url, client_id, secret_key, content):
    return requests.post(url, auth=HTTPBasicAuth(client_id, secret_key),
                         verify=False, data=content)


def send_delete(url, client_id, secret_key):
    return requests.delete(url, auth=HTTPBasicAuth(client_id, secret_key),
                           verify=False)


def send_apply_call(client_id, secret_key, service_point_ip, port):
    return send_post(APPLY_ENDPOINT.format(service_point_ip, port),
                     client_id, secret_key, '')


def stage_daemons_file(daemon, disable, client_id,
                       secret_key, service_point_ip, port):
    daemons_file_content = generate_daemons_file(client_id, secret_key,
                                                 service_point_ip, port,
                                                 daemon, disable)
    return send_put(DAEMONS_STAGED_ENDPOINT.format(
                        service_point_ip, port),
                    client_id, secret_key, daemons_file_content)


def handle_api_response(response, suppress, text_handling_func=None):
    """
    Handles the output from API calls.  If a text_handling_func is given,
        it uses that to parse the response text,
    otherwise prints the response text.
    """
    if response.status_code == HTTPStatus.NO_CONTENT \
            or response.status_code == HTTPStatus.OK:
        if not suppress:
            print('Success.')
            if response.text is not None:
                if text_handling_func is None:
                    print(response.text)
                    return response.text
                else:
                    return text_handling_func(response.text)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise requests.HTTPError('Unauthorized.')
    elif response.status_code == HTTPStatus.BAD_REQUEST:
        raise requests.HTTPError('Invalid parameters.')
    else:
        raise requests.HTTPError(response.text)


def handle_show_debug_output(output):
    output_dict = json.loads(output)
    eventType_Output \
        = 'Event type: ' + output_dict['events'][0]['metadata']['eventType']
    event_output = output_dict['events'][0]['event']
    print(eventType_Output + '\n' + event_output)
    return eventType_Output + '\n' + event_output


def authenticate(func):
    def wrapper(*args, **kwargs):
        file_path = os.path.join(conf.get('processing_folder'),
                                 session['folder_name'],
                                 '.script_config')
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            client_id = session.get('clientID', '')
            secret_key = session.get('password', '')
            service_point_ip = session.get('ip_address', '')
            port = session.get('port', '')
            write_script_config(client_id + '\n' + secret_key + '\n' +
                                service_point_ip + '\n' + str(port))
            return func(*args, **kwargs, client_id=client_id,
                        secret_key=secret_key,
                        service_point_ip=service_point_ip, port=port)
        else:
            client_id, secret_key, service_point_ip, port \
                    = extract_credentials()
            return func(*args, **kwargs, client_id=client_id,
                        secret_key=secret_key,
                        service_point_ip=service_point_ip, port=port)
    return wrapper


@authenticate
def do_pause_start_daemon(daemon, disable, client_id=None, secret_key=None,
                          service_point_ip=None, port=443):
    handle_api_response(
        stage_daemons_file(daemon, disable, client_id, secret_key,
                           service_point_ip, port), True)
    handle_api_response(
        send_apply_call(client_id, secret_key, service_point_ip, port), False)


@authenticate
def do_show_daemons(client_id=None, secret_key=None,
                    service_point_ip=None, port=443):
    return handle_api_response(
        send_get(DAEMONS_RUNNING_ENDPOINT.format(service_point_ip, port),
                 client_id, secret_key), False)


@authenticate
def do_set_staged_conf(daemon, file, client_id=None, secret_key=None,
                       service_point_ip=None, port=443):
    """
    Stage the given daemon's conf file while also adjusting and
        staging the daemons file accordingly.
    """
    contents = get_file_contents(file)
    handle_api_response(
        stage_daemons_file(daemon, False, client_id, secret_key,
                           service_point_ip, port), True)
    handle_api_response(
        send_put(CONF_STAGED_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key, contents), False)


@authenticate
def do_show_staged_conf(daemon, client_id=None, secret_key=None,
                        service_point_ip=None, port=443):
    return handle_api_response(
        send_get(CONF_STAGED_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key), False)


@authenticate
def do_no_staged_conf(daemon, client_id=None, secret_key=None,
                      service_point_ip=None, port=443):
    """
    Unstage the given daemon's conf file while also adjusting
        and staging the daemons file accordingly.
    """
    handle_api_response(
        stage_daemons_file(daemon, False, client_id, secret_key,
                           service_point_ip, port), True)
    handle_api_response(
        send_delete(
            CONF_STAGED_ENDPOINT.format(service_point_ip, port, daemon),
            client_id, secret_key), False)


@authenticate
def do_apply(client_id=None, secret_key=None, service_point_ip=None, port=443):
    handle_api_response(
        send_post(
            APPLY_ENDPOINT.format(service_point_ip, port),
            client_id, secret_key, ''), False)


@authenticate
def do_set_run_conf(daemon, file, client_id=None, secret_key=None,
                    service_point_ip=None, port=443):
    contents = get_file_contents(file)
    handle_api_response(
        stage_daemons_file(daemon, False, client_id,
                           secret_key, service_point_ip, port), True)
    handle_api_response(
        send_put(CONF_STAGED_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key, contents), True)
    handle_api_response(
        send_apply_call(client_id, secret_key, service_point_ip, port), False)


@authenticate
def do_show_run_conf(daemon, client_id=None, secret_key=None,
                     service_point_ip=None, port=443):
    return handle_api_response(
        send_get(CONF_RUNNING_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key), False)


@authenticate
def do_no_run_conf(daemon, client_id=None, secret_key=None,
                   service_point_ip=None, port=443):
    handle_api_response(
        stage_daemons_file(daemon, True, client_id, secret_key,
                           service_point_ip, port), True)
    handle_api_response(
        send_put(CONF_STAGED_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key, ''), True)
    handle_api_response(
        send_apply_call(client_id, secret_key, service_point_ip, port), False)


@authenticate
def do_show_debug(option, client_id=None, secret_key=None,
                  service_point_ip=None, port=443):
    return handle_api_response(
        send_get(DEBUG_ENDPOINT.format(service_point_ip, port,
                 'option={}'.format(option)), client_id, secret_key),
        False,
        text_handling_func=handle_show_debug_output)


@authenticate
def do_show_logs(daemon, client_id=None, secret_key=None,
                 service_point_ip=None, port=443):
    handle_api_response(
        send_get(LOGS_ENDPOINT.format(service_point_ip, port, daemon),
                 client_id, secret_key), False)


@authenticate
def do_set_loopbacks(loopbacks, client_id=None, secret_key=None,
                     service_point_ip=None, port=443):
    additional_loopbacks = {}
    additional_loopbacks['additionalLoopbacks'] = loopbacks
    handle_api_response(
        send_put(NETWORKING_ENDPOINT.format(service_point_ip, port),
                 client_id, secret_key, json.dumps(additional_loopbacks)),
        False)


@authenticate
def do_show_loopbacks(client_id=None, secret_key=None,
                      service_point_ip=None, port=443):
    handle_api_response(
        send_get(NETWORKING_ENDPOINT.format(service_point_ip, port),
                 client_id, secret_key),
        False)


@authenticate
def do_no_loopbacks(client_id=None, secret_key=None,
                    service_point_ip=None, port=443):
    handle_api_response(
        send_delete(NETWORKING_ENDPOINT.format(service_point_ip, port),
                    client_id, secret_key), False)


def main(args):
    print(args)
    action = args.get('action', '')
    daemon = args.get('daemon', '')
    file = args.get('file', '')
    loopbacks = args.get('loopbacks', '')
    option = args.get('option', '')
    try:
        if action is None:
            return ('Must supply a command.  Run <python> \
                     anycast_config.py -h for help.')
        elif action == 'pause':
            return do_pause_start_daemon(daemon, True)
        elif action == 'start':
            return do_pause_start_daemon(daemon, False)
        elif action == 'show_daemons':
            return do_show_daemons()
        elif action == 'set_staged_conf':
            return do_set_staged_conf(daemon, file)
        elif action == 'show_staged_conf':
            print(action)
            return do_show_staged_conf(daemon)
        elif action == 'no_staged_conf':
            return do_no_staged_conf(daemon)
        elif action == 'apply':
            return do_apply()
        elif action == 'set_run_conf':
            return do_set_run_conf(daemon, file)
        elif action == 'show_run_conf':
            return do_show_run_conf(daemon)
        elif action == 'no_run_conf':
            return do_no_run_conf(daemon)
        elif action == 'show_debug':
            return do_show_debug(option)
        elif action == 'show_logs':
            return do_show_logs(daemon)
        elif action == 'set_loopbacks':
            return do_set_loopbacks(loopbacks)
        elif action == 'show_loopbacks':
            return do_show_loopbacks()
        elif action == 'no_loopbacks':
            return do_no_loopbacks()
        else:
            raise ValueError('Unsupported action was given.')
    except (ConnectionError, TimeoutError) as e:
        return ('Error while making request: ' + str(e))
    except requests.HTTPError as e:
        return ('Unsuccessful status code: ' + str(e))
    except requests.exceptions.InvalidURL:
        return ('Invalid service point IP.')
    except requests.exceptions.ConnectionError as e:
        return ('Connection error.')
    except IOError as e:
        return ('Error handling file.')
    except Exception as e:
        if os.environ.get('SCRIPT_DEBUG', False):
            print(e)
        return ('Unexpected error.')
    return ('succefull')
