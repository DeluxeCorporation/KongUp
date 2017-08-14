#!/bin/bash

if [[ -z $KONG_HOST ]] ; then
    missing_vars="$missing_vars KONG_HOST"
fi

if [[ -z $KONG_ENVIRONMENT ]] ; then
    missing_vars="$missing_vars KONG_ENVIRONMENT"
fi

if [[ -z $HIPCHAT_URL ]] ; then
    missing_vars="$missing_vars HIPCHAT_URL"
fi

if [[ $missing_vars ]] ; then
    echo "missing environment variables: $missing_vars"
    exit 1
fi

python kong_up.py
