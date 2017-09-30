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

import os
import sys
import threading
import time
from contextlib import contextmanager
from io import StringIO
from unittest.mock import MagicMock

import py
import pytest
import re
import requests_mock
from pytest import fixture
from web3 import TestRPCProvider, Web3

sys.path.append(os.path.dirname(__file__) + "/..")

from plunger.plunger import Plunger

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


@fixture
def datadir(request):
    return py.path.local(request.module.__file__).join("..").join("data")


@fixture
def port_number():
    global last_port_number
    last_port_number += 1
    return last_port_number


def args(arguments):
    return arguments.split()


class TestPlunger:
    @staticmethod
    def simulate_transactions(web3, number_of_transactions: int):
        for no in range(0, number_of_transactions):
            web3.eth.sendTransaction({'from': web3.eth.accounts[0],
                                      'to': web3.eth.accounts[1],
                                      'value': 20})

    # Until `https://github.com/pipermerriam/eth-testrpc/issues/98` gets resolved, we substitute
    # `web3.eth.sendTransaction` and do our own nonce comparison to ensure `plunger` uses correct nonces
    @staticmethod
    def ensure_transaction_nonces(web3: Web3, nonces: list):
        def send_transaction_replacement(transaction):
            if transaction['nonce'] == nonces.pop(0):
                del transaction['nonce']
                return send_transaction_original(transaction)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def mock_0_pending_txs_on_eterscan(mock, datadir, account: str):
        mock.get(f"https://unknown.etherscan.io/txsPending?a={account}", text=datadir.join('etherscan').join('0_pending_txs-list.html').read_text('utf-8'))

    @staticmethod
    def mock_3_pending_txs_on_eterscan(mock, datadir, account: str):
        mock.get(f"https://unknown.etherscan.io/txsPending?a={account}", text=datadir.join('etherscan').join('3_pending_txs-list.html').read_text('utf-8'))
        mock.get(f"https://unknown.etherscan.io/tx/0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9", text=datadir.join('etherscan').join('3_pending_txs-get1.html').read_text('utf-8'))
        mock.get(f"https://unknown.etherscan.io/tx/0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a", text=datadir.join('etherscan').join('3_pending_txs-get2.html').read_text('utf-8'))
        mock.get(f"https://unknown.etherscan.io/tx/0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559", text=datadir.join('etherscan').join('3_pending_txs-get3.html').read_text('utf-8'))

    @staticmethod
    def mock_0_pending_txs_in_parity_txqueue(mock, datadir, port_number: int):
        TestPlunger.mock_3_pending_txs_in_parity_txqueue(mock, datadir, port_number, '0x0')

    @staticmethod
    def mock_3_pending_txs_in_parity_txqueue(mock, datadir, port_number: int, account: str):
        response = datadir.join('parity').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:{port_number}/rpc", text=response)

    def test_should_print_usage_when_no_arguments(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: the following arguments are required: address" in err.getvalue()

    def test_should_complain_about_missing_source_when_only_address_specified(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("0x0000011111222223333322222111110000099999")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: the following arguments are required: --source" in err.getvalue()

    def test_should_complain_about_missing_mode_when_only_address_and_source_specified(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("--source etherscan 0x0000011111222223333322222111110000099999")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: one of the arguments --list --wait --override-with-zero-txs is required" in err.getvalue()

    def test_should_complain_about_invalid_sources(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("--source etherscan,invalid_one,parity_txqueue --wait 0x0000011111222223333322222111110000099999")).main()

        # then
        assert "Unknown source(s): 'invalid_one'." in err.getvalue()

    def test_should_detect_0_pending_transactions_on_etherscan(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_0_pending_txs_on_eterscan(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source etherscan --list {some_account}")).main()

        # then
        assert out.getvalue() == f"There are no pending transactions on unknown from {some_account}\n"

    def test_should_detect_3_pending_transactions_on_etherscan(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source etherscan --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There are 3 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

"""

    def test_should_detect_0_pending_transactions_in_parity_txqueue(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_0_pending_txs_in_parity_txqueue(mock, datadir, port_number)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"There are no pending transactions on unknown from {some_account}\n"

    def test_should_detect_3_pending_transactions_in_parity_txqueue(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_in_parity_txqueue(mock, datadir, port_number, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There are 3 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

"""

    def test_should_ignore_duplicates_when_using_two_sources(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)
            self.mock_3_pending_txs_in_parity_txqueue(mock, datadir, port_number, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source etherscan,parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There are 4 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

"""

    def test_should_ignore_pending_transactions_if_their_nonce_is_already_used(self, port_number, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
        some_account = web3.eth.accounts[0]

        # and
        self.simulate_transactions(web3, 10)

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port {port_number} --source etherscan --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There is 1 pending transaction on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

"""

    @pytest.mark.timeout(20)
    def test_wait_should_not_terminate_until_transactions_get_mined(self, port_number, datadir):
        with captured_output() as (out, err):
            # given
            web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
            some_account = web3.eth.accounts[0]

            # when
            with requests_mock.Mocker(real_http=True) as mock:
                self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)

                threading.Thread(target=lambda: Plunger(args(f"--rpc-port {port_number} --source etherscan --wait {some_account}")).main()).start()
                time.sleep(3)

            # then
            assert out.getvalue() == f"""There are 3 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

Waiting for the transactions to get mined...
"""

            # when
            self.simulate_transactions(web3, 11)

            # and
            time.sleep(4)

            # then
            assert out.getvalue() == f"""There are 3 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

Waiting for the transactions to get mined...
All pending transactions have been mined.
"""

    @pytest.mark.timeout(20)
    def test_should_override_transactions(self, port_number, datadir):
        with captured_output() as (out, err):
            # given
            web3 = Web3(TestRPCProvider("127.0.0.1", port_number))
            web3.eth.defaultAccount = web3.eth.accounts[0]
            some_account = web3.eth.accounts[0]

            # and
            self.simulate_transactions(web3, 9)
            self.ensure_transaction_nonces(web3, [9, 10])

            # when
            with requests_mock.Mocker(real_http=True) as mock:
                self.mock_3_pending_txs_on_eterscan(mock, datadir, some_account)

                plunger = Plunger(args(f"--rpc-port {port_number} --source etherscan --override-with-zero-txs {some_account}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for nonce comparison
                plunger.main()

            # then
            assert re.match(f"""There are 2 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

Sent replacement transaction with nonce=9, gas_price=1, tx_hash=0x[0-9a-f]{{64}}.
Sent replacement transaction with nonce=10, gas_price=1, tx_hash=0x[0-9a-f]{{64}}.
Waiting for the transactions to get mined...
All pending transactions have been mined.
""", out.getvalue(), re.MULTILINE)

            # and
            assert web3.eth.getTransactionCount(some_account) == 11
