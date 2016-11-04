from docker import Client
import socket
import json
import os
import requests
import uuid
import time
KONG_HOST = os.getenv("KONG_HOST")
HOSTNAME = os.getenv("HOST_NAME") if os.getenv("HOST_NAME") else socket.gethostname()
HIPCHAT_URL = os.getenv("HIPCHAT_URL")


def get_api(request_path):
    '''
    Retrun API is API exists, else False
    '''
    apis = requests.get('http://' + KONG_HOST + ':8001/apis/').json()['data']
    for api in apis:
        if api['request_path'] == request_path:
            return api
    return False


def add_to_kong(request_path, port):
    upstream_url = "http://" + HOSTNAME + ":" + port

    api = get_api(request_path)

    if api:
        api['upstream_url'] = upstream_url
    else:
        api = {
            "upstream_url": upstream_url,
            "strip_request_path": True,
            "request_path": request_path,
            "created_at": int(time.time())}

    k = requests.put('http://' + KONG_HOST + ':8001/apis/', data=api)

    if k.status_code == 201 or k.status_code == 200:
        print("Successfully added", request_path, "to gateway")
        notifier(True, request_path)
    elif k.status_code == 409:
        print("Could not add api to gateway", k.json())
        notifier(False, request_path)


def notifier(is_successful, request_path):
    gateway_link = "https://" + KONG_HOST + ":8243" + request_path
    if is_successful:
        message = '{{"color":"green","message":"{API} KongedUP (successful), {l}","notify":true,"message_format":"text"}}'.format(API=request_path, l=gateway_link)
    else:
        message = '{{"color":"red","message":"{API} not KongedUP (failed)","notify":true,"message_format":"text"}}'.format(API=request_path)
    m = requests.post(HIPCHAT_URL, data=message, headers={"Content-Type": "application/json"})


def listener():
    cli = Client(version='auto')
    for event in cli.events():
        event = json.loads(event.decode('utf-8'))
        if event.get('status') == 'start':
            event_handler(event)


def event_handler(event):
    cli = Client(version='auto')
    container = cli.inspect_container(event['id'])

    if len(container['NetworkSettings']['Ports']) > 1:
        raise NotImplementedError("Only one port is suppored atm")

    if container['Config']['Labels'].get('GATEWAY_VISIBLE') == "True":
        port = list(container['NetworkSettings']['Ports'].values())[0][0]['HostPort']
        request_path = container['Config']['Labels']['GATEWAY_REQUEST_PATH']
        add_to_kong(request_path, port)

if __name__ == '__main__':
    listener()
