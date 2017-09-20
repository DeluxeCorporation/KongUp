'''
KongUp is an application that automatically
wires up APIs to Kong when deployed in a
Rancher Cattle Env
'''

import os
import re
import sys
import time
import logging
import json
import requests
import nmap
from docker import Client

KONG_ENVIRONMENT = os.getenv("KONG_UP_KONG_ENVIRONMENT")
KONG_HOST = os.getenv("KONG_UP_KONG_HOST")
HIPCHAT_URL = os.getenv("KONG_UP_HIPCHAT_URL")
LOG_LEVEL = os.getenv("KONG_UP_LOG_LEVEL")

log = logging.getLogger('kong_up')
log.setLevel(LOG_LEVEL)
KONG_UP_LOGGER = logging.StreamHandler(stream=sys.stdout)
KONG_UP_LOGGER.setLevel(LOG_LEVEL)
log.addHandler(KONG_UP_LOGGER)

def get_rancher_dns_name(container):
    '''
    Return the Rancher DNS name of the given container.
    Inspect the container and use the value in
    'io.rancher.stack_service.name' container label
    and return the DNS name
    '''

    stack_service_name = container['Config']['Labels']['io.rancher.stack_service.name']

    # From : 'DEV/d-dwsotodfswconverter-gd', To: 'd-dwsotodfswconverter-gd.DEV'
    return re.sub(r"(.*)/(.*)", r"\2.\1", stack_service_name)

def get_open_port(host):
    '''
    Return the *first* open port on host
    after running a port scan using nmap.
    '''

    wait_time = 1
    scanner = nmap.PortScanner()

    for attempt in range(5):
        wait_time *= 2
        log.info('Sleeping for %i seconds', wait_time)
        time.sleep(wait_time)
        scan_results = scanner.scan(host, arguments='-PN').get('scan')

        if not bool(scan_results):
            log.warning('Service not started yet. retrying attempt: %i', attempt)
            continue
        else:
            open_ports = list(scan_results.values())[0].get('tcp', {})
            if len(open_ports.keys()) != 1:
                log.warning('Exactly one port supported, but %i given, retrying attempt %i'
                            ,len(open_ports.keys()), attempt)
                continue
            else:
                return list(open_ports.keys())[0]

def get_api(uri):
    '''
    Return API if API exists in kong, else False. Check only
    the first uri in the api.
    '''

    apis = requests.get('http://' + KONG_HOST + ':8001/apis/').json()['data']
    for api in apis:
        if api['uris'][0] == uri:
            return api
    return {}

def get_gateway_visibility(container):
    '''
    Return True if GATEWAY_VISIBLE label is set to "True", False
    otherwise.
    '''

    return container['Config']['Labels'].get('GATEWAY_VISIBLE') == "True"

def get_environment(container):
    '''
    Retrun value associated with 'ENVIRONMENT'
    '''

    return container['Config']['Labels'].get('ENVIRONMENT')

def get_uri(container):
    '''
    Return the value associated with the label
    GATEWAY_URI
    '''

    return container['Config']['Labels'].get('GATEWAY_URI')

def format_api_name(name):
    '''
    Return the name after so that it complies with Kong's 
    standards
    '''
    
    return name.replace("/", "-")

def add_container_to_kong(container):
    '''
    Use the info in the container to add it as an API to Kong
    '''

    gateway_visible = get_gateway_visibility(container)
    environment = get_environment(container)

    if gateway_visible and environment == KONG_ENVIRONMENT:
        host = get_rancher_dns_name(container)
        port = get_open_port(host)
        uri = get_uri(container)

        if  all([host, uri, port]):
            upstream_url = "http://" + host + ":" + str(port)
            api = get_api(uri)
            if api:
                api['upstream_url'] = upstream_url
            else:
                api = {
                    "upstream_url": upstream_url,
                    "uris": uri,
                    "name": format_api_name(uri[1:]),
                    "created_at": int(time.time())}

            k = requests.put('http://' + KONG_HOST + ':8001/apis/', data=api)

            if k.status_code == 201 or k.status_code == 200:
                log.info("Successfully added %s to gateway", uri)
                notifier(True, uri)
            else:
                log.error("Could not add api to gateway: %s", str(k.json()))
                notifier(False, uri)
    else:
        log.info('Not Adding to Kong: %s', str(container))

def notifier(is_successful, uri):
    '''
    Send a notification to hipchat

    :param is_successful: (Boolean) - True if api was added successfully, false otherwise
    :param uri: (String) - Request path to the api that was/wasn't added
    '''
    gateway_link = "https://" + KONG_HOST + ":8243" + uri
    if is_successful:
        message = '''{{"color":"green",
                       "message":"{API} KongedUP (successful), {link}",
                       "notify":true,
                       "message_format":"text"}}'''.format(API=uri, link=gateway_link)
    else:
        message = '''{{"color":"red",
                       "message":"{API} not KongedUP (failed)",
                       "notify":true,
                       "message_format":"text"}}'''.format(API=uri)

    requests.post(HIPCHAT_URL, data=message, headers={"Content-Type": "application/json"})


def listener():
    '''
    Listen to docker events, and invoke event_handler if a
    container was started.
    '''
    log.info('Listening for Docker events')
    cli = Client(version='auto')
    for event in cli.events():
        event = json.loads(event.decode('utf-8'))
        if event.get('status') == 'start':
            log.info('Event - Container starting: %s', event)
            try:
                event_handler(event)
            except Exception as event_exception:
                notifier(False, str(event_exception))
                continue

def event_handler(event):
    '''
    Inspect the container, and send it to add_container_to_kong
    '''
    cli = Client(version='auto')
    container = cli.inspect_container(event['id'])
    add_container_to_kong(container)

def rewire():
    '''
    Add all existing containers to Kong
    '''
    cli = Client(version='auto')
    time.sleep(5)
    containers = cli.containers()
    for container in containers:
        add_container_to_kong(cli.inspect_container(container['Id']))

if __name__ == '__main__':
    log.info("KongUp started")
    rewire()
    listener()
