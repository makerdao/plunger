# This file is part of Plunger.
#
# Copyright (C) 2017-2020 reverendus, EdNoepel
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
import requests
import sys
import time
import web3
from lxml import html

from plunger.etherscan import Etherscan
from plunger.keys import register_key
from plunger.model import Transaction
from texttable import Texttable
from web3 import Web3, HTTPProvider


class Plunger:
    SOURCE_ETHERSCAN = "etherscan"
    SOURCE_PARITY_TXQUEUE = "parity_txqueue"
    SOURCE_GETH_GETBLOCK = "geth_getblock"

    def __init__(self, args: list):
        # Define basic arguments
        parser = argparse.ArgumentParser(prog='plunger')
        parser.add_argument("address", help="Ethereum address to check for pending transactions", type=str)
        parser.add_argument("--rpc-host", help="JSON-RPC host (default: `localhost')", default="localhost", type=str)
        parser.add_argument("--rpc-port", help="JSON-RPC port (default: `8545')", default=8545, type=int)
        parser.add_argument("--gas-price", help="Gas price (in Wei) for overriding transactions", default=0, type=int)
        parser.add_argument("--source", help=f"Comma-separated list of sources to use for pending transaction discovery"
                                             f" (available: {self.SOURCE_ETHERSCAN}, {self.SOURCE_PARITY_TXQUEUE}, {self.SOURCE_GETH_GETBLOCK})",
                            type=lambda x: x.split(','), required=True)

        # Define mutually exclusive action arguments
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument('--list', help="List pending transactions", dest='list', action='store_true')
        action.add_argument('--wait', help="Wait for the pending transactions to clear", dest='wait', action='store_true')
        action.add_argument('--override-with-zero-txs', help="Override the pending transactions with zero-value txs", dest='override', action='store_true')

        parser.add_argument("--eth-key", type=str,
                            help="Ethereum private key to use (e.g. 'key_file=aaa.json,pass_file=aaa.pass') for unlocking account")
        parser.add_argument("--etherscan-key", type=str,
                            help=f"Etherscan API key to use; required when using {self.SOURCE_ETHERSCAN} as a --source")

        # Parse the arguments, validate source
        self.arguments = parser.parse_args(args)
        self.validate_sources()

        # Initialize pending transactions list
        self.transactions = []

        # Initialize web3.py
        if self.arguments.rpc_host.startswith("http"):
            endpoint_uri = f"{self.arguments.rpc_host}:{self.arguments.rpc_port}"
        else:
            endpoint_uri = f"http://{self.arguments.rpc_host}:{self.arguments.rpc_port}"
        self.web3 = Web3(HTTPProvider(endpoint_uri=endpoint_uri))
        self.web3.eth.defaultAccount = self.arguments.address
        if self.arguments.eth_key:
            register_key(self.web3, self.arguments.eth_key)

    def validate_sources(self):
        # Check if only correct sources have been listed in the value of the `--source` argument
        unknown_sources = set(self.arguments.source) - {self.SOURCE_ETHERSCAN, self.SOURCE_PARITY_TXQUEUE, self.SOURCE_GETH_GETBLOCK}
        if len(unknown_sources) > 0:
            print(f"Unknown source(s): {str(unknown_sources).replace('{', '').replace('}', '')}.", file=sys.stderr)
            exit(-1)

    def main(self):
        # Get pending transactions
        self.transactions = self.get_pending_transactions()

        # List pending transactions, alternatively say there are none
        self.list(self.transactions)

        # If there is at least one pending transaction...
        if len(self.transactions) > 0:
            # ...if called with `--override-with-zero-txs`, all of them to clear
            if self.arguments.override:
                self.override(self.transactions)

            # ...if called with either `--override-with-zero-txs` or `--wait`, wait for all of them to clear
            if self.arguments.override or self.arguments.wait:
                self.wait(self.transactions)

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
        last_nonce = self.get_last_nonce()
        for nonce in self.unique_nonces(transactions):
            ## Check for nonce gaps
            # If gap exists, set pending transaction nonce to 1 above last sent transaction
            if nonce > last_nonce + 1:
                nonce = last_nonce + 1

            try:
                gas_price = self.web3.eth.gasPrice if self.arguments.gas_price == 0 else self.arguments.gas_price
                tx_hash = self.web3.eth.sendTransaction({'from': self.web3.eth.defaultAccount,
                                                         'to': self.web3.eth.defaultAccount,
                                                         'gasPrice': gas_price,
                                                         'nonce': nonce,
                                                         'value': 0})

                # increment last nonce to account for successful transaction
                last_nonce += 1

                ## Remove sent transaction from pending transaction queue
                # As transactions are already sorted and duplicates are removed, can safely pop in order
                self.transactions.pop(0)

                print(f"Sent replacement transaction with nonce={nonce}, gas_price={gas_price}, tx_hash={self.web3.toHex(tx_hash)}.")
            except Exception as e:
                print(f"Failed to send replacement transaction with nonce={nonce}, gas_price={gas_price}.")
                print(f"   Error: {e}")

    def wait(self, transactions: list):
        print(f"Waiting for the transactions to get mined...")

        # When `get_last_nonce()` stops being lower than the highest pending nonce,
        # it means all pending transactions or their replacements have been mined.
        if len(self.transactions) > 0:
            while self.get_last_nonce() < max(self.transactions, key=lambda tx: tx.nonce).nonce:
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
        if self.web3.eth.chainId == 1:
            return "mainnet"
        elif self.web3.eth.chainId == 42:
            return "kovan"
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
        if self.SOURCE_GETH_GETBLOCK in self.arguments.source:
            transactions += self.get_pending_transactions_from_geth()

        # Ignore these which have been already mined
        last_nonce = self.get_last_nonce()
        transactions = filter(lambda tx: tx.nonce > last_nonce, transactions)

        # Remove duplicates, sort by nonce and tx_hash
        return sorted(set(transactions), key=lambda tx: (tx.nonce, tx.tx_hash))

    def get_pending_transactions_from_etherscan(self) -> list:
        # Get the list of pending transactions and their details from etherscan.io
        return Etherscan(self.chain(), self.arguments.etherscan_key).list_pending_txs(self.web3.eth.defaultAccount)

    def get_pending_transactions_from_parity(self) -> list:
        # Get the list of pending transactions and their details from Parity transaction pool
        # First, execute the RPC call and get the response
        request = {"method": "parity_pendingTransactions", "params": [], "id": 1, "jsonrpc": "2.0"}
        response = requests.post(self.web3.provider.endpoint_uri + "/rpc", None, request).json()

        # Then extract pending transactions sent by us from the response and convert them into `Transaction` objects
        items = response['result']
        items = filter(lambda item: item['from'].lower() == self.web3.eth.defaultAccount.lower(), items)
        items = filter(lambda item: item['blockNumber'] is None, items)
        return list(map(lambda item: Transaction(tx_hash=item['hash'], nonce=int(item['nonce'], 16)), items))

    def get_pending_transactions_from_geth(self) -> list:
        request = {"method": "eth_getBlockByNumber", "params": ["pending", True], "id": 1, "jsonrpc": "2.0"}
        response = requests.post(self.web3.provider.endpoint_uri + "/rpc", None, request).json()
        items = response['result']['transactions']
        items = filter(lambda item: item['from'].lower() == self.web3.eth.defaultAccount.lower(), items)
        return list(map(lambda item: Transaction(tx_hash=item['hash'], nonce=int(item['nonce'], 16)), items))


if __name__ == "__main__":
    Plunger(sys.argv[1:]).main()
