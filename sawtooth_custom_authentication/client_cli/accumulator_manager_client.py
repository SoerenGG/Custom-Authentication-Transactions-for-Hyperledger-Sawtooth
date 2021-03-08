# Copyright 2017 Intel Corporation
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

import hashlib
import base64
import time
import random
import requests
import yaml
import cbor

from sawtooth_custom_authentication.client_cli.exceptions import IntkeyClientException

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch


def _sha512(data):
    return hashlib.sha512(data).hexdigest()


class CustomAuthenticationClient:
    def __init__(self, url, keyfile=None):
        self.url = url

        if keyfile is not None:
            try:
                with open(keyfile) as fd:
                    private_key_str = fd.read().strip()
                    fd.close()
            except OSError as err:
                raise IntkeyClientException(
                    'Failed to read private key: {}'.format(str(err))) from err

            try:
                private_key = Secp256k1PrivateKey.from_hex(private_key_str)
            except ParseError as e:
                raise IntkeyClientException(
                    'Unable to load private key: {}'.format(str(e))) from e

            self._signer = CryptoFactory(
                create_context('secp256k1')).new_signer(private_key)

    def initialize(self, service, value, witness=None, wait=None):
        return self._send_transaction('initialize', service, value, witness=witness, wait=wait)

    def update(self, service, value, witness=None, wait=None):
        return self._send_transaction('update', service, value, witness=witness,  wait=wait)

    def authentication(self, service, prime, witness, wait=None):
        return self._send_transaction('authenticate', service, prime, witness, wait=wait)

    def show(self, service):
        address = self._get_address(service)
        result = self._send_request("state/{}".format(address), service=service)

        try:
            return cbor.loads(
                base64.b64decode(
                    yaml.safe_load(result)["data"]))[service]

        except BaseException:
            return None

    def _get_status(self, batch_id, wait):
        try:
            result = self._send_request(
                'batch_statuses?id={}&wait={}'.format(batch_id, wait),)
            return yaml.safe_load(result)['data'][0]['status']
        except BaseException as err:
            raise IntkeyClientException(err) from err 

    def _get_prefix(self):
        return _sha512('custom_authentication'.encode('utf-8'))[0:6]

    def _get_address(self, service):
        prefix = self._get_prefix()
        service_address = _sha512(service.encode('utf-8'))[-64:]
        return prefix + service_address

    def _send_request(self, suffix, data=None, content_type=None, service=None):
        if self.url.startswith("http://"):
            url = "{}/{}".format(self.url, suffix)
        else:
            url = "http://{}/{}".format(self.url, suffix)

        headers = {}

        if content_type is not None:
            headers['Content-Type'] = content_type
            print(headers['Content-Type'])
        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)
                print(result)
                print(headers)
                

            if result.status_code == 404:
                raise IntkeyClientException("No such service: {}".format(service))

            if not result.ok:
                raise IntkeyClientException("Error {}: {}".format(
                    result.status_code, result.reason))

        except requests.ConnectionError as err:
            raise IntkeyClientException(
                'Failed to connect to REST API: {}'.format(err)) from err

        except BaseException as err:
            raise IntkeyClientException(err) from err

        return result.text

    def _send_transaction(self, verb, service, value, witness=None, wait=None):
        value_str = str(value)
        if witness == None:
            witness = 0
        witness_str = str(witness)          #wegen encoding von cbor
        payload = cbor.dumps(
            {
            'Verb': verb,
            'Service': service,
            'Value': value_str,
            'Witness': witness_str,
            })

        # Construct the address
        address = self._get_address(service)

        header = TransactionHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            family_name="custom_authentication",
            family_version="1.0",
            inputs=[address],
            outputs=[address],
            dependencies=[],
            payload_sha512=_sha512(payload),
            batcher_public_key=self._signer.get_public_key().as_hex(),
            nonce=hex(random.randint(0, 2**64))
        ).SerializeToString()

        signature = self._signer.sign(header)

        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=signature
        )

        batch_list = self._create_batch_list([transaction])
        batch_id = batch_list.batches[0].header_signature

        if wait and wait > 0:
            wait_time = 0
            start_time = time.time()
            response = self._send_request(
                "batches", batch_list.SerializeToString(),
                'application/octet-stream',
            )
            while wait_time < wait:
                status = self._get_status(
                    batch_id,
                    wait - int(wait_time),
                )
                wait_time = time.time() - start_time

                if status != 'PENDING':
                    return response

            return response

        return self._send_request(
            "batches", batch_list.SerializeToString(),
            'application/octet-stream',
        )

    def _create_batch_list(self, transactions):
        transaction_signatures = [t.header_signature for t in transactions]

        header = BatchHeader(
            signer_public_key=self._signer.get_public_key().as_hex(),
            transaction_ids=transaction_signatures
        ).SerializeToString()

        signature = self._signer.sign(header)

        batch = Batch(
            header=header,
            transactions=transactions,
            header_signature=signature)
        return BatchList(batches=[batch])


