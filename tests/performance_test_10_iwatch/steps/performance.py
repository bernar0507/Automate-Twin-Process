from behave import given, when, then
import subprocess
import time
import sys
import os
import csv
import psutil
import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import twin_sd


def measure_performance(test_name, duration, interval, device_id, csv_filename):
    start_time = time.time()
    end_time = start_time + duration * 60  # convert duration from minutes to seconds

    with open(csv_filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write the header row
        writer.writerow(['Test Name', 'Timestamp', 'Time', 'CPU Usage (%)', 'RAM Usage (MB)', 'Network Usage (Bytes)', 'Response Time (s)'])

        while time.time() < end_time:
            # Get CPU usage
            cpu_usage = psutil.cpu_percent()

            # Get RAM usage
            ram_usage = psutil.virtual_memory().used / (1024 ** 2)  # convert from bytes to MB

            # Get network usage
            network_usage = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv

            # Get response time
            response_start_time = time.time()
            # Call check_dt_status instead of requests.get
            response = twin_sd.check_dt_status(device_id)
            response_end_time = time.time()
            response_time = response_end_time - response_start_time

            # Get the current time
            current_time = time.time() - start_time

            # Get the current timestamp
            current_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Write the data row
            writer.writerow([test_name, current_timestamp, current_time, cpu_usage, ram_usage, network_usage, response_time])

            # Wait for the specified interval before the next measurement
            time.sleep(interval * 60)  # convert interval from minutes to seconds


def docker_cleanup(container_names):
    for container_name in container_names:
        # stop and remove the container if it exists
        subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.PIPE, check=True)


@given('I have a clean environment')
def step_clean_environment(context):
    pass


@when('I start the twinning process for {num_watches} iWatch')
def step_start_twinning(context, num_watches):
    # Start the twinning process. Implementation will depend on your project's requirements.
    os.chdir("/home/ditto/project2/Automate-Twin-Process")
    context.num_watches = int(num_watches)
    definition = "https://raw.githubusercontent.com/bernar0507/Eclipse-Ditto-MQTT-iWatch/main/iwatch/wot/iwatch.tm.jsonld"
    twin_sd.start_ditto()
    twin_sd.start_mosquitto()

    # Loop over the number of iWatches
    for i in range(int(num_watches)):
        # Assign unique device id to each iWatch
        device_id = f"iwatch{i+1}"
        twin_sd.run_sd(device_id)
        twin_sd.twinning_process(device_id, definition)
        twin_sd.check_dt_status(device_id)
        twin_sd.send_iwatch_data(device_id)


@then('I measure and record the performance for {num_minutes} minutes')
def step_measure_performance(context, num_minutes):
    # Measure performance and write results to a CSV file. Implementation will depend on your project's requirements.
    # context.current_scenario is a Behave method that returns the name of the current scenario.
    # If you want to use the feature name instead of the scenario name, you can use context.feature.name
    test_name = context.current_scenario.name
    duration = int(num_minutes)
    interval = 1  # interval -> 1 minute
    device_id = "iwatch1"
    csv_filename = "/home/ditto/project2/Automate-Twin-Process/performance.csv"
    context.performance_data = measure_performance(test_name, duration, interval, device_id, csv_filename)

    # Define your cleanup process
    num_watches = int(context.num_watches)
    iwatch_containers_to_cleanup = [f"iwatch-container{i+1}" for i in range(num_watches)]
    docker_cleanup(iwatch_containers_to_cleanup)

    # Cleanup Ditto and Mosquitto containers
    other_containers_to_cleanup = ["ditto", "mosquitto"]
    docker_cleanup(other_containers_to_cleanup)
