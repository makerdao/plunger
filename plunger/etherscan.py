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


import requests
from pprint import pprint

from plunger.model import Transaction


class Etherscan:

    def __init__(self, chain: str, api_key: str):
        assert isinstance(chain, str)
        assert isinstance(api_key, str)

        if chain == "mainnet":
            self.url = "api.etherscan.io"
        elif chain == "kovan":
            self.url = "api-kovan.etherscan.io"
        else:
            # TODO for unit testing only, let's find a better solution afterwards
            self.url = "unknown.etherscan.io"
        self.api_key = api_key

    def list_pending_txs(self, address) -> list:
        request_url = f"http://{self.url}/api?module=account&action=txlist&address={address}&apikey={self.api_key}"
        print(f"making request to {request_url}")
        response = requests.get(request_url)
        pprint(response.text)
        # FIXME: The response doesn't contain pending tx's, and API documentation shows no way to query them.

        # TODO: cache tx hash, status, and nonce, return a list of tx hashes
        return []

    def tx_details(self, tx_id) -> Transaction:
        # TODO: No second request is needed; the nonce is included in the request made above.
        raise NotImplementedError
        # return Transaction(tx_hash=tx_id, nonce=nonce)
