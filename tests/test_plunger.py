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

import pytest
import requests_mock
from web3 import Web3

from plunger.plunger import Plunger
from tests.conftest import args, captured_output


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
        # def send_transaction_replacement(transaction):
        #     if transaction['nonce'] == nonces.pop(0) and transaction['gasPrice'] == gas_price:
        #         del transaction['nonce']
        #         return send_transaction_original(transaction)
        #
        # send_transaction_original = web3.eth.sendTransaction
        # web3.eth.sendTransaction = send_transaction_replacement
        pass

    @staticmethod
    def ensure_transactions_fail(web3: Web3, error_message: str):
        def send_transaction_replacement(transaction):
            del transaction['nonce']
            send_transaction_original(transaction)
            raise Exception(error_message)

        send_transaction_original = web3.eth.sendTransaction
        web3.eth.sendTransaction = send_transaction_replacement

    @staticmethod
    def mock_0_pending_txs_on_jsonrpc(mock, datadir):
        TestPlunger.mock_3_pending_txs_on_jsonrpc(mock, datadir, '0x0')

    @staticmethod
    def mock_3_pending_txs_on_jsonrpc(mock, datadir, account: str):
        response = datadir.join('jsonrpc').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:8545/rpc", text=response)

    @staticmethod
    def mock_0_pending_txs_in_parity_txqueue(mock, datadir):
        TestPlunger.mock_3_pending_txs_in_parity_txqueue(mock, datadir, '0x0')

    @staticmethod
    def mock_3_pending_txs_in_parity_txqueue(mock, datadir, account: str):
        response = datadir.join('parity').join('response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:8545/rpc", text=response)


class TestPlunger(TestPlungerUtils):
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
        plunger = Plunger(args(f"--rpc-port 8545 --source jsonrpc_getblock --list {some_account}"))

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
                Plunger(args(f"--rpc-port 8545 --source jsonrpc_getblock --list {some_account}")).main()

        # then
        assert out.getvalue() == f"""WARNING: jsonrpc_getblock requires Parity/OpenEthereum in mining configuration
There is 1 pending transaction on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

"""
