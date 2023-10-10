#!/bin/bash


# perform all steps, but exit with the cumulative exit code values
exit_code=0

# exit on any failure until we start linting and testing
set -e

# run this script from the directory with the setup.py file, which is one
# directory up from this script
script_dir=$(dirname $(readlink -f $0))
cd $(dirname "$script_dir")

# upgrade the requirements, install the code with testing dependencies
pip install --upgrade -r requirements.txt
pip install --editable .[dev]

# run everything and exit with the cumulative exit code
set +e

# run isort to sort the import statements
echo -e "\n-- RUNNING ISORT"
python -m isort --settings-path "$script_dir/.isort.cfg" src tests
exit_code=$((exit_code + $?))

# run mypy linting for types
echo -e "\n-- RUNNING MYPY"
python -m mypy --config-file "$script_dir/mypy.ini" src
exit_code=$((exit_code + $?))

# run pylint static code analyzer
echo -e "\n-- RUNNING PYLINT"
set -o pipefail
python -m pylint --rcfile "$script_dir/pylintrc" --jobs 0 --fail-under 10.0 src | tee "$script_dir/pylint.log"
exit_code=$((exit_code + ${PIPESTATUS[0]}))

# run pytest with coverage
echo -e "\n-- RUNNING PYTEST AND COVERAGE"
python -m coverage run --source src --data-file tests/.coverage --rcfile tests/.coveragerc -m pytest -c "$script_dir/pytest.ini" -vvvv
exit_code=$((exit_code + $?))
python -m coverage html --data-file tests/.coverage --directory tests/htmlcov --rcfile tests/.coveragerc
exit_code=$((exit_code + $?))
python -m coverage xml --data-file tests/.coverage -o tests/coverage.xml --rcfile tests/.coveragerc
exit_code=$((exit_code + $?))
python -m coverage report -m --fail-under=65 --data-file tests/.coverage --rcfile tests/.coveragerc | tee "$script_dir/coverage.log"
exit_code=$((exit_code + ${PIPESTATUS[0]}))

# cummulative exit code values
exit $exit_code
