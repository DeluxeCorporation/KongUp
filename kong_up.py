from docker import Client
import socket
import json
import os
import requests
import uuid
import time
KONGS = {"DEV" : os.getenv("DEV_KONG_HOST"),
         "QA" : os.getenv("QA_KONG_HOST"),
         "UAT": os.getenv("UAT_KONG_HOST"),
         "XUAT":os.getenv("XUAT_KONG_HOST"),
         "PREPROD":os.getenv("PREPROD_KONG_HOST"),
         "PROD":os.getenv("PROD_KONG_HOST")}
HOSTNAME = os.getenv("HOSTNAME")
HIPCHAT_URL = os.getenv("HIPCHAT_URL")


def get_api(uri, environment):
    '''
    Return API if API exists in the environment
    specified, else False. Check only
    the first uri in the api.
    '''
    KONG_HOST = KONGS[environment]
    apis = requests.get('http://' + KONG_HOST + ':8001/apis/').json()['data']
    for api in apis:
        if api['uris'][0] == uri:
            return api
    return False


def add_to_kong(uri, port, environment):
    '''
    Add uri to Kong in environment on port 
    '''
    upstream_url = "http://" + HOSTNAME + ":" + port
    KONG_HOST = KONGS[environment]
    api = get_api(uri, environment)

    if api:
        api['upstream_url'] = upstream_url
    else:
        api = {
            "upstream_url": upstream_url,
            "uris": uri,
            "name": uri[1:],
            "created_at": int(time.time())}

    print("request" + str(api))
    k = requests.put('http://' + KONG_HOST + ':8001/apis/', data=api)

    if k.status_code == 201 or k.status_code == 200:
        print("Successfully added", uri, "to gateway")
        notifier(True, uri, KONG_HOST)
    else:
        print("Could not add api to gateway", k.json())
        notifier(False, uri, KONG_HOST)


def notifier(is_successful, uri, KONG_HOST=''):
    '''
    Send a notification to hipchat

    :param is_successful: (Boolean) - True if api was added successfully, false otherwise
    :param uri: (String) - Request path to the api that was/wasn't added
    :KONG_HOST: (String) - hostname of the server where kong is running
    '''
    gateway_link = "https://" + KONG_HOST + ":8243" + uri
    if is_successful:
        message = '{{"color":"green","message":"{API} KongedUP (successful), {link}","notify":true,"message_format":"text"}}'.format(API=uri, link=gateway_link)
    else:
        message = '{{"color":"red","message":"{API} not KongedUP (failed)","notify":true,"message_format":"text"}}'.format(API=uri)
    requests.post(HIPCHAT_URL, data=message, headers={"Content-Type": "application/json"})


def listener():
    '''
    Listen to docker events, and invoke event_handler if a
    container was started.
    '''
    cli = Client(version='auto')
    for event in cli.events():
        event = json.loads(event.decode('utf-8'))
        if event.get('status') == 'start':
            time.sleep(5)
            try:
                event_handler(event)
            except Exception as e:
                notifier(False, str(e))
                continue

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
    
def event_handler(event):
    '''
    Inspect the container, and wire it up to the gateway if GATEWAY_VISIBLE is set to "True"
    '''
    cli = Client(version='auto')
    container = cli.inspect_container(event['id'])

    if container['Config']['Labels'].get('GATEWAY_VISIBLE') == "True":
        pvt_c_id = container['Config']['Labels'].get('io.rancher.container.ip')[:-3]
        port = get_port_from_ip_table(pvt_c_id)
        request_path = container['Config']['Labels'].get('GATEWAY_REQUEST_PATH')
        environment = container['Config']['Labels'].get('ENVIRONMENT')
        if request_path: 
            add_to_kong(request_path, port, environment)

def rewire():
    cli = Client(version='auto')
    time.sleep(5)
    containers = cli.containers()
    for container in containers:
        try:
            if container['Labels'].get('GATEWAY_VISIBLE') == "True":
                print(container['Names'])
                pvt_c_id = container['Labels'].get('io.rancher.container.ip')[:-3]
                port = get_port_from_ip_table(pvt_c_id)
                request_path = container['Labels'].get('GATEWAY_REQUEST_PATH')
                environment = container['Labels'].get('ENVIRONMENT')
                if request_path: 
                    add_to_kong(request_path, port, environment)
        except Exception as e:
            notifier(False, str(e))
            continue

if __name__ == '__main__':
    print("started")
    rewire()
    listener()
