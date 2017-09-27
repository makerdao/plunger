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

import requests
from texttable import Texttable
from web3 import Web3, HTTPProvider

from plunger.etherscan import Etherscan
from plunger.transaction import Transaction


class Plunger:
    SOURCE_ETHERSCAN = "etherscan"
    SOURCE_PARITY_TXQUEUE = "parity_txqueue"

    def __init__(self, args: list):
        # Define basic arguments
        parser = argparse.ArgumentParser(prog='plunger')
        parser.add_argument("address", help="Ethereum address to check for pending transactions", type=str)
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--source", help=f"Comma-separated list of sources to get pending transactions from"
                                             f" (available: {self.SOURCE_ETHERSCAN}, {self.SOURCE_PARITY_TXQUEUE})",
                            type=lambda x: x.split(','), required=True)

        # Define mutually exclusive action arguments
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument('--list', help="List pending transactions", dest='list', action='store_true')
        action.add_argument('--wait', help="Wait for the pending transactions to clear", dest='wait', action='store_true')
        action.add_argument('--override-with-zero-txs', help="Override the pending transactions with zero-value txs", dest='override', action='store_true')

        # Parse the arguments, validate source
        self.arguments = parser.parse_args(args)
        self.validate_sources()

        # Initialize web3.py
        self.web3 = Web3(HTTPProvider(endpoint_uri=f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"))
        self.web3.eth.defaultAccount = self.arguments.address

    def validate_sources(self):
        # Check if only correct sources have been listed in the value of the `--source` argument
        unknown_sources = set(self.arguments.source) - {self.SOURCE_ETHERSCAN, self.SOURCE_PARITY_TXQUEUE}
        if len(unknown_sources) > 0:
            print(f"Unknown source(s): {str(unknown_sources).replace('{', '').replace('}', '')}.")
            exit(-1)

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
            print(f"")

    def override(self, transactions: list):
        # Override all pending transactions with zero-wei transfer transactions
        for nonce in self.unique_nonces(transactions):
            try:
                gas_price = self.web3.eth.gasPrice
                tx_hash = self.web3.eth.sendTransaction({'from': self.web3.eth.defaultAccount,
                                                         'to': self.web3.eth.defaultAccount,
                                                         'gasPrice': gas_price,
                                                         'nonce': nonce,
                                                         'value': 0})

                print(f"Sent replacement transaction with nonce={nonce}, gas_price={gas_price}, tx_hash={tx_hash}.")
            except Exception as e:
                print(f"Failed to send replacement transaction with nonce={nonce}, gas_price={gas_price}.")
                print(f"   Error: {e}")

    def wait(self, transactions: list):
        print(f"Waiting for the transactions to get mined...")

        # When `get_last_nonce()` stops being lower than the highest pending nonce,
        # it means all pending transactions or their replacements have been mined.
        while self.get_last_nonce() < max(transactions, key=lambda tx: tx.nonce).nonce:
            time.sleep(1)

        print(f"All pending transactions have been mined.")

    @staticmethod
    def unique_nonces(transactions: list) -> list:
        unique_nonces = []
        for transaction in transactions:
            if transaction.nonce not in unique_nonces:
                unique_nonces.append(transaction.nonce)
        return unique_nonces

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
        # Get the list of pending transactions and their details from specified sources
        transactions = []
        if self.SOURCE_ETHERSCAN in self.arguments.source:
            transactions += self.get_pending_transactions_from_etherscan()
        if self.SOURCE_PARITY_TXQUEUE in self.arguments.source:
            transactions += self.get_pending_transactions_from_parity()

        # Ignore these which have been already mined
        last_nonce = self.get_last_nonce()
        transactions = filter(lambda tx: tx.nonce > last_nonce, transactions)

        # Sort by nonce and tx_hash
        return sorted(transactions, key=lambda tx: (tx.nonce, tx.tx_hash))

    def get_pending_transactions_from_etherscan(self) -> list:
        # Get the list of pending transactions and their details from etherscan.io
        return Etherscan(self.chain()).list_pending_txs(self.web3.eth.defaultAccount)

    def get_pending_transactions_from_parity(self) -> list:
        # Get the list of pending transactions and their details from Parity transaction pool
        # First, execute the RPC call and get the response
        request = {"method": "parity_pendingTransactions", "params": [], "id": 1, "jsonrpc": "2.0"}
        response = requests.post(self.web3.currentProvider.endpoint_uri, None, request).json()

        # Then extract pending transactions sent by us from the response and convert them into `Transaction` objects
        items = response['result']
        items = filter(lambda item: item['from'].lower() == self.web3.eth.defaultAccount.lower(), items)
        items = filter(lambda item: item['blockNumber'] is None, items)
        return list(map(lambda item: Transaction(tx_hash=item['hash'], nonce=int(item['nonce'], 16)), items))


if __name__ == "__main__":
    Plunger(sys.argv[1:]).main()
