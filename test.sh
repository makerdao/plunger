#!/bin/sh

py.test --cov=plunger --cov-report=term --cov-append tests/ $@
