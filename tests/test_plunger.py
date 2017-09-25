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

import os
import sys
from contextlib import contextmanager
from io import StringIO

import py
import pytest
import requests_mock
from pytest import fixture
from web3 import TestRPCProvider, Web3

sys.path.append(os.path.dirname(__file__) + "/..")

from plunger.plunger import Plunger


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


@fixture
def datadir(request):
    return py.path.local(request.module.__file__).join("..").join("data")


def args(arguments):
    return arguments.split()


class TestPlunger:
    def test_should_print_usage_when_no_arguments(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: the following arguments are required: address" in err.getvalue()

    def test_should_print_usage_when_only_address_specified(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args("0x0000011111222223333322222111110000099999")).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: one of the arguments --list --wait --override-with-zero-txs is required" in err.getvalue()

    def test_should_detect_0_pending_transactions_on_etherscan(self, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", 28545))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            mock.get(f"https://unknown.etherscan.io/txsPending?a={some_account}", text=datadir.join('0_pending_txs-list.html').read_text('utf-8'))

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port 28545 --list {some_account}")).main()

        # then
        assert out.getvalue() == f"There are no pending transactions on unknown from {some_account}\n"

    def test_should_detect_3_pending_transactions_on_etherscan(self, datadir):
        # given
        web3 = Web3(TestRPCProvider("127.0.0.1", 28546))
        some_account = web3.eth.accounts[0]

        # when
        with requests_mock.Mocker(real_http=True) as mock:
            mock.get(f"https://unknown.etherscan.io/txsPending?a={some_account}", text=datadir.join('3_pending_txs-list.html').read_text('utf-8'))
            mock.get(f"https://unknown.etherscan.io/tx/0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9", text=datadir.join('3_pending_txs-get1.html').read_text('utf-8'))
            mock.get(f"https://unknown.etherscan.io/tx/0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a", text=datadir.join('3_pending_txs-get2.html').read_text('utf-8'))
            mock.get(f"https://unknown.etherscan.io/tx/0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559", text=datadir.join('3_pending_txs-get3.html').read_text('utf-8'))

            with captured_output() as (out, err):
                Plunger(args(f"--rpc-port 28546 --list {some_account}")).main()

        # then
        print(out.getvalue())
        assert out.getvalue() == f"""There are 3 pending transactions on unknown from 0x82a978b3f5962a5b0957d9ee9eef472ee55b42f1:

                              TxHash                                 Nonce
==========================================================================
0x7bc44a24f93df200a3bd172a5a690bec50c215e7a84fa794bacfb61a211d6559       8
0x72e7a42d3e1b0773f62cfa9ee2bc54ff904a908ac2a668678f9c4880fd046f7a       9
0x124cb0887d0ea364b402fcc1369b7f9bf4d651bc77d2445aefbeab538dd3aab9      10
"""
