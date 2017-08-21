from docker import Client
import socket
import json
import os
import requests
import time
import logging
import sys
import nmap
import re

KONG_ENVIRONMENT = os.getenv("KONG_ENVIRONMENT")
KONG_HOST = os.getenv("KONG_HOST")
HOSTNAME = os.getenv("HOSTNAME")
HIPCHAT_URL = os.getenv("HIPCHAT_URL")

log = logging.getLogger('kong_up')
log.setLevel('INFO')
kong_up_logger = logging.StreamHandler(stream=sys.stdout)
kong_up_logger.setLevel('INFO')
log.addHandler(kong_up_logger)


def get_rancher_DNS_name(container):
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

    nm = nmap.PortScanner()
    open_ports = list(nm.scan(host, arguments='-PN')['scan'].values())[0]['tcp']

    if len(open_ports.keys()) != 1:
        log.fatal('Only open port per service is supported')
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
    return False


def add_to_kong(uri, port):
    '''
    Add uri to Kong on port 
    '''
    upstream_url = "http://" + HOSTNAME + ":" + port
    api = get_api(uri)

    if api:
        api['upstream_url'] = upstream_url
    else:
        api = {
            "upstream_url": upstream_url,
            "uris": uri,
            "name": uri[1:],
            "created_at": int(time.time())}

    k = requests.put('http://' + KONG_HOST + ':8001/apis/', data=api)

    if k.status_code == 201 or k.status_code == 200:
        log.info("Successfully added %s to gateway", uri)
        notifier(True, uri)
    else:
        log.error("Could not add api to gateway: %s", str(k.json()))
        notifier(False, uri)


def notifier(is_successful, uri):
    '''
    Send a notification to hipchat

    :param is_successful: (Boolean) - True if api was added successfully, false otherwise
    :param uri: (String) - Request path to the api that was/wasn't added
    '''
    gateway_link = "https://" + KONG_HOST + ":8243" + uri
    if is_successful:
        message = '{{"color":"green","message":"{API} KongedUP (successful), {link}","notify":true,"message_format":"text"}}'.format(API=uri, link=gateway_link)
    else:
        message = '{{"color":"red","message":"{API} not KongedUP (failed)","notify":true,"message_format":"text"}}'.format(API=uri)
    requests.post(HIPCHAT_URL, data=message, headers={"Content-Type": "application/json"})


def get_port_from_ip_table(pvt_c_id):
    '''
    Return exposed port by looking it up on IP tables
    '''
    
    cmd = 'iptables -t nat -L -n | grep "{pvt_c_id}"'
    cmd = cmd.format(pvt_c_id=pvt_c_id)
    iptables = os.popen(cmd).read()
    iptable_rows = iptables.split('\n')
    DNAT = list(filter(lambda x: x.startswith('DNAT'), iptable_rows))[0].split()
    dpt = list(filter(lambda x: x.startswith('dpt'), DNAT))[0]
    port = dpt.split(':')[-1]
    return port

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
            time.sleep(5)
            try:
                event_handler(event)
            except Exception as e:
                notifier(False, str(e))
                continue

def get_uri(container):
    '''
    Return the value associated with the label 
    GATEWAY_REQUEST_PATH
    '''
    return container['Config']['Labels'].get('GATEWAY_REQUEST_PATH')

def add_container_to_kong(container):
    host = get_rancher_DNS_name(container)
    port = get_open_port(host)
    uri  = get_uri(container)

    if port:
        upstream_url = "http://" + host + ":" + str(port)
        api = get_api(uri)
        if api:
            api['upstream_url'] = upstream_url
        else:
            api = {
            "upstream_url": upstream_url,
            "uris": uri,
            "name": uri[1:],
            "created_at": int(time.time())}
            
        k = requests.put('http://' + KONG_HOST + ':8001/apis/', data=api)

        if k.status_code == 201 or k.status_code == 200:
            log.info("Successfully added %s to gateway", uri)
            notifier(True, uri)
        else:
            log.error("Could not add api to gateway: %s", str(k.json()))
            notifier(False, uri)

def event_handler(event):
    '''
    Inspect the container, and wire it up to the gateway if GATEWAY_VISIBLE is set to "True"
    '''
    cli = Client(version='auto')
    container = cli.inspect_container(event['id'])
    gateway_visible = container['Config']['Labels'].get('GATEWAY_VISIBLE') == "True"
    request_path = container['Config']['Labels'].get('GATEWAY_REQUEST_PATH')
    environment = container['Config']['Labels'].get('ENVIRONMENT')
      
    if environment == KONG_ENVIRONMENT and all([gateway_visible, request_path, container]):
        add_container_to_kong(container)


if __name__ == '__main__':
    log.info("KongUp started")
    listener()



