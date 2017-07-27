!/bin/bash

if [[ -z $DEV_KONG_HOST ]] ; then
    missing_vars="$missing_vars DEV_KONG_HOST"
fi

if [[ -z $QA_KONG_HOST ]] ; then
    missing_vars="$missing_vars QA_KONG_HOST"
fi

if [[ -z $UAT_KONG_HOST ]] ; then
    missing_vars="$missing_vars UAT_KONG_HOST"
fi
if [[ -z $XUAT_KONG_HOST ]] ; then
    missing_vars="$missing_vars XUAT_KONG_HOST"
fi
if [[ -z $PREPROD_KONG_HOST ]] ; then
    missing_vars="$missing_vars PREPROD_KONG_HOST"
fi

if [[ $missing_vars ]] ; then
    echo "missing environment variables: $missing_vars"
    exit 1
fi

python kong_up.py
