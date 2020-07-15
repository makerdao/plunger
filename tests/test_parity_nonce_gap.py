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

import pytest
import re
import requests_mock

from plunger.plunger import Plunger
from tests.conftest import args, captured_output
from tests.test_plunger import TestPlungerUtils


class TestPlungerNonceGap(TestPlungerUtils):

    # Create a set of transactions in the pool with nonces 9 and 11
    @staticmethod
    def mock_noncegapped_txs_in_parity_txqueue(mock, datadir, account: str):
        response = datadir.join('parity').join('nonce_gap_response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:8545/rpc", text=response)

    @staticmethod
    def mock_noncegapped_first_txs_in_parity_txqueue(mock, datadir, account: str):
        response = datadir.join('parity').join('duplicate_nonce_gap_response.json').read_text('utf-8')
        response = response.replace('OUR_ADDRESS', account.upper())
        mock.post(f"http://localhost:8545/rpc", text=response)

    def test_should_handle_parity_tx_queue_nonce_gap(self, web3, datadir):
        # time.sleep(30)
        # given
        web3.eth.defaultAccount = web3.eth.accounts[0]
        some_account = web3.eth.accounts[0]
        some_gas_price = 150000000

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_noncegapped_txs_in_parity_txqueue(mock, datadir, some_account)

            with captured_output() as (out, err):
                # and
                self.simulate_transactions(web3, 9)

                plunger = Plunger(args(f"--rpc-port 8545 --source parity_txqueue --override-with-zero-txs {some_account} --gas-price {some_gas_price}"))
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
    def test_should_handle_duplicated_nonce_gaps_on_first_transaction(self, web3, datadir):
        # time.sleep(30)
        # given
        web3.eth.defaultAccount = web3.eth.accounts[3]
        some_account = web3.eth.accounts[3]
        some_gas_price = 150000000

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            self.mock_noncegapped_first_txs_in_parity_txqueue(mock, datadir, some_account)

            with captured_output() as (out, err):

                plunger = Plunger(args(
                    f"--rpc-port 8545 --source parity_txqueue --override-with-zero-txs {some_account} --gas-price {some_gas_price}"))
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
