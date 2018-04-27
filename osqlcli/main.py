from __future__ import unicode_literals
from __future__ import print_function

import click
import getpass
import os
import sys
import platform

from builtins import input

from osqlcli.config import config_location
from osqlcli.__init__ import __version__


click.disable_unicode_literals_warning = True

try:
    from urlparse import urlparse, unquote, parse_qs
except ImportError:
    from urllib.parse import urlparse, unquote, parse_qs

from osqlcli.osql_cli import MssqlCli
from osqlcli.osqlclioptionsparser import create_parser
import osqlcli.telemetry as telemetry_session

MSSQLCLI_TELEMETRY_PROMPT = """
Telemetry
---------
By default, osql-cli collects usage data in order to improve your experience.
The data is anonymous and does not include commandline argument values.
The data is collected by Microsoft.

Disable telemetry collection by setting environment variable MSSQL_CLI_TELEMETRY_OPTOUT to 'True' or '1'.

Microsoft Privacy statement: https://privacy.microsoft.com/privacystatement
"""


def run_cli_with(options):

    if create_config_dir_for_first_use():
        display_telemetry_message()

    display_version_message(options)
    display_integrated_auth_message_for_non_windows(options)

    configure_and_update_options(options)

    osqlcli = MssqlCli(options)
    osqlcli.connect_to_database()

    telemetry_session.set_server_information(osqlcli.osqlcliclient_main)
    osqlcli.run()


def configure_and_update_options(options):
    if options.dac_connection and options.server and not options.server.lower().startswith("admin:"):
        options.server = "admin:" + options.server

    if not options.integrated_auth:
        if not options.username:
            options.username = input(u'Username (press enter for sa)') or u'sa'
        if not options.password:
            options.password = getpass.getpass()


def create_config_dir_for_first_use():
    config_dir = os.path.dirname(config_location())
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
        return True

    return False


def display_integrated_auth_message_for_non_windows(options):
    if platform.system().lower() != 'windows' and options.integrated_auth:
        options.integrated_auth = False
        print(u'Integrated authentication not supported on this platform')


def display_version_message(options):
    if options.version:
        print('Version:', __version__)
        sys.exit(0)


def display_telemetry_message():
    print(MSSQLCLI_TELEMETRY_PROMPT)


if __name__ == "__main__":
    try:
        telemetry_session.start()
        osqlcli_options_parser = create_parser()
        osqlcli_options = osqlcli_options_parser.parse_args(sys.argv[1:])
        run_cli_with(osqlcli_options)
    finally:
        # Upload telemetry async in a separate process.
        telemetry_session.conclude()