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

from lxml import html
import requests


class Etherscan:
    def list_pending_txs(self, address) -> list:
        page = requests.get(f"https://etherscan.io/txsPending?a={address}")
        tree = html.fromstring(page.content)
        tx_ids = tree.xpath('//table[contains(@class,"table")]/tbody//td[1]/span[@class="address-tag"]/a/text()')
        return tx_ids

    def tx_nonce(self, tx_id) -> int:
        page = requests.get(f"https://etherscan.io/tx/{tx_id}")
        tree = html.fromstring(page.content)
        return int(tree.xpath('//span[contains(@title,"The transaction nonce")]/text()')[0].strip())
