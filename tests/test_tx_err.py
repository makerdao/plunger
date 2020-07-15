# This file is part of Plunger.
#
# Copyright (C) 2017 reverendus
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
import threading
import time
from contextlib import contextmanager
from io import StringIO

import py
import pytest
import requests_mock
from pytest import fixture
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

    # @pytest.mark.timeout(20)
    @pytest.mark.skip("reconcile what the new mock does vs the etherscan mock")
    def test_should_handle_transaction_sending_errors(self, web3, port_number, datadir):
        with captured_output() as (out, err):
            # given
            web3.eth.defaultAccount = web3.eth.accounts[0]
            some_account = web3.eth.accounts[0]

            # and
            self.simulate_transactions(web3, 10)
            self.ensure_transactions_fail(web3, "Simulated transaction failure")

            # when
            with requests_mock.Mocker(real_http=True) as mock:
                self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)

                plunger = Plunger(args(f"--rpc-host 0.0.0.0 --rpc-port {port_number} --gas-price 1 --source etherscan --override-with-zero-txs {some_account}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for transaction failure simulation
                plunger.main()

            # then
            assert out.getvalue() == f"""There is 1 pending transaction on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

Failed to send replacement transaction with nonce=10, gas_price=1.
   Error: Simulated transaction failure
Waiting for the transactions to get mined...
All pending transactions have been mined.
"""

            # and
            assert web3.eth.getTransactionCount(some_account) == 11
