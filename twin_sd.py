import os
import time
import subprocess
import json
from getpass import getpass
import requests


def wait_for_ditto(retries=20, delay=5):
    """Wait for Ditto API to start"""
    api_url = "http://localhost:8080/api/2/things"
    auth = ("ditto", "ditto")
    for _ in range(retries):
        try:
            response = requests.get(api_url, auth=auth)
            if response.status_code == 200:
                print("Ditto API is ready.")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"Waiting for Ditto API... (retrying in {delay} seconds)")
        time.sleep(delay)
    print("Ditto API is still not ready after all retries. Exiting.")
    return False


def start_ditto():
    """Start Ditto"""
    os.chdir("..")
    os.chdir("ditto/deployment/docker")
    print("Starting Ditto")
    subprocess.run(
        ["docker-compose", "up", "-d"]
        , stdout=subprocess.DEVNULL
        , stderr=subprocess.DEVNULL
    )
    print("Ditto started")
    os.chdir("../../..")


def start_mosquitto():
    """Start Mosquitto"""
    os.chdir("Eclipse-Ditto-MQTT-iWatch")
    subprocess.run(
        ["docker", "stop", "mosquitto"]
        , stdout=subprocess.DEVNULL
        , stderr=subprocess.DEVNULL
    )
    subprocess.run(
        ["docker", "rm", "mosquitto"]
        , stdout=subprocess.DEVNULL
        , stderr=subprocess.DEVNULL
    )
    print("Starting Mosquitto")
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            "mosquitto",
            "--network",
            "docker_default",
            "-p",
            "1883:1883",
            "-v",
            f"{os.getcwd()}/mosquitto:/mosquitto/",
            "eclipse-mosquitto",
        ]
    , stdout=subprocess.DEVNULL
    , stderr=subprocess.DEVNULL
    )
    print("Mosquitto started")
    os.chdir("..")


def create_policy():
    """Create Policy"""
    headers = {"Content-Type": "application/json"}
    auth = ("ditto", "ditto")
    data = {
        "entries": {
            "owner": {
                "subjects": {"nginx:ditto": {"type": "nginx basic auth user"}},
                "resources": {
                    "thing:/": {"grant": ["READ", "WRITE"], "revoke": []},
                    "policy:/": {"grant": ["READ", "WRITE"], "revoke": []},
                    "message:/": {"grant": ["READ", "WRITE"], "revoke": []},
                },
            }
        }
    }
    response = requests.put(
        "http://localhost:8080/api/2/policies/org.Iotp2c:policy"
        , auth=auth
        , headers=headers
        , json=data,
    )
    if response.status_code == 201 or response.status_code == 200:
        print("DT policy created with sucess")


def twin_device(device_id, definition):
    """ Create the DT"""
    auth = ("ditto", "ditto")
    headers = {"Content-Type": "application/json"}
    data = {
        "policyId": "org.Iotp2c:policy",
        "definition": definition,
    }
    response = requests.put(
        f"http://localhost:8080/api/2/things/org.Iotp2c:{device_id}"
        , auth=auth
        , headers=headers
        , json=data,
    )
    if response.status_code == 201 or response.status_code == 200:
        print("DT created with sucess")


def untwin_device(device_id):
    """Untwin a device"""
    auth = ("ditto", "ditto")
    response = requests.delete(
        f"http://localhost:8080/api/2/things/org.Iotp2c:{device_id}"
        , auth=auth
    )
    # Delete thing if exists
    if response.status_code == 200:
        response = requests.delete(
            f"http://localhost:8080/api/2/things/org.Iotp2c:{device_id}"
            , auth=auth
        )
        print("Device Untwinned")


def create_connection(device_id):
    """Create the connection"""
    # Create the connection to the device
    headers = {"Content-Type": "application/json"}
    mosquitto_ip = ""
    while not mosquitto_ip:
        try:
            mosquitto_ip = subprocess.check_output(
                [
                    "docker",
                    "inspect",
                    "-f",
                    "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                    "mosquitto",
                ]
            ).decode("utf-8").strip()
        except subprocess.CalledProcessError:
            print("Waiting for Mosquitto container to start...")
            time.sleep(5)
    # Create connection
    data = {
        "targetActorSelection": "/system/sharding/connection",
        "headers": {"aggregate": False},
        "piggybackCommand": {
            "type": "connectivity.commands:createConnection",
            "connection": {
                "id": f"mqtt-connection-{device_id}",
                "connectionType": "mqtt",
                "connectionStatus": "open",
                "failoverEnabled": True,
                "uri": f"tcp://ditto:ditto@{mosquitto_ip}:1883",
                "sources": [
                    {
                        "addresses": [f"org.Iotp2c:{device_id}/things/twin/commands/modify"],
                        "authorizationContext": ["nginx:ditto"],
                        "qos": 0,
                        "filters": []
                    }
                ],
                "targets": [
                    {
                        "address": f"org.Iotp2c:{device_id}/things/twin/events/modified",
                        "topics": [
                            "_/_/things/twin/events",
                            "_/_/things/live/messages"
                        ],
                        "authorizationContext": ["nginx:ditto"],
                        "qos": 0
                    }
                ]
            }
        }
    }
    response = requests.post(
        "http://localhost:8080/devops/piggyback/connectivity?timeout=10",
        auth=("devops", "foobar"),
        headers=headers,
        json=data,
    )
    if response.status_code == 200:
        print("Connection created with sucess")


def delete_connection(device_id):
    """Delete the connection"""
    headers = {"Content-Type": "application/json"}
    data = {
        "targetActorSelection": "/system/sharding/connection",
        "headers": {"aggregate": False},
        "piggybackCommand": {
            "type": "connectivity.commands:deleteConnection",
            "connectionId": f"mqtt-connection-{device_id}",
        },
    }
    response = requests.post(
        "http://localhost:8080/devops/piggyback/connectivity?timeout=10",
        auth=("devops", "foobar"),
        headers=headers,
        json=data,
    )
    if response.status_code == 200:
        print("Connection deleted with sucess")


def check_dt_status(device_id):
    """Check latest state of the DT"""
    url = f"http://localhost:8080/api/2/things/org.Iotp2c:{device_id}"
    auth = ("ditto", "ditto")
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        return print(response.json())
    else:
        print(f"Error: {response.status_code}")
        return None


def twinning_process():
    """Twin device, policy and connection"""
    if not wait_for_ditto():
        return
    device_id = input("Please enter your Device ID: ")
    definition = input("Please enter your Device Definition: ")
    url = f"http://localhost:8080/api/2/things/org.Iotp2c:{device_id}"
    auth = ("ditto", "ditto")
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        return print("DT already created")
    else:
        create_policy()
        twin_device(device_id, definition)
        create_connection(device_id)
    

if __name__ == "__main__":
    start_ditto()
    start_mosquitto()
    twinning_process()
    check_dt_status("iwatch")