# This file is part of Maker Keeper Framework.
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

import argparse
import logging

import time

from texttable import Texttable
from web3 import Web3, HTTPProvider

from plunger.etherscan import Etherscan


class Plunger:
    logger = logging.getLogger('plunger')

    def __init__(self):
        # Define basic arguments
        parser = argparse.ArgumentParser(prog='plunger')
        parser.add_argument("address", help="Ethereum address to check for pending transactions", type=str)
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)

        # Define mutually exclusive action arguments
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument('--list', help="List pending transactions", dest='list', action='store_true')
        action.add_argument('--wait', help="Wait for the pending transactions to clear", dest='wait', action='store_true')
        action.add_argument('--override-with-zero-txs', help="Override the pending transactions with zero-value txs", dest='override', action='store_true')

        # Parse the arguments, initialize web3.py
        self.arguments = parser.parse_args()
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.address

    def main(self):
        # Get pending transactions
        pending_transactions = self.get_pending_transactions()

        # List pending transactions, alternatively say there are none
        self.list(pending_transactions)

        # If there is at least one pending transaction...
        if len(pending_transactions) > 0:
            # ...if called with `--override-with-zero-txs`, all of them to clear
            if self.arguments.override:
                self.override()

            # ...if called with either `--override-with-zero-txs` or `--wait`, wait for all of them to clear
            if self.arguments.override or self.arguments.wait:
                self.wait()

    def list(self, transactions):
        if len(transactions) == 0:
            print(f"There are no pending transactions on {self.chain()} from {self.web3.eth.defaultAccount}")
        else:
            print(f"There are {len(transactions)} pending transactions on {self.chain()} from {self.web3.eth.defaultAccount}:")
            print(f"")

            table = Texttable()
            table.set_deco(Texttable.HEADER)
            table.set_cols_dtype(['t', 'i'])
            table.set_cols_align(["l", "r"])
            table.add_rows([["TxHash", "Nonce"]] + list(map(lambda tx: [tx.tx_hash, tx.nonce], transactions)))

            print(table.draw())

    def override(self):
        print(f"Transaction overriding is not implemented yet")
        exit(-1)

    def wait(self):
        print(f"Waiting for the transactions to get mined...")

        #TODO checking Etherscan.io once every ten seconds is probably not the best idea
        #TODO as we can just look at `getTransactionCount` to see if the transactions
        #TODO get mined or not
        #
        #TODO having said that, checking Etherscan.io once a while can be useful as
        #TODO we may discover the pending transactions have disappeared :)
        while len(self.get_pending_transactions()) > 0:
            time.sleep(10)

        print(f"All pending transactions have been mined")

    def chain(self) -> str:
        block_0 = self.web3.eth.getBlock(0)['hash']
        if block_0 == "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3":
            block_1920000 = self.web3.eth.getBlock(1920000)['hash']
            if block_1920000 == "0x94365e3a8c0b35089c1d1195081fe7489b528a84b22199c916180db8b28ade7f":
                return "etclive"
            else:
                return "ethlive"
        elif block_0 == "0xa3c565fc15c7478862d50ccd6561e3c06b24cc509bf388941c25ea985ce32cb9":
            return "kovan"
        elif block_0 == "0x41941023680923e0fe4d74a34bdac8141f2540e3ae90623718e47d66d1ca4a2d":
            return "ropsten"
        elif block_0 == "0x0cd786a2425d16f152c658316c423e6ce1181e15c3295826d7c9904cba9ce303":
            return "morden"
        else:
            return "unknown"

    def get_last_nonce(self):
        return self.web3.eth.getTransactionCount(self.web3.eth.defaultAccount)-1

    def get_pending_transactions(self) -> list:
        last_nonce = self.get_last_nonce()
        etherscan = Etherscan(self.chain())
        txs = etherscan.list_pending_txs(self.web3.eth.defaultAccount)
        filter(lambda tx: tx.nonce > last_nonce, txs)
        return txs


if __name__ == "__main__":
    Plunger().main()
