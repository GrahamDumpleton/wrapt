#!/bin/sh

echo
echo "INFO: TOX CONFIGURATION"
echo

tox --showconfig

echo
echo "INFO: EXTENSIONS DISABLED"
echo

WRAPT_EXTENSIONS=false tox

STATUS=$?
if test "$STATUS" != "0"
then
    echo
    echo "`basename $0` (extensions disabled): *** Error $STATUS"
    exit 1
fi

echo
echo "INFO: EXTENSIONS ENABLED"
echo

WRAPT_EXTENSIONS=true tox

STATUS=$?
if test "$STATUS" != "0"
then
    echo
    echo "`basename $0` (extensions enabled): *** Error $STATUS"
    exit 1
fi
