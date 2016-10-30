from docker import Client
import socket
import json
import os
import requests

KONG_HOST = os.getenv("KONG_HOST")
HOSTNAME = os.getenv("HOST_NAME")

def add_to_kong(request_path,port):
    upstream_url = "http://" + HOSTNAME + ":" + port
    k = requests.post('http://' + KONG_HOST + ':8001/apis/', data={"upstream_url": upstream_url, "request_path": request_path, "strip_request_path": True})
    if k.status_code == 201:
        print("Successfully added", request_path, "to gateway")
    else:
        print("Could not add api to gateway")

def listener():
    cli = Client()
    for event in cli.events():
        event = json.loads(event.decode('utf-8'))
        if event.get('status') == 'start':
            event_handler(event)


def event_handler(event):
    cli = Client()
    container = cli.inspect_container(event['id'])

    if len(container['NetworkSettings']['Ports']) > 1:
        raise NotImplementedError("Only one port is suppored atm")

    if container['Config']['Labels'].get('GATEWAY_VISIABLE') == "True": 
        port = list(container['NetworkSettings']['Ports'].values())[0][0]['HostPort']
        request_path = container['Config']['Labels']['GATEWAY_REQUEST_PATH']
        add_to_kong(request_path,port)

if __name__ == '__main__':
    listener()
