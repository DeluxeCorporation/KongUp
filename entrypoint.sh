#!/bin/bash

if [[ -z $KONG_UP_KONG_ENVIRONMENT ]] ; then
    missing_vars="$missing_vars KONG_UP_KONG_ENVIRONMENT"
fi

if [[ -z $KONG_UP_KONG_HOST ]] ; then
    missing_vars="$missing_vars KONG_UP_KONG_HOST"
fi

if [[ -z $KONG_UP_HIPCHAT_URL ]] ; then
    missing_vars="$missing_vars KONG_UP_HIPCHAT_URL"
fi

if [[ -z $KONG_UP_LOG_LEVEL ]] ; then
    missing_vars="$missing_vars KONG_UP_LOG_LEVEL"
fi

if [[ $missing_vars ]] ; then
    echo "missing environment variables: $missing_vars"
    exit 1
fi

python kong_up.py
