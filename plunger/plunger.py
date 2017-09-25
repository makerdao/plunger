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

import web3
from web3 import Web3, HTTPProvider

from plunger.etherscan import Etherscan


class Plunger:
    logger = logging.getLogger('plunger')

    def __init__(self):
        # Define basic arguments
        parser = argparse.ArgumentParser(prog='plunger')
        parser.add_argument("address", help="Ethereum address to operate on", type=str)
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

        # Initialize logging
        # logging.basicConfig(format='%(message)s', level=logging.INFO)
        logging.basicConfig(format='%(asctime)-15s %(levelname)-8s %(name)-8s %(message)s', level=logging.INFO)

    def main(self):
        self.logger.info(f"Plunger on {self.chain()}, connected to {self.web3.currentProvider.endpoint_uri}")
        self.wait_for_sync()
        self.logger.info(f"Checking for pending transactions from {self.web3.eth.defaultAccount}")

        tx_ids = self.get_pending_transactions()
        if len(tx_ids) == 0:
            self.logger.info(f"There are no pending transactions from this address according to Etherscan")
        else:
            #TODO extract to list() method
            self.logger.info(f"There are {len(tx_ids)} pending transactions from this address: {tx_ids}")
            self.logger.info(f"")

            # If called with `--override-with-zero-txs`, override all pending transactions
            if self.arguments.override:
                self.override()

            # If called with either `--override-with-zero-txs` or `--wait`, wait for all pending transactions
            if self.arguments.override or self.arguments.wait:
                self.wait()

    def override(self):
        self.logger.info(f"Transaction overriding is not implemented yet")
        exit(-1)

    def wait(self):
        self.logger.info(f"Waiting for the transactions to get mined...")

        #TODO checking Etherscan.io once every ten seconds is probably not the best idea
        #TODO as we can just look at `getTransactionCount` to see if the transactions
        #TODO get mined or not
        #
        #TODO having said that, checking Etherscan.io once a while can be useful as
        #TODO we may discover the pending transactions have disappeared :)
        while len(self.get_pending_transactions()) > 0:
            time.sleep(10)

        self.logger.info(f"All pending transactions have been mined")

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

    def wait_for_sync(self):
        # wait for the client to have at least one peer
        if self.web3.net.peerCount == 0:
            self.logger.info(f"Waiting for the node to have at least one peer...")
            while self.web3.net.peerCount == 0:
                time.sleep(0.25)

        # wait for the client to sync completely
        if self.web3.eth.syncing:
            self.logger.info(f"Waiting for the node to sync...")
            while self.web3.eth.syncing:
                time.sleep(0.25)

    def get_last_nonce(self):
        return self.web3.eth.getTransactionCount(self.web3.eth.defaultAccount)-1

    def get_pending_transactions(self):
        last_nonce = self.get_last_nonce()
        etherscan = Etherscan(self.chain())
        txs = etherscan.list_pending_txs(self.web3.eth.defaultAccount)
        filter(lambda tx: etherscan.tx_nonce(tx) > last_nonce, txs)
        return txs


if __name__ == "__main__":
    Plunger().main()
