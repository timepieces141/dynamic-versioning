#!/bin/bash

## Clean up from unit tests, builds, etc.

# from building
find . -type d -name __pycache__ -exec rm -rf {} \; 2>/dev/null
find . -type f -name *.pyc -exec rm -f {} \; 2>/dev/null
find . -type d -name build -exec rm -rf {} \; 2>/dev/null
find . -type d -name dist -exec rm -rf {} \; 2>/dev/null
find . -type d -name *egg-info -exec rm -rf {} \; 2>/dev/null
find . -type f -name MANIFEST -exec rm -f {} \; 2>/dev/null
find . -type f -name version.py -exec rm -f {} \; 2>/dev/null

# from testing
find . -type d -name .pytest_cache -exec rm -rf {} \; 2>/dev/null
find . -type d -name .cache -exec rm -rf {} \; 2>/dev/null
find . -type d -name htmlcov -exec rm -rf {} \; 2>/dev/null
find . -type d -name .coverage -exec rm -rf {} \; 2>/dev/null

# logs
find . -type f -name *.log -exec rm -f {} \; 2>/dev/null
find . -type d -name *.log -exec rm -rf {} \; 2>/dev/null

# just Mac being a pain
find . -type f -name .DS_Store -exec rm -f {} \; 2>/dev/null
