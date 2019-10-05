import datetime

from wtforms import StringField, PasswordField, FileField
from wtforms import BooleanField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Email, MacAddress, URL
from bluecat.wtform_extensions import GatewayForm
from bluecat.wtform_fields import Configuration, CustomStringField, IP4Address


class GenericFormTemplate(GatewayForm):

    client_id = CustomStringField(
        default='b2756813-e562-4d21-837b-33aa1d5456b6',
        label='Cliend ID'
    )

    password = PasswordField(
        label='Security Key',
        default='c62ba28e-c6a8-4d40-ae50-bf45c47dbfd1'
    )

    ip_address = IP4Address(
        label='IP Address',
        default='10.244.135.248',
        required=True,
        result_decorator=None,
        enable_on_complete=['submit']
    )

    port = CustomStringField(
        default='443',
        label='Port'
    )
    submit = SubmitField(label='Login')
    logout = SubmitField(label='logout')
