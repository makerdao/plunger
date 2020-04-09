#!/bin/sh

# Pull the docker image
docker pull makerdao/testchain-pymaker:unit-testing

# Remove existing container if tests not gracefully stopped
docker-compose down

# Start parity and wait to initialize
docker-compose up -d parity-plunger
sleep 2

PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_plunger.py $@
TEST_RESULT=$?

# Cleanup
docker-compose down
docker-compose up -d parity-plunger
sleep 2
PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_wait.py $@
TEST_RESULT=$((TEST_RESULT+$?))

# Cleanup
docker-compose down
docker-compose up -d parity-plunger
sleep 2
PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_nonce_gap.py $@
TEST_RESULT=$((TEST_RESULT+$?))

# Cleanup
docker-compose down
docker-compose up -d parity-plunger
sleep 2
PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_override.py $@
TEST_RESULT=$((TEST_RESULT+$?))

# Cleanup
docker-compose down
docker-compose up -d parity-plunger
sleep 2
PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_custom_gas.py $@
TEST_RESULT=$((TEST_RESULT+$?))

# Cleanup
docker-compose down
docker-compose up -d parity-plunger
sleep 2
PYTHONPATH=$PYTHONPATH:. py.test --cov=plunger --cov-report=term --cov-append tests/test_tx_err.py $@
TEST_RESULT=$((TEST_RESULT+$?))

# Cleanup
docker-compose down
exit $TEST_RESULT
