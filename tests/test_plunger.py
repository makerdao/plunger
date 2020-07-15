# This file is part of Plunger.
#
# Copyright (C) 2017-2020 reverendus,EdNoepel
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

import sys
from contextlib import contextmanager
from io import StringIO

import py
import pytest
import requests_mock
from pytest import fixture
from web3 import HTTPProvider, Web3

from plunger.keys import register_key
from plunger.plunger import Plunger


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


def args(arguments):
    return arguments.split()

class TestPlungerUtils:
    @staticmethod
    def simulate_transactions(web3, number_of_transactions: int):
        for no in range(0, number_of_transactions):
            web3.eth.sendTransaction({'from': web3.eth.accounts[0],
                                      'to': web3.eth.accounts[1],
                                      'value': 20})

    # Until `https://github.com/pipermerriam/eth-testrpc/issues/98` gets resolved, we substitute
    # `web3.eth.sendTransaction` and do our own nonce comparison to ensure `plunger` uses correct nonces
    @staticmethod
    def ensure_transactions(web3: Web3, nonces: list, gas_price: int):
        def send_transaction_replacement(transaction):
            if transaction['nonce'] == nonces.pop(0) and transaction['gasPrice'] == gas_price:
                del transaction['nonce']
                return send_transaction_original(transaction)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def ensure_transactions_fail(web3: Web3, error_message: str):
        def send_transaction_replacement(transaction):
            del transaction['nonce']
            send_transaction_original(transaction)
            raise Exception(error_message)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def mock_0_pending_txs_on_jsonrpc(mock, datadir, account: str):
        TestPlunger.mock_3_pending_txs_on_jsonrpc(mock, datadir, '0x0')

    @staticmethod
    def mock_3_pending_txs_on_jsonrpc(mock, datadir, account: str):
        # TODO: Hack my json dump to include these tx hashes
        # mock.get(f"https://unknown.etherscan.io/txsPending?a={account}", text=datadir.join('etherscan').join('3_pending_txs-list.html').read_text('utf-8'))
        # mock.get(f"https://unknown.etherscan.io/tx/0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9", text=datadir.join('etherscan').join('3_pending_txs-get1.html').read_text('utf-8'))
        # mock.get(f"https://unknown.etherscan.io/tx/0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a", text=datadir.join('etherscan').join('3_pending_txs-get2.html').read_text('utf-8'))
        # mock.get(f"https://unknown.etherscan.io/tx/0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559", text=datadir.join('etherscan').join('3_pending_txs-get3.html').read_text('utf-8'))
        response = datadir.join('jsonrpc').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://0.0.0.0:8545/rpc", text=response)

    @staticmethod
    def mock_0_pending_txs_in_parity_txqueue(mock, datadir):
        TestPlunger.mock_3_pending_txs_in_parity_txqueue(mock, datadir, '0x0')

    @staticmethod
    def mock_3_pending_txs_in_parity_txqueue(mock, datadir, account: str):
        response = datadir.join('parity').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://0.0.0.0:8545/rpc", text=response)

class TestPlunger(TestPlungerUtils):
    @staticmethod
    def simulate_transactions(web3, number_of_transactions: int):
        for no in range(0, number_of_transactions):
            web3.eth.sendTransaction({'from': web3.eth.accounts[0],
                                      'to': web3.eth.accounts[1],
                                      'value': 20})

    # Until `https://github.com/pipermerriam/eth-testrpc/issues/98` gets resolved, we substitute
    # `web3.eth.sendTransaction` and do our own nonce comparison to ensure `plunger` uses correct nonces
    @staticmethod
    def ensure_transactions(web3: Web3, nonces: list, gas_price: int):
        def send_transaction_replacement(transaction):
            if transaction['nonce'] == nonces.pop(0) and transaction['gasPrice'] == gas_price:
                del transaction['nonce']
                return send_transaction_original(transaction)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def ensure_transactions_fail(web3: Web3, error_message: str):
        def send_transaction_replacement(transaction):
            del transaction['nonce']
            send_transaction_original(transaction)
            raise Exception(error_message)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def mock_0_pending_txs_in_parity_txqueue(mock, datadir):
        TestPlunger.mock_3_pending_txs_in_parity_txqueue(mock, datadir, '0x0')

    @staticmethod
    def mock_3_pending_txs_in_parity_txqueue(mock, datadir, account: str):
        response = datadir.join('parity').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:8545/rpc", text=response)

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
                Plunger(args("--source parity_txqueue 0x0000011111222223333322222111110000099999")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: one of the arguments --list --wait --override-with-zero-txs is required" in err.getvalue()

    def test_should_complain_about_invalid_sources(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("--source invalid_one,parity_txqueue --wait 0x0000011111222223333322222111110000099999")).main()

        # then
        assert "Unknown source(s): 'invalid_one'." in err.getvalue()

    def test_should_detect_0_pending_transactions_in_parity_txqueue(self, web3, datadir):
        # given
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_0_pending_txs_in_parity_txqueue(mock, datadir)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port 8545 --source parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"There are no pending transactions on unknown from {some_account}\n"

    def test_should_detect_3_pending_transactions_in_parity_txqueue(self, web3, datadir):
        # given
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_in_parity_txqueue(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port 8545 --source parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There are 3 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

"""

    @pytest.mark.skip("cannot mock different request methods on same endpoint, cannot configure different endpoints for same plunger")
    def test_should_ignore_duplicates_when_using_two_sources(self, web3, datadir):
        # given
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_on_jsonrpc(mock, datadir, some_account)
            self.mock_3_pending_txs_in_parity_txqueue(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port 8545 --source jsonrpc_getblock,parity_txqueue --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There are 4 pending transactions on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10
0x53050e62c81fbe440d97d703860096467089bd37b2ad4cc6c699acf217436a64      11

"""

    def test_chain(self, web3):
        # given
        some_account = web3.eth.accounts[0]
        plunger = Plunger(args(f"--rpc-host 0.0.0.0 --rpc-port 8545 --source jsonrpc_getblock --list {some_account}"))

        # then
        assert plunger.chain() == "unknown"

    def test_should_ignore_pending_transactions_if_their_nonce_is_already_used(self, web3, datadir):
        # given
        some_account = web3.eth.accounts[0]

        # and
        self.simulate_transactions(web3, 10)

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_3_pending_txs_on_jsonrpc(mock, datadir, some_account)

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-host 0.0.0.0 --rpc-port 8545 --source jsonrpc_getblock --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""There is 1 pending transaction on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

"""
