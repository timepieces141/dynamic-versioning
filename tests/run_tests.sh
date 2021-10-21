#!/bin/bash

# Wrapper script for running all the tests using pytest and coverage

# run the test
cd `dirname $0`
PYTHONPATH="../src" python -m coverage run --source ../src/dynamic_versioning -m pytest $@
EXIT_CODE=$?

# invoke pylint on source packages
echo
echo "Pylint Analysis"
echo "==============="
find ../src -name "*.py" -exec pylint --fail-under 9.97 {} + | tee pylint.log
EXIT_CODE=$((EXIT_CODE + ${PIPESTATUS[0]}))

# generate coverage report
echo
echo "Coverage Report"
echo "==============="
python -m coverage html
set -o pipefail
python -m coverage report -m --fail-under=77 | tee coverage.log
EXIT_CODE=$((EXIT_CODE + ${PIPESTATUS[0]}))

exit $EXIT_CODE
