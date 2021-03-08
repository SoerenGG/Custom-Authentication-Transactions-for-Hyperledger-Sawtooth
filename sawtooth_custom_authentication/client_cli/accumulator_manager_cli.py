# Copyright 2016, 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import argparse
import getpass
import logging
import os
import sys
import traceback
import pkg_resources
import time
from colorlog import ColoredFormatter
from sawtooth_custom_authentication.client_cli.tailsfile import create_tailsfile
from sawtooth_custom_authentication.client_cli.tailsfile import write_tailsfile_data
from sawtooth_custom_authentication.client_cli.tailsfile import get_tailsfile_data
from sawtooth_custom_authentication.client_cli.user_client import UserClient
from sawtooth_custom_authentication.client_cli.accumulator_manager_client import CustomAuthenticationClient
from sawtooth_custom_authentication.client_cli.exceptions import IntKeyCliException
from sawtooth_custom_authentication.client_cli.exceptions import IntkeyClientException
from sawtooth_custom_authentication.client_cli.rsa_accumulator import RSA2048_Accumulator

DISTRIBUTION_NAME = 'sawtooth-authentication'


DEFAULT_URL = 'http://127.0.0.1:8008'    # url of Rest API, the Client sends its transactions to


def create_console_handler(verbose_level):
    clog = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s[%(asctime)s %(levelname)-8s%(module)s]%(reset)s "
        "%(white)s%(message)s",
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red',
        })

    clog.setFormatter(formatter)

    if verbose_level == 0:
        clog.setLevel(logging.WARN)
    elif verbose_level == 1:
        clog.setLevel(logging.INFO)
    else:
        clog.setLevel(logging.DEBUG)

    return clog


def setup_loggers(verbose_level):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(create_console_handler(verbose_level))


def create_parent_parser(prog_name):
    parent_parser = argparse.ArgumentParser(prog=prog_name, add_help=False)
    parent_parser.add_argument(
        '-v', '--verbose',
        action='count',
        help='enable more verbose output')

    try:
        version = pkg_resources.get_distribution(DISTRIBUTION_NAME).version
    except pkg_resources.DistributionNotFound:
        version = 'UNKNOWN'

    parent_parser.add_argument(
        '-V', '--version',
        action='version',
        version=(DISTRIBUTION_NAME + ' (Hyperledger Sawtooth) version {}')
        .format(version),
        help='display version information')

    return parent_parser


def create_parser(prog_name):
    parent_parser = create_parent_parser(prog_name)

    parser = argparse.ArgumentParser(
        parents=[parent_parser],
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subparsers = parser.add_subparsers(title='subcommands', dest='command')
    add_initialize_parser(subparsers, parent_parser)
    add_show_parser(subparsers, parent_parser)
    add_user_client_add_parser(subparsers, parent_parser)
    add_user_client_authenticatication_parser(subparsers, parent_parser)
    add_user_client_remove_parser(subparsers, parent_parser)
    return parser


def add_initialize_parser(subparsers, parent_parser):
    message = 'Sends an transaction to initalize an accumulator for the specified service.'

    parser = subparsers.add_parser(
        'initialize',
        parents=[parent_parser],
        description=message,
        help='Sets an accumulator-value for the service')

    parser.add_argument(
        'service',
        type=str,
        help='name of service for which an accumulator-value should be saved on ledger')
    '''
    parser.add_argument(
        'acc_value',
        type=int,
        help='acc_value for ledger')
    '''
    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--keyfile',
        type=str,
        help="identify file containing user's private key")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for transaction to commit')


def do_initialize(args):
    service,  wait = args.service,  args.wait      #auslesen
    value = 9                                       #Startvalue für RSA accumulator
    client = _get_client(args)
    response = client.initialize(service, value, None, wait)          #initialize transaction schicken bsp 9
    create_tailsfile(service)
    elements = []
    usernames = []
    write_tailsfile_data(service, value, 0, elements, usernames)                 #value eig immer 9
    print(response)






def add_show_parser(subparsers, parent_parser):
    message = 'Shows the accumulator value of the specified service name'

    parser = subparsers.add_parser(
        'show',
        parents=[parent_parser],
        description=message,
        help='Displays the specified message')

    parser.add_argument(
        'service',
        type=str,
        help='name of service to show acc_value')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')


def do_show(args):
    service = args.service
    client = _get_client(args, False)
    value = client.show(service)
    print('{}: {}'.format(service, value))


def add_user_client_add_parser(subparsers, parent_parser):
    message = 'To add a new user-client to accumulator'

    parser = subparsers.add_parser(
        'user-client-add',
        parents=[parent_parser],
        description=message,
        help='Displays the specified message')

    parser.add_argument(
        'name',
        type=str,
        help='specify name of client')

    parser.add_argument(
        'service',
        type=str,
        help='specify servicename client wants to be added to')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--keyfile',
        type=str,
        help="identify file containing user's private key")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for transaction to commit')


