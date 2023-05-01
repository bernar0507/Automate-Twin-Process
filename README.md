# Automate-Twin-Process
Automation of the twinning process in Eclipse Ditto

# Requirements

1. Clone Ditto: ```git clone https://github.com/eclipse-ditto/ditto.git```

2. Pull Mosquitto: ```docker pull eclipse-mosquitto```

3. Clone Eclipse-Ditto-MQTT-iWatch: ```git clone https://github.com/bernar0507/Eclipse-Ditto-MQTT-iWatch.git```

4. Clone Automate-Twin-Process: ```git clone https://github.com/bernar0507/Automate-Twin-Process.git```

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

`cd Eclipse-Ditto-MQTT-iWatch/iwatch/dockerfile`

`docker build --no-cache  -t iwatch_image -f Dockerfile.iwatch .`

`docker run -it --name iwatch-container --network docker_default iwatch_image`

# Check the Twin

```curl -u ditto:ditto -X GET 'http://localhost:8080/api/2/things/org.Iotp2c:iwatch'```
