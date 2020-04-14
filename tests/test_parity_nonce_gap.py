# This file is part of Plunger.
#
# Copyright (C) 2020 MikeHathaway
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import time
from contextlib import contextmanager
from io import StringIO

import py
import pytest
from pytest import fixture
import requests_mock
import requests
from web3 import HTTPProvider, Web3

from plunger.keys import register_key
from plunger.plunger import Plunger

from test_plunger import TestPlungerUtils

last_port_number = 28545


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


@fixture(scope="session")
def web3():
    web3 = Web3(HTTPProvider("http://0.0.0.0:8545"))
    web3.eth.defaultAccount = "0x6c626f45e3b7aE5A3998478753634790fd0E82EE"
    register_key(web3, "key_file=tests/data/key1.json,pass_file=/dev/null")
    register_key(web3, "key_file=tests/data/key2.json,pass_file=/dev/null")
    assert len(web3.eth.accounts) > 1
    assert isinstance(web3.eth.accounts[0], str)
    assert isinstance(web3.eth.accounts[1], str)
    return web3


@fixture
def datadir(request):
    return py.path.local(request.module.__file__).join("..").join("data")


@fixture
def port_number():
    # global last_port_number
    # last_port_number += 1
    # return last_port_number
    return 8545


def args(arguments):
    return arguments.split()


class TestPlunger(TestPlungerUtils):

    # Create a set of transactions in the pool with nonces 9 and 11
    @staticmethod
    def mock_noncegapped_txs_in_parity_txqueue(mock, datadir, port_number: int, account: str):
        response = datadir.join('parity').join('nonce_gap_response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://0.0.0.0:{port_number}/rpc", text=response)

    @staticmethod
    def mock_noncegapped_first_txs_in_parity_txqueue(mock, datadir, port_number: int, account: str):
        response = datadir.join('parity').join('duplicate_nonce_gap_response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://0.0.0.0:{port_number}/rpc", text=response)


    def test_should_handle_parity_tx_queue_nonce_gap(self, web3, port_number, datadir):
        # time.sleep(30)
        # given
        web3.eth.defaultAccount = web3.eth.accounts[0]
        some_account = web3.eth.accounts[0]
        some_gas_price = 150000000

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_noncegapped_txs_in_parity_txqueue(mock, datadir, port_number, some_account)

            with captured_output() as (out, err):
                # and
                self.simulate_transactions(web3, 9)

                plunger = Plunger(args(f"--rpc-port {port_number} --source parity_txqueue --override-with-zero-txs {some_account} --gas-price {some_gas_price}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for nonce comparison
                plunger.main()

        # then
        assert re.match(f"""There are 2 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

Sent replacement transaction with nonce=9, gas_price={some_gas_price}, tx_hash=0x[0-9a-f]{{64}}.
Sent replacement transaction with nonce=10, gas_price={some_gas_price}, tx_hash=0x[0-9a-f]{{64}}.
Waiting for the transactions to get mined...
All pending transactions have been mined.
""", out.getvalue(), re.MULTILINE)

        # and
        assert web3.eth.getTransactionCount(some_account) == 11

    # first transaction fell out of tx queue, with later nonce transactions stuck pending
    def test_should_handle_duplicated_nonce_gaps_on_first_transaction(self, web3, port_number, datadir):
        # time.sleep(30)
        # given
        web3.eth.defaultAccount = web3.eth.accounts[3]
        some_account = web3.eth.accounts[3]
        some_gas_price = 150000000

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_noncegapped_first_txs_in_parity_txqueue(mock, datadir, port_number, some_account)

            with captured_output() as (out, err):

                plunger = Plunger(args(
                    f"--rpc-port {port_number} --source parity_txqueue --override-with-zero-txs {some_account} --gas-price {some_gas_price}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for nonce comparison
                plunger.main()

        # then
        assert re.match(f"""There are 2 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

Sent replacement transaction with nonce=0, gas_price={some_gas_price}, tx_hash=0x[0-9a-f]{{64}}.
Sent replacement transaction with nonce=1, gas_price={some_gas_price}, tx_hash=0x[0-9a-f]{{64}}.
Waiting for the transactions to get mined...
All pending transactions have been mined.
""", out.getvalue(), re.MULTILINE)

        # and
        assert web3.eth.getTransactionCount(some_account) == 2


