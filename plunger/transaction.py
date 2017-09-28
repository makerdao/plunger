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


class Transaction:
    def __init__(self, tx_hash, nonce):
        self.tx_hash = tx_hash
        self.nonce = nonce

    def __eq__(self, other):
        return self.tx_hash == other.tx_hash and \
               self.nonce == other.nonce

    def __hash__(self):
        return hash(self.tx_hash) + hash(self.nonce)
