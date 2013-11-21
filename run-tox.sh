#!/bin/sh

PATH="$PATH:/usr/local/python/cpython-2.6/bin"
PATH="$PATH:/usr/local/python/cpython-2.7/bin"
PATH="$PATH:/usr/local/python/cpython-3.3/bin"
PATH="$PATH:/usr/local/python/pypy/bin"

export PATH

exec tox "$@"
