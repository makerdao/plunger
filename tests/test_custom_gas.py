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
import re
import requests_mock

from plunger.plunger import Plunger
from tests.conftest import args, captured_output
from tests.test_plunger import TestPlungerUtils


class TestPlungerCustomGas(TestPlungerUtils):

    @pytest.mark.timeout(30)
    def test_should_use_custom_gas_price_when_overriding_transactions(self, web3, datadir):
        with captured_output() as (out, err):
            # given
            web3.eth.defaultAccount = web3.eth.accounts[0]
            some_account = web3.eth.accounts[0]
            some_gas_price = 150000000

            # and
            self.simulate_transactions(web3, 10)
            self.ensure_transactions(web3, [10], some_gas_price)

            # when
            with requests_mock.Mocker(real_http=True) as mock:
                self.mock_3_pending_txs_on_jsonrpc(mock, datadir, some_account)

                plunger = Plunger(args(f"--rpc-port 8545 --source jsonrpc_getblock --override-with-zero-txs --gas-price {some_gas_price} {some_account}"))
                plunger.web3 = web3  # we need to set `web3` as it has `sendTransaction` mocked for nonce comparison
                plunger.main()

            # then
            print(out.getvalue())
            assert re.match(f"""WARNING: jsonrpc_getblock requires Parity/OpenEthereum in mining configuration
There is 1 pending transaction on unknown from {some_account}:

                              TxHash                                 Nonce
==========================================================================
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10

Sent replacement transaction with nonce=10, gas_price={some_gas_price}, tx_hash=0x[0-9a-f]{{64}}.
Waiting for the transactions to get mined...
All pending transactions have been mined.
""", out.getvalue(), re.MULTILINE)

            # and
            assert web3.eth.getTransactionCount(some_account) == 11
