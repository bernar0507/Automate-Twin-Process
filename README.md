# Automate-Twin-Process
Automation of the twinning process in Eclipse Ditto

# Requirements

1. Clone Ditto: ```git clone https://github.com/eclipse-ditto/ditto.git```

2. Pull Mosquitto: ```docker pull eclipse-mosquitto```

3. Clone Eclipse-Ditto-MQTT-iwatch-SSL-TCP: ```git clone https://github.com/bernar0507/Eclipse-Ditto-MQTT-iwatch-SSL-TCP.git```

4. Clone Automate-Twin-Process: ```git clone https://github.com/bernar0507/Automate-Twin-Process.git```

5. Install the requirements: ```sh install_requirements.sh```

6. Build the sd image: ```docker build --no-cache  -t iwatch_image -f Dockerfile.iwatch .```

# How to run it:

`cd Automate-Twin-Process`

`python twin_sd.py`

# Demo 

### Run the script 

`cd Automate-Twin-Process`

`python twin_sd.py`

### Give the parameters:

Please enter your Device ID: `iwatch`

Please enter your Device Definition: `https://raw.githubusercontent.com/bernar0507/Eclipse-Ditto-MQTT-iWatch/main/iwatch/wot/iwatch.tm.jsonld`

### It will create the DT

```
{
   "thingId":"org.Iotp2c:iwatch",
   "policyId":"org.Iotp2c:policy",
   "definition":"https://raw.githubusercontent.com/bernar0507/Eclipse-Ditto-MQTT-iWatch/main/iwatch/wot/iwatch.tm.jsonld",
   "attributes":{
      "heart_rate":60.0,
      "timestamp":"1970-01-01T00:00:00.000Z",
      "longitude":0,
      "latitude":0
   }
}
```

### To simulate sending data from smart device

The sd will start sending data automatically.

# Check the Twin

```curl -u ditto:ditto -X GET 'http://localhost:8080/api/2/things/org.Iotp2c:iwatch'```

# Tests
The test are available in the test folder. 

Here are the test cases written in Gherkins:

## performance_test_10_iwatch
```
Feature: Performance Testing of Eclipse Ditto for 10 iWatch

  Scenario: Twinning and performance testing for ten iWatch
    Given I have a clean environment
    When I start the twinning process for 10 iWatch
    Then I measure and record the performance for 30 minutes
```

## performance_test_1_iwatch
```
Feature: Performance Testing of Eclipse Ditto for 1 iWatch

  Scenario: Twinning and performance testing for one iWatch
    Given I have a clean environment
    When I start the twinning process for 1 iWatch
    Then I measure and record the performance for 30 minutes
```
## twin_test
```
Feature: Twinning Process Performance Testing in Eclipse Ditto

  Scenario: Test twinning process and capture time for 100 iterations
    Given I have a clean environment with Eclipse Ditto set up
    When I initiate the twinning process for 100 iterations
    Then I should have a CSV file with the time data of 100 iterations
```
