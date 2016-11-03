#!/bin/bash

if [[ -z $KONG_HOST ]] ; then
    missing_vars="$missing_vars KONG_HOST"
fi

if [[ -z $HOSTNAME ]] ; then
    missing_vars="$missing_vars HOST_NAME"
fi

if [[ $missing_vars ]] ; then
    echo "missing environment variables: $missing_vars"
    exit 1
fi

python kong_up.py