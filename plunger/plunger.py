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

import argparse
import sys
import time

from texttable import Texttable
from web3 import Web3, HTTPProvider

from plunger.etherscan import Etherscan


class Plunger:
    def __init__(self, args: list):
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
        self.arguments = parser.parse_args(args)
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.address

    def main(self):
        # Get pending transactions
        transactions = self.get_pending_transactions()

        # List pending transactions, alternatively say there are none
        self.list(transactions)

        # If there is at least one pending transaction...
        if len(transactions) > 0:
            # ...if called with `--override-with-zero-txs`, all of them to clear
            if self.arguments.override:
                self.override(transactions)

            # ...if called with either `--override-with-zero-txs` or `--wait`, wait for all of them to clear
            if self.arguments.override or self.arguments.wait:
                self.wait(transactions)

    def list(self, transactions):
        # Print the number of pending transactions
        if len(transactions) == 0:
            print(f"There are no pending transactions on {self.chain()} from {self.web3.eth.defaultAccount}")
        elif len(transactions) == 1:
            print(f"There is 1 pending transaction on {self.chain()} from {self.web3.eth.defaultAccount}:")
        else:
            print(f"There are {len(transactions)} pending transactions on {self.chain()} from {self.web3.eth.defaultAccount}:")

        # Print the table with pending transactions, if there are any
        if len(transactions) > 0:
            table = Texttable()
            table.set_deco(Texttable.HEADER)
            table.set_cols_dtype(['t', 'i'])
            table.set_cols_align(["l", "r"])
            table.add_rows([["TxHash", "Nonce"]] + list(map(lambda tx: [tx.tx_hash, tx.nonce], transactions)))

            print("")
            print(table.draw())

    def override(self, transactions: list):
        print(f"Transaction overriding is not implemented yet")
        exit(-1)

    def wait(self, transactions: list):
        print(f"")
        print(f"Waiting for the transactions to get mined...")

        # When `get_last_nonce()` stops being lower than the highest pending nonce,
        # it means all pending transactions or their replacements have been mined
        while self.get_last_nonce() < max(transactions, key=lambda tx: tx.nonce).nonce:
            time.sleep(5)

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
        # Get the list of pending transactions and their details from etherscan.io
        transactions = Etherscan(self.chain()).list_pending_txs(self.web3.eth.defaultAccount)

        # Ignore these which have been already mined
        last_nonce = self.get_last_nonce()
        transactions = filter(lambda tx: tx.nonce > last_nonce, transactions)

        # Sort by nonce and tx_hash
        return sorted(transactions, key=lambda tx: (tx.nonce, tx.tx_hash))


if __name__ == "__main__":
    Plunger(sys.argv[1:]).main()
