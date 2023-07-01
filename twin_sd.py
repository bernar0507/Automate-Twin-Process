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
        start_time = time.time()
        subprocess.run(
            ["docker-compose", "up", "-d"]
            , stdout=subprocess.DEVNULL
            , stderr=subprocess.DEVNULL
        )
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Ditto started in {time_taken} seconds")
    else:
        print("Ditto already running")
    os.chdir("../../..")


def start_mosquitto():
    """Start Mosquitto"""
    os.chdir("Eclipse-Ditto-MQTT-iWatch-SSL")
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
        subprocess.run(
            ["docker", "rm", "mosquitto"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("Starting Mosquitto")
        start_time = time.time()
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
        end_time = time.time()
        time_taken = end_time - start_time
        print(f"Mosquitto started in {time_taken} seconds")

        # Get container logs
        print("Getting Mosquitto container logs...")
        logs = subprocess.run(["docker", "logs", "mosquitto"], stdout=subprocess.PIPE, text=True)
        print(logs.stdout)
    else:
        print("Mosquitto already running")
    os.chdir("..")
    

def create_ssl_certificates_ca_broker():
    """Create the certificates for the CA and Broker/server"""
    print("Creating SSL Certificates")

    # Define variables
    env = {
        "COUNTRY": "PT",
        "STATE": "MAFRA",
        "CITY": "LISBON",
        "ORGANIZATION": "My Company",
        "ORG_UNIT": "IT Department",
    }

    # Define common name for first certificate
    common_name = "CA"
    
    running = subprocess.run(
        ["docker", "ps", "-q", "--filter", "name=mosquitto"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    # Define commands
    commands = [
        "docker exec mosquitto sh -c '"
        "cd /mosquitto/config && "
        "apk add openssl && "
        f'openssl req -new -x509 -days 3650 -extensions v3_ca -keyout ca.key -out ca.crt -nodes -subj "/C={env["COUNTRY"]}/ST={env["STATE"]}/L={env["CITY"]}/O={env["ORGANIZATION"]}/OU={env["ORG_UNIT"]}/CN={common_name}" && '
        "sh generate_openssl_config.sh && "
        f'openssl req -new -out server.csr -keyout server.key -nodes -subj "/C={env["COUNTRY"]}/ST={env["STATE"]}/L={env["CITY"]}/O={env["ORGANIZATION"]}/OU={env["ORG_UNIT"]}/CN=MQTT Broker" -config openssl.cnf && '
        "openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -extensions v3_req -extfile openssl.cnf"
        "'"
    ]

    # Record total time
    start_time = time.time()
    for cmd in commands:
        subprocess.run(cmd, shell=True, check=True)

    # Restart the mosquitto container
    subprocess.run("docker restart mosquitto", shell=True, check=True)

    end_time = time.time()
    print(f"SSL Certificates created and Mosquitto restarted in {end_time - start_time} seconds in total")


def exec_and_get_output(container_name, command):
    """Cat a file in a container"""
    result = subprocess.run(
        ["docker", "exec", "-i", container_name, "cat", command], 
        stdout=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode()


def format_strings_for_connection(string, start_marker, end_marker):
    string = string.replace(start_marker, "").replace(end_marker, "").replace("\n", " ").strip()
    return string
    

def sign_certificate():
    """Sign certificate of the client"""
    start_time = time.time()
    # define commands to get CA cert, CA key, client cert, and client key
    ca_cert_cmd = "/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/ca.crt"
    client_key_cmd = "/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/client.key"
    client_crt_cmd = "/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/client.crt"
    
    # create and sign the client certificate
    openssl_command = "openssl x509 -req -in '/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/client.csr' -CA '/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/ca.crt' -CAkey '/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/ca.key' -CAcreateserial -out '/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/client.crt' -days 3650 -extensions v3_req -extfile '/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/mosquitto/config/openssl.cnf'"
    process = subprocess.run(["docker", "exec", "-i", "iwatch-container", "/bin/sh", "-c", openssl_command], stdout=subprocess.PIPE,check=True,)
    result = process.stdout.decode()

    # trim the keys and certificate
    CA_CERT = format_strings_for_connection(exec_and_get_output("iwatch-container", ca_cert_cmd), "-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----")
    CLIENT_CERT = format_strings_for_connection(exec_and_get_output("iwatch-container", client_crt_cmd), "-----BEGIN CERTIFICATE-----", "-----END CERTIFICATE-----")
    CLIENT_KEY = format_strings_for_connection(exec_and_get_output("iwatch-container", client_key_cmd), "-----BEGIN PRIVATE KEY-----", "-----END PRIVATE KEY-----")
    end_time = time.time()
    print(f"Signing certificate process took {end_time - start_time} seconds")
    
    return CA_CERT, CLIENT_CERT, CLIENT_KEY


def create_policy():
    """Create Policy"""
    start_time = time.time()
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
        end_time = time.time()
        print(f"DT policy created with sucess and took {end_time - start_time} seconds")


def twin_device(device_id, definition):
    """ Create the DT"""
    start_time = time.time()
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
        end_time = time.time()
        print(f"DT created with sucess and took {end_time - start_time} seconds")


def untwin_device(device_id):
    """Untwin a device"""
    start_time = time.time()
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
        end_time = time.time()
        print(f"Device Untwinned and took {end_time - start_time} seconds")


def create_connection(device_id):
    """Create the connection"""
    start_time = time.time()
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
    CA_CERT, CLIENT_CERT, CLIENT_KEY = sign_certificate()
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
                        "//things/twin/events",
                        "//things/live/messages"
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
        end_time = time.time()
        print(f"Connection created with sucess and took {end_time - start_time} seconds")


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
        print(f"Connection deleted with sucess and took {end_time - start_time} seconds")


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


def send_iwatch_data():
    container_name = "iwatch-container"  # Replace with your container name
    script_path = "/app/Eclipse-Ditto-MQTT-iwatch-SSL-OOP/iwatch/send_data_iwatch.py"
    
    # Enter the Docker container
    enter_container_cmd = ["docker", "exec", "-d", container_name, "/bin/sh", "-c", f"python3 {script_path}"]
    subprocess.run(enter_container_cmd, stdout=subprocess.PIPE, check=True)
    

def twinning_process():
    """Twin device, policy and connection"""
    start_time = time.time()
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
        end_time = time.time()
        print(f"Twinning process took {end_time - start_time} seconds")


if __name__ == "__main__":
    start_ditto()
    start_mosquitto()
    create_ssl_certificates_ca_broker()
    twinning_process()
    check_dt_status("iwatch")
    send_iwatch_data()
