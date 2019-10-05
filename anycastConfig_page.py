#!/user/bin/python3

# Copyright 2018 BlueCat Networks. All rights reserved.
# Various Flask framework items.

import os
import sys
import codecs

from flask import (url_for, redirect, render_template,
                   flash, g, session, jsonify, request, Markup)
from random import randint
from collections import defaultdict
from bluecat import route, util
from main_app import app
from .anycastConfig_form import GenericFormTemplate
from .config import conf
from .anycast_config import main

import config.default_config as config
import shutil
import pandas as pd


def module_path():
    return os.path.dirname(os.path.abspath(__file__))


@route(app, '/anycastConfig/anycastConfig_endpoint')
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anycastConfig_page():
    form = GenericFormTemplate()
    random_number = str(randint(101, 999))
    session['folder_name'] = session['username'] + random_number
    processing_folder = os.path.join(conf.get('processing_folder', '.'),
                                     session['folder_name'])
    if os.path.exists(processing_folder):
        shutil.rmtree(processing_folder)
    os.makedirs(processing_folder, mode=0o777)
    source_file_path = os.path.join(conf.get('processing_folder'),
                                    'anycast_config.py')
    destination_file_path = os.path.join(processing_folder,
                                         'anycast_config.py')
    shutil.copyfile(source_file_path, destination_file_path)
    print(processing_folder)
    os.chmod(destination_file_path, mode=0o777)
    return render_template(
        'anycastConfig_page.html',
        form=form,
        text=util.get_text(module_path(), config.language),
        options=g.user.get_options(),
    )


