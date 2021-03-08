# Copyright 2016 Intel Corporation
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

import logging
import hashlib

import cbor
import time

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_custom_authentication.client_cli.rsa_accumulator import RSA2048_Accumulator

LOGGER = logging.getLogger(__name__)


VALID_VERBS = 'update', 'initialize', 'authenticate'
#, 'inc', 'dec'


MAX_SERVICE_LENGTH = 20

FAMILY_NAME = 'custom_authentication'

AUTHENTICATION_ADDRESS_PREFIX = hashlib.sha512(
    FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]


def make_accumulator_address(service):                       #service ist dienst, der später authentication nutzt bsp 'mercedes'
    return AUTHENTICATION_ADDRESS_PREFIX + hashlib.sha512(
        service.encode('utf-8')).hexdigest()[-64:]             # das -64 greift auf die hinteren 64 zahlen vom array drauf


class AuthenticationTransactionHandler(TransactionHandler):
    # Disable invalid-overridden-method. The sawtooth-sdk expects these to be
    # properties.
    # pylint: disable=invalid-overridden-method
    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return ['1.0']

    @property
    def namespaces(self):
        return [AUTHENTICATION_ADDRESS_PREFIX]

    def apply(self, transaction, context):                              # Entry point
        start = time.clock()
        verb, service, value, witness = _unpack_transaction(transaction)     # Transaction auslesen
        # value ist entweder accumulator oder prime zum authenticaten

        state = _get_state_data(service, context)                       # Aktuellen hinterlegten Wert an
                                                                        # service-Adresse kriegen
        updated_state = _do_begin_processing(verb, service, value, witness, state)        # Holt neuen Wert der in Ledger
                                                                      # geschrieben werden soll
                                                                       # Entweder acc_value oder acc_updated


        if verb == 'authenticate':
            elapsed = (time.clock() - start)
            print("time for authenticate ", elapsed)
        else:
            _set_state_data(service, updated_state, context)
            elapsed = (time.clock() - start)
            print("time for update/initialize: ", elapsed)

def _unpack_transaction(transaction):
    verb, service, value, witness = _decode_transaction(transaction)     #value = accumulator value, new or to update
    _validate_verb(verb)
    _validate_service(service)
    _validate_accumulator_value(value)              #acc value kann auch prime enthalten
    #validate witness
    return verb, service, value, witness


def _decode_transaction(transaction):
    try:
        content = cbor.loads(transaction.payload)
    except Exception as e:
        raise InvalidTransaction('Invalid payload serialization') from e

    try:
        verb = content['Verb']
    except AttributeError:
        raise InvalidTransaction('Verb is required') from AttributeError

    try:
        service = content['Service']
    except AttributeError:
        raise InvalidTransaction('ServiceName is required') from AttributeError

    try:
        value = content['Value']
    except AttributeError:
        raise InvalidTransaction('Accumulator Value is required') from AttributeError

    try:
        witness = content['Witness']
    except AttributeError:
        raise InvalidTransaction('Accumulator Value is required') from AttributeError

    return verb, service, value, witness


def _validate_verb(verb):
    if verb not in VALID_VERBS:
        raise InvalidTransaction('Verb must be "initialize" "update" or "authenticate"')


def _validate_service(service):
    if not isinstance(service, str) or len(service) > MAX_SERVICE_LENGTH:
        raise InvalidTransaction(
            'Name must be a string of no more than {} characters'.format(
                MAX_SERVICE_LENGTH))


def _validate_accumulator_value(value_str):
    value = int(value_str)
    if not isinstance(value, int):              #Hier eventuell noch bytegröße angeben
        raise InvalidTransaction(
            'Value must be an integer')


def _get_state_data(service, context):
    address = make_accumulator_address(service)         # Speicheradresse für bestimmen service bsp autohaus
                                                        # anlegen
    state_entries = context.get_state([address])        # Ledgerinhalt an Speicheradresse herauskopieren

    try:
        return cbor.loads(state_entries[0].data)        # "Decoden" der zuvor cbor "codierten" werte
    except IndexError:
        return {}                                       # Wenn entry im Ledger leer ist wird nichts zurück
    except Exception as e:                              # gegeben
        raise InternalError('Failed to load state data') from e


def _set_state_data(service, state, context):
    address = make_accumulator_address(service)         # Neue adresse erstellen mit servicenamen
    encoded_accumulator = cbor.dumps(state)                         # Kodieren des zu speichernden accumulator values
                                                        # state = accumulator value
    addresses = context.set_state({address: encoded_accumulator})   # Inhalt von encoded an adresse schreiben

    if not addresses:
        raise InternalError('State error')


def _do_begin_processing(verb, service, prime, witness, state):
    verbs = {                               # key value object, um danach funktionen je nach übergebenem
        'initialize': _do_initialize,       # Verb aufzurufen
        'update': _do_update,
        'authenticate': _do_authenticate
    }

    try:
        if verb == 'authenticate':
            return verbs[verb](service, prime, witness, state)
        else:
            return verbs[verb](service, prime, state)       # hier wird funktion je nach ver (initialize oder
    except KeyError:                                        # update)
        # This would be a programming error.
        raise InternalError('Unhandled verb: {}'.format(verb)) from KeyError


def _do_initialize(service, acc_value, state):

    msg = 'Sending"{n}" to {m}'.format(n=service, m=acc_value)
    LOGGER.debug(msg)
    updated = dict(state.items())
    updated[service] = acc_value

    return updated


def _do_update(service, acc_value, state):

    msg = 'Sending"{n}" to {m}'.format(n=service, m=acc_value)
    LOGGER.debug(msg)
    updated = dict(state.items())
    updated[service] = acc_value

    return updated


def _do_authenticate(service, prime, witness, state):
    prime = int(prime)
    witness = int(witness)
    updated = dict(state.items())
    acc_value = updated[service]
    acc_value = int(acc_value)
    rsa_acc = RSA2048_Accumulator([])
    modulus = rsa_acc.get_modulus()
    result = verify_membership(witness, prime, modulus, acc_value)
    print("User is authenticated:", result)
    return updated

def verify_membership(wit, x, modulus, acc_value):
        if pow(wit, x, modulus) == acc_value:
            return True
        else:
            return False