def do_user_client_add(args):
    username, service= args.name, args.service  #name des userclients
    user_client = _get_user_cient(username) #neuer user client wird erstellt mit zugehörigem namen prime wird erstellt
    prime = user_client.get_prime()         #userclient prime wird ausgelesen
    acc_value, acc_value_updated, elements, usernames = get_tailsfile_data(service)   #aktuellen status auslesn
    if not elements:
        elements_int = []
    else:
        elements_int = list(map(int, elements))
    rsa_acc = RSA2048_Accumulator(elements_int)                         #RSA holen
    acc_value_updated = rsa_acc.add(prime)                          #Neuen acc value berechnen
    elements.append(prime)                                          #neue prime zu elements hinzufügen
    usernames.append(username)
    write_tailsfile_data(service, acc_value, acc_value_updated, elements, usernames)
    client = _get_client(args)
    response = client.update(service, acc_value_updated)
    print(response)
    witness_update(service)

def witness_update(service):
    acc_value, acc_value_updated, elements, usernames = get_tailsfile_data(service)
    elements_int = list(map(int, elements))
    rsa_acc = RSA2048_Accumulator(elements_int)
    for username in usernames:
        user_client = _get_user_cient(username)
        prime = user_client.get_prime()
        prime_int = int(prime)
        wit = rsa_acc.gen_witness(prime_int)
        user_client.store_wit(wit)

def add_user_client_authenticatication_parser(subparsers, parent_parser):
    message = 'To add a new user-client to accumulator'

    parser = subparsers.add_parser(
        'user-client-authenticate',
        parents=[parent_parser],
        description=message,
        help='Displays the specified message')

    parser.add_argument(
        'name',
        type=str,
        help='specify name of client')

    parser.add_argument(
        'service',
        type=str,
        help='specify servicename client wants to be removed from')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--keyfile',
        type=str,
        help="identify file containing user's private key")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for transaction to commit')


def do_user_client_authentication(args):
    username, service = args.name, args.service
    user_client = _get_user_cient(username)
    prime, witness = user_client.authenticate_me()
    client = _get_client(args)
    response = client.authentication(service, prime, witness)
    print(response)

def add_user_client_remove_parser(subparsers, parent_parser):
    message = 'To remove a existing user-client to accumulator'

    parser = subparsers.add_parser(
        'user-client-remove',
        parents=[parent_parser],
        description=message,
        help='Displays the specified message')

    parser.add_argument(
        'name',
        type=str,
        help='specify name of client')

    parser.add_argument(
        'service',
        type=str,
        help='specify servicename client wants to be added to')

    parser.add_argument(
        '--url',
        type=str,
        help='specify URL of REST API')

    parser.add_argument(
        '--keyfile',
        type=str,
        help="identify file containing user's private key")

    parser.add_argument(
        '--wait',
        nargs='?',
        const=sys.maxsize,
        type=int,
        help='set time, in seconds, to wait for transaction to commit')

def do_user_client_remove(args):
    username, service = args.name, args.service
    acc_value, acc_value_updated, elements, usernames = get_tailsfile_data(service)
    index = usernames.index(username)
    usernames.remove(username)
    elements.pop(index)
    elements_int = list(map(int, elements))
    rsa_acc = RSA2048_Accumulator(elements_int)
    acc_value_updated = rsa_acc.get_acc_value()
    write_tailsfile_data(service, acc_value, acc_value_updated, elements, usernames)
    client = _get_client(args)
    response = client.update(service, acc_value_updated)
    print(response)
    witness_update(service)
    if os.path.exists(username):
        os.remove("{}.json".format(username))


def _get_user_cient(username):
    return UserClient(username)

def _get_client(args, read_key_file=True):
    return CustomAuthenticationClient(
        url=DEFAULT_URL if args.url is None else args.url,
        keyfile=_get_keyfile(args) if read_key_file else None)


def _get_keyfile(args):
    try:
        if args.keyfile is not None:
            return args.keyfile
    except AttributeError:
        return None

    real_user = getpass.getuser()
    home = os.path.expanduser("~")
    key_dir = os.path.join(home, ".sawtooth", "keys")

    return '{}/{}.priv'.format(key_dir, real_user)



def main(prog_name=os.path.basename(sys.argv[0]), args=None):
    if args is None:
        args = sys.argv[1:]
    parser = create_parser(prog_name)
    args = parser.parse_args(args)

    if args.verbose is None:
        verbose_level = 0
    else:
        verbose_level = args.verbose
    setup_loggers(verbose_level=verbose_level)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'initialize':
        start = time.clock()
        do_initialize(args)
        elapsed = (time.clock()-start)
        print("Time of initialize: ", elapsed)
    elif args.command == 'show':
        do_show(args)
    elif args.command == 'user-client-add':
        start = time.clock()
        do_user_client_add(args)
        elapsed = (time.clock() - start)
        print("Time of add a user:", elapsed)
    elif args.command == 'user-client-authenticate':
        start = time.clock()
        do_user_client_authentication(args)
        elapsed = (time.clock() - start)
        print("Time of a authentication in manager: ", elapsed)
    elif args.command == 'user-client-remove':
        start = time.clock()
        do_user_client_remove(args)
        elapsed = (time.clock() - start)
        print("Time of a remove: ", elapsed)
    else:
        raise IntKeyCliException("invalid command: {}".format(args.command))
  

def main_wrapper():
    # pylint: disable=bare-except
    try:
        main()
    except (IntKeyCliException, IntkeyClientException) as err:
        print("Error: {}".format(err), file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
    except SystemExit as e:
        raise e
    except:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