@route(app, '/anycastConfig/form', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anycastConfig_page_form():
    form = GenericFormTemplate()
    if form.validate_on_submit():
        session['clientID'] = form.client_id.data
        session['password'] = form.password.data
        session['ip_address'] = form.ip_address.data
        session['port'] = form.port.data
        args = {'action': 'show_daemons'}
        output = main(args)
        print(output)
        if not output.count('Unsuccessful'):
            g.user.logger.info('SUCCESS')
            return jsonify({'responce': 'this is responce',
                            'status': 'created connection',
                            'output': output})
        else:
            return jsonify(
                    {'exception': 'Please check your credentials',
                     'redirect': url_for(
                        'anycastConfiganycastConfig_anycastConfig_page')})
    else:
        return jsonify({'responce': 'validation failed'})


@route(app, '/anycastConfig/update_status', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_update_status():

    daemons_status, select_field = get_stats()
    return jsonify({'output': create_status_table(daemons_status),
                    'select_field': select_field})


@route(app, '/anycastConfig/update_textfield', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_update_textfiled():
    option = request.form.get('option')
    output = main({
                'action': 'show_run_conf',
                'daemon': option
            })
    return jsonify({'text_field': output})


@route(app, '/anycastConfig/update_textfield_staged', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_update_textfiled_staged():
    option = request.form.get('option')
    output = main({
                'action': 'show_staged_conf',
                'daemon': option
            })
    if output == '' or output.count('Unsuccessful'):
        output = 'File is not staged'
    return jsonify({'text_field': output})


@route(app, '/anycastConfig/update_configuration', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_update_configuration():
    option = request.form.get('option')
    text = request.form.get('confText')
    if text.count(option):
        print(text)
        conf_file_path \
            = os.path.join(conf.get('processing_folder'),
                           session['folder_name'], option+'.conf')
        with open(conf_file_path, 'w') as option_file:
            option_file.write(text)
        print("set_staged_conf ouput :", main({
                'action': 'set_staged_conf',
                'daemon': option,
                'file': conf_file_path}))
        daemons_status, select_field = get_stats()

        return jsonify({'output': create_status_table(daemons_status),
                        'select_field': select_field})
    else:
        return jsonify({'exception': 'Please check your configuration file'})


@route(app, '/anycastConfig/clear_configuration', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_clear_configuration():
    print("this function is clearing configuration")
    option = request.form.get('option')
    main({
            'action': 'no_staged_conf',
            'daemon': option
    })
    daemons_status, select_field = get_stats()

    return jsonify({'output': create_status_table(daemons_status),
                    'select_field': select_field})

@route(app, '/anycastConfig/clear_run_configuration', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_clear_run_configuration():
    print("this function is clearing running configuration")
    option = request.form.get('option')
    main({
            'action': 'no_run_conf',
            'daemon': option
    })
    daemons_status, select_field = get_stats()

    return jsonify({'output': create_status_table(daemons_status),
                    'select_field': select_field})

@route(app, '/anycastConfig/run_daemon', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_run_daemon():
    option = request.form.get('option')
    main({
            'action': 'start',
            'daemon': option
    })
    daemons_status, select_field = get_stats()

    return jsonify({'output': create_status_table(daemons_status),
                    'select_field': select_field})


@route(app, '/anycastConfig/stop_daemon', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_stop_daemon():
    option = request.form.get('option')
    print('this is option for stoping the daemin', option)
    main({
            'action': 'pause',
            'daemon': option
    })
    daemons_status, select_field = get_stats()

    return jsonify({'output': create_status_table(daemons_status),
                    'select_field': select_field})


@route(app, '/anycastConfig/apply_configuration', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_applythestagedConfiguration():
    staged_conf = main({
        'action': 'apply'
    })
    if staged_conf != '' or 'Unsuccessful' in staged_conf:
        daemons_status, select_field = get_stats()
        return jsonify({'output': create_status_table(daemons_status),
                        'select_field': select_field})
    else:
        return jsonify({'exception': 'Stage configuration before applying'})


@route(app, '/anycastConfig/debug', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_debug():
    print("this function is debug")
    table_contents = [
        ["Zebra", "zebraSummary",
            main({'action': 'show_debug', 'option': 'zebraSummary'})],
        ["", 'routes', main({'action': 'show_debug', 'option': 'routes'})],
        ["", 'interfaces',
            main({'action': 'show_debug', 'option': 'interfaces'})],
        ["", 'runningConfig',
            main({'action': 'show_debug', 'option': 'runningConfig'})],
        ["BGP", 'bgpSummary',
            main({'action': 'show_debug', 'option': 'bgpSummary'})],
        ["", 'bgpNeighbors',
            main({'action': 'show_debug', 'option': 'bgpNeighbors'})],
        ["OSPF", 'ospfNeighbors',
            main({'action': 'show_debug', 'option': 'ospfNeighbors'})],
        ["", 'ospfRoutes',
            main({'action': 'show_debug', 'option': 'ospfRoutes'})],
        ["", 'ospfRouterInfo',
            main({'action': 'show_debug', 'option': 'ospfRouterInfo'})],
        ["", 'ospfDatabase',
            main({'action': 'show_debug', 'option': 'ospfDatabase'})]]
    for i, _ in enumerate(table_contents):
        table_contents[i][2] =\
            table_contents[i][2].replace('\n', '</div> <div>')
        table_contents[i][2] = '<div>' + table_contents[i][2] + '</div>'
        table_contents[i][2] = table_contents[i][2].replace('\r', ' ')

    pd.set_option('display.max_colwidth', -1)
    print(pd.DataFrame(
        table_contents,
        columns=['DAEMON', 'OPTION', 'DEBUG SUMMARY'])
            .to_html(index=False))
    return jsonify(
        {'debug_output': create_dubug_table(table_contents)})


@route(app, '/anycastConfig/logout', methods=['POST'])
@util.workflow_permission_required('anycastConfig_page')
@util.exception_catcher
def anycastConfig_anacastConfig_logout():
    session_folder_path = os.path.join(conf.get('processing_folder'),
                                       session['folder_name'])
    shutil.rmtree(session_folder_path)
    return jsonify(
        {'redirect': url_for('anycastConfiganycastConfig_anycastConfig_page')})


def get_stats():
    run_status = main({
                'action': 'show_daemons'
            })
    run_status = run_status.strip().split("\n")
    output_staged_conf_dict = {}
    for val in run_status:
        local_val = val.split("=")
        output_staged_conf_dict[local_val[0]] = local_val[1]
    daemons_status = []
    for key in ['zebra', 'ospfd', 'bgpd']:
        output_run_cofig = main({
            'action': 'show_run_conf',
            'daemon': key
        })
        output_staged_conf = main({
            'action': 'show_staged_conf',
            'daemon': key
        })
        local_list = [key]
        if output_staged_conf_dict[key] == "no":
            local_list.append('&#215;')
        else:
            local_list.append('&#10003;')

        if output_run_cofig == "" or output_run_cofig.count("Unsuccessful"):
            local_list.append('&#215;')
        else:
            local_list.append('&#10003;')

        if output_staged_conf == "" \
                or output_staged_conf.count("Unsuccessful"):
            local_list.append('&#215;')
        else:
            local_list.append('&#10003;')
        daemons_status.append(local_list)
    select_field = '<div id="daemon-status-select"> \n'
    for key, _, configure, _ in daemons_status:
        if configure == '&#10003;':
            select_field += '<input class="btn-primary" \
                onclick="getconfigfile(event, \''+key.strip()+'\')" \
                type="submit" value='+key+'>'
        else:
            select_field += '<input class="btn-primary" \
                onclick="cleartextarea(event, \''+key.strip()+'\')" \
                type="submit" value='+key+'>'
    select_field += '\n </div>'
    select_field = ''
    return [daemons_status, select_field]


def create_status_table(status_table):
    print(status_table)
    html_text = ''' <table border="1" class="dataframe">
                        <thead>
                            <tr style="text-align: right;">
                                <th>Daemon</th>
                                <th>Running status</th>
                                <th>Running Configuration Status</th>
                                <th>Stage Configuration Status</th>
                            </tr>
                        </thead>
                        <tbody> \n '''
    for daemon_details in status_table:
        html_text += '<tr> \n \
            <td>' + daemon_details[0] + '</td> \n \
            <td onclick=' + '\'stoporstartDaemon("'\
                    + daemon_details[0] + '", "'\
                    + daemon_details[1] + '", this)\'>'\
                    + daemon_details[1] + '</td>  \n\
            <td onclick=' + '\'showrunConf("'\
                    + daemon_details[0]+'", this)\'>'\
                    + daemon_details[2]+'</td> \n \
            <td onclick='+'\'showstagedConf("'\
                    + daemon_details[0]+'", this)\'>'\
                    + daemon_details[3]+'</td> \n \
            </tr>\n '
    html_text += ' </tbody></table>'
    return html_text


def create_dubug_table(dubug_table):
    html_text = ''' <table border="1" class="dubug-table">
                        <thead>
                            <tr style="text-align: left;">
                                <th>Daemon</th>
                                <th>Option</th>
                                <th>Debug Summary</th>
                            </tr>
                        </thead>
                        <tbody> \n '''
    for daemon_details in dubug_table:
        html_text += '<tr> \n \
            <td>' + daemon_details[0] + '</td> \n \
            <td>' + daemon_details[1] + '</td> \n \
            <td>' + daemon_details[2] + '</td> \n \
            </tr>\n '
    html_text += ' </tbody></table>'
    return html_text
