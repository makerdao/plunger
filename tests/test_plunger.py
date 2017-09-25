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

import pytest

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


def args(arguments):
    return arguments.split()


class TestPlunger:
    def test_should_print_usage_when_no_arguments(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args('')).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: the following arguments are required: address" in err.getvalue()

    def test_should_print_usage_only_address_specified(self):
        # when
        with captured_output() as (out, err):
            with pytest.raises(SystemExit):
                Plunger(args('0x0000011111222223333322222111110000099999')).main()

        # then
        assert "usage: plunger" in err.getvalue()
        assert "error: one of the arguments --list --wait --override-with-zero-txs is required" in err.getvalue()
