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

from plunger.etherscan import Etherscan


if __name__ == "__main__":
    etherscan = Etherscan()
    txs = etherscan.list_pending_txs('0xc4522328d5467d90a8d2cd8391dd3aa5b53e02b0')
    print(txs)
    for tx in txs:
        print(etherscan.tx_nonce(tx))