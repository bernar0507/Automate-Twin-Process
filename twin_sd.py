import os
import time
import subprocess
import json
from getpass import getpass
import requests
import datetime
import csv
import re


def write_to_csv(file_name, time_taken, event_name):
    """Write time taken to csv file"""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    
    # Construct the full path to the CSV file
    full_path = os.path.join(script_dir, 'Automate-Twin-Process', file_name)

    with open(full_path, 'a', newline='') as file:
        writer = csv.writer(file)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, event_name, time_taken])
        

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
    os.chdir("ditto/")
    subprocess.run(["git", "checkout", "tags/3.0.0"]
        , stdout=subprocess.PIPE
        , stderr=subprocess.DEVNULL
    )
    os.chdir("deployment/docker")
    print("Starting Ditto")
    running = subprocess.run(
        ["docker-compose", "ps", "-q", "ditto"]
        , stdout=subprocess.PIPE
        , stderr=subprocess.DEVNULL
    )
    if not running.stdout:
        subprocess.run(
            ["docker-compose", "up", "-d"]
            , stdout=subprocess.DEVNULL
            , stderr=subprocess.DEVNULL
        )
    else:
        print("Ditto already running")
    os.chdir("../../..")


def is_container_running(container_name):
    """Check if a specific docker container is running."""
    running = subprocess.run(
        ["docker", "ps", "-q", "--filter", f"name={container_name}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    return running.stdout != b''


def wait_for_container(container_name, timeout=120):
    """Wait for a docker container to start."""
    for _ in range(timeout):
        if is_container_running(container_name):
            return
        time.sleep(1)
    raise TimeoutError(f"Container {container_name} did not start within {timeout} seconds.")


def create_ssl_certificates_broker():
    """Create the certificates for Broker/server"""
    print("Creating SSL Certificates")

    # Define variables
    env = {
        "COUNTRY": "PT",
        "STATE": "MAFRA",
        "CITY": "LISBON",
        "ORGANIZATION": "My Company",
        "ORG_UNIT": "IT Department",
    }
    
    wait_for_container('mosquitto')

    # Define commands
    commands = [
        "docker exec mosquitto sh -c '"
        "cd /mosquitto/config && "
        "apk add openssl && "
        "sh generate_openssl_config.sh && "
        f'openssl req -new -out server.csr -keyout server.key -nodes -subj "/C={env["COUNTRY"]}/ST={env["STATE"]}/L={env["CITY"]}/O={env["ORGANIZATION"]}/OU={env["ORG_UNIT"]}/CN=MQTT Broker" -config openssl.cnf && '
        "openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -extensions v3_req -extfile openssl.cnf"
        "'"
    ]
    
    # Execute commands
    for cmd in commands:
        subprocess.run(cmd, shell=True, check=True)
        
    # Now restart the container with the SSL configuration
        subprocess.run(
            ["docker", "stop", "mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        subprocess.run(
            ["docker", "rm", "mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
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
                "8883:8883",
                "-v",
                f"{os.getcwd()}/mosquitto:/mosquitto/",
                "eclipse-mosquitto",
                "mosquitto",
                "-c",
                "/mosquitto/config/mosquitto_ssl.conf", 
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    
def start_mosquitto():
    """Start Mosquitto"""
    os.chdir("Eclipse-Ditto-MQTT-iwatch-SSL-TCP")
    running = subprocess.run(
        ["docker", "ps", "-q", "--filter", "name=mosquitto"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )
    if not running.stdout:
        subprocess.run(
            ["docker", "stop", "mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
        subprocess.run(
            ["docker", "rm", "mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(5)
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
                "8883:8883",
                "-v",
                f"{os.getcwd()}/mosquitto:/mosquitto/",
                "eclipse-mosquitto",
                "mosquitto",
                "-c",
                "/mosquitto/config/mosquitto.conf", 
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        create_ssl_certificates_broker()  

        # Get container logs
        print("Getting Mosquitto container logs...")
        logs = subprocess.run(["docker", "logs", "mosquitto"], stdout=subprocess.PIPE, text=True)
        print(logs.stdout)
    else:
        print("Mosquitto already running")
    os.chdir("..")


def run_sd(device_id):
    """Start the smart device container."""
    print(f"Starting {device_id} container...")
    base_device_name = re.split('\d', device_id)[0]

    cmd = [
        "docker", 
        "run", 
        "-it", 
        "-d", 
        "--name", 
        f"{device_id}-container", 
        "-v", 
        "/home/ditto/project2/Eclipse-Ditto-MQTT-iwatch-SSL-TCP/mosquitto/:/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/",
        "--network", 
        "docker_default", 
        f"{base_device_name}_image"
    ]
    
    

    try:
        subprocess.run(cmd, check=True)
        print("Container started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start container: {e}")
    

def exec_and_get_output(container_name, command):
    """Get content of the file in a container"""
    result = subprocess.run(
        ["docker", "exec", "-i", container_name, "cat", command], 
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode()


def format_strings_for_connection(string, start_marker, end_marker):
    string = string.replace(start_marker, "").replace(end_marker, "").replace("\n", " ").strip()
    return string
 
 
def get_container_id(container_name):
    """Get the id of a Docker container by its name"""
    process = subprocess.run(["docker", "ps", "-qf", f"name={container_name}"], stdout=subprocess.PIPE, check=True)
    return process.stdout.decode().strip()   


def sign_certificate(device_id):
    """Sign certificate of the client"""
    
    env = {
        "COUNTRY": "PT",
        "STATE": "MAFRA",
        "CITY": "LISBON",
        "ORGANIZATION": "My Company",
        "ORG_UNIT": "IT Department",
        "COMMON_NAME": f"{device_id} client"
    }
    
    # define commands to get CA cert, CA key, client cert, and client key
    ca_cert_cmd = "/device/mosquitto/config/ca.crt"
    client_key_cmd = "/device/mosquitto/config/client.key"
    client_crt_cmd = "/device/mosquitto/config/client.crt"
    
    # Define commands - create and sign the client certificate
    commands = [
    f"docker exec {device_id}-container /bin/sh -c '"
    "cd .. && "
    "cd /device/mosquitto/config && "
    "sh generate_openssl_config_client.sh && "
    f'openssl req -new -out client.csr -keyout client.key -nodes -subj "/C={env["COUNTRY"]}/ST={env["STATE"]}/L={env["CITY"]}/O={env["ORGANIZATION"]}/OU={env["ORG_UNIT"]}/CN={env["COMMON_NAME"]}" -config openssl.cnf && '
    "openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650 -extensions v3_req -extfile openssl.cnf"
    "'"
    ]
    
    # Execute commands
    for cmd in commands:
        subprocess.run(cmd, shell=True, check=True)

    # trim the keys and certificate
    CA_CERT = format_strings_for_connection(exec_and_get_output(f"{device_id}-container", ca_cert_cmd), "-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----")
    CLIENT_CERT = format_strings_for_connection(exec_and_get_output(f"{device_id}-container", client_crt_cmd), "-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----")
    CLIENT_KEY = format_strings_for_connection(exec_and_get_output(f"{device_id}-container", client_key_cmd), "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----")
    
    return CA_CERT, CLIENT_CERT, CLIENT_KEY


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
        pass


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
        pass
        


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
        delete_connection(device_id)


def create_connection(device_id):
    """Create the connection"""
    # Create the connection to the device
    headers = {"Content-Type": "application/json"}
    mosquitto_ip = ""
    while not mosquitto_ip:
        try:
            mosquitto_ip = subprocess.run(
                [
                    "docker",
                    "inspect",
                    "-f",
                    "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                    "mosquitto",
                ],capture_output=True,
                text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError:
            print("Waiting for Mosquitto container to start...")
            time.sleep(5)
    # Create connection
    CA_CERT, CLIENT_CERT, CLIENT_KEY = sign_certificate(device_id)
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
            "uri": f"ssl://ditto:ditto@{mosquitto_ip}:8883",
            "validateCertificates": True,
            "ca": f"-----BEGIN CERTIFICATE-----\n{CA_CERT}\n-----END CERTIFICATE-----",
            "credentials": {
                "type": "client-cert",
                "cert": f"-----BEGIN CERTIFICATE-----\n{CLIENT_CERT}\n-----END CERTIFICATE-----",
                "key": f"-----BEGIN PRIVATE KEY-----\n{CLIENT_KEY}\n-----END PRIVATE KEY-----"
            },
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
        pass


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
        pass


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


def send_iwatch_data(device_id):
    container_name = f"{device_id}-container"
    script_path = "/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/iwatch/send_data_iwatch.py"
    
    # Enter the Docker container
    enter_container_cmd = ["docker", "exec", "-d", container_name, "/bin/sh", "-c", f"python3 {script_path} '{device_id}'"]
    try:
        subprocess.run(enter_container_cmd, stdout=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Docker command failed with error: {str(e)}")
        

def twinning_process(device_id, definition):
    """Twin device, policy and connection"""
    if not wait_for_ditto():
        return
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
    device_id = input("Please enter your Device ID: ")
    definition = input("Please enter your Device Definition: ")
    start_ditto()
    start_mosquitto()
    run_sd(device_id)
    twinning_process(device_id, definition)
    check_dt_status(device_id)
    send_iwatch_data(device_id)
