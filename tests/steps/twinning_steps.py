from behave import given, when, then
import subprocess
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import twin_sd


@given('I have a clean environment with Eclipse Ditto set up')
def setup_clean_environment(context):
    pass


@when('I initiate the twinning process for {iterations} iterations')
def initiate_twinning_process(context, iterations):
    for i in range(int(iterations)):
        os.chdir("/home/ditto/project2/Automate-Twin-Process")
        device_id = "iwatch"
        definition = "https://raw.githubusercontent.com/bernar0507/Eclipse-Ditto-MQTT-iWatch/main/iwatch/wot/iwatch.tm.jsonld"
        
        start_time = time.time()
        twin_sd.start_ditto()
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "Ditto start", end_time - start_time)
        
        start_time = time.time()
        twin_sd.start_mosquitto()
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "Mosquitto start", end_time - start_time)
        
        start_time = time.time()
        twin_sd.run_sd(device_id)
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "start container smart device", end_time - start_time)
        
        start_time = time.time()
        twin_sd.twinning_process(device_id, definition)
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "Create DT", end_time - start_time)
        
        start_time = time.time()
        twin_sd.check_dt_status(device_id)
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "Check DT latest status", end_time - start_time)
        
        start_time = time.time()
        twin_sd.send_iwatch_data(device_id)
        end_time = time.time()
        twin_sd.write_to_csv('/home/ditto/project2/Automate-Twin-Process/timing_data.csv', "Start sending data to DT", end_time - start_time)
        
        # Clear the environment for the next run
        subprocess.run(["docker", "rm", "-f", "mosquitto"], stdout=subprocess.PIPE, check=True)
        subprocess.run(["docker", "rm", "-f", "iwatch-container"], stdout=subprocess.PIPE, check=True)
        os.chdir("/home/ditto/project2/ditto/deployment/docker/")
        subprocess.run(["docker-compose", "down"], stdout=subprocess.PIPE, check=True)


@then('I should have a CSV file with the time data of {iterations} iterations')
def verify_csv_file(context, iterations):
    pass
