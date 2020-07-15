# This file is part of Plunger.
#
# Copyright (C) 2017-2020 reverendus,EdNoepel
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

import sys
from contextlib import contextmanager
from io import StringIO

import py
import pytest
from pytest import fixture
from web3 import HTTPProvider, Web3

from plunger.keys import register_key

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


@fixture(scope="session")
def web3():
    web3 = Web3(HTTPProvider("http://0.0.0.0:8545"))
    web3.eth.defaultAccount = "0x6c626f45e3b7aE5A3998478753634790fd0E82EE"
    register_key(web3, "key_file=tests/data/key1.json,pass_file=/dev/null")
    register_key(web3, "key_file=tests/data/key2.json,pass_file=/dev/null")
    assert len(web3.eth.accounts) > 1
    assert isinstance(web3.eth.accounts[0], str)
    assert isinstance(web3.eth.accounts[1], str)
    return web3


@fixture
def datadir(request):
    return py.path.local(request.module.__file__).join("..").join("data")


def args(arguments):
    return arguments.split()