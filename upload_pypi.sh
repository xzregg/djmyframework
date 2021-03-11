#!/usr/bin/env bash

rm -rf dj_myframework.egg-info/
rm -rf build/
rm -rf dist/
python setup.py sdist build
twine upload dist/* $*