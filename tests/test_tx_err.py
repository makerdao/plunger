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


import pytest
import requests_mock

from plunger.plunger import Plunger
from tests.conftest import args, captured_output
from tests.test_plunger import TestPlungerUtils


class TestPlungerTxError(TestPlungerUtils):

    @pytest.mark.timeout(20)
    def test_should_handle_transaction_sending_errors(self, web3, datadir):
        with captured_output() as (out, err):
            # given
            web3.eth.defaultAccount = web3.eth.accounts[0]
            some_account = web3.eth.accounts[0]

            # and
            self.simulate_transactions(web3, 10)
            self.ensure_transactions_fail(web3, "Simulated transaction failure")

            # when
            with requests_mock.Mocker(real_http=True) as mock:
                self.mock_3_pending_txs_on_jsonrpc(mock, datadir, some_account)

                plunger = Plunger(args(f"--rpc-port 8545 --gas-price 1 --source jsonrpc_getblock --override-with-zero-txs {some_account}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for transaction failure simulation
                plunger.main()

            # then
            assert out.getvalue() == f"""WARNING: jsonrpc_getblock requires Parity/OpenEthereum in mining configuration
There is 1 pending transaction on unknown from {some_account}:

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
