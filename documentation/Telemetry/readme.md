## Prerequisites
- Nautobot Setup and Onboarding
# Telemetry VM Creation
## Steps
1.	On google cloud, go to Compute Engine > VM instances > Create Instance.
2. Use the following choices for your VM instance
    1. Name and Region 
        1. Name: ntca-capstone-2024-telemetry
        2. Region: us-central1(Iowa)
        3. Zone: us-central1-a 
    2. Machine Configuration 
        1. General Purpose e2 Instance
        2. Machine type:  Preset: e2-medium
        3. Availability policies: Standard 
    3. Boot disk. Click Change to configure.
        1. OS: Ubuntu 
        2. Version: 20.04 LTS (x86) 
        3. Size: 20 GB 
    4. Firewall 
        1. Allow HTTP traffic 
        2. Allow HTTPS traffic 
    5. Advanced Options 
        1. Networking 
            1. Network tags: telemetry-server
            2. Ip forwarding: Enable 
    6. Create
3. Once the instance is created, go to VM Instances, select the SSH button on the created Telemetry server to confirm connectivity.
4. Run the below command
    1.     sudo apt update && sudo apt upgrade -y
5. Ping the address of one of the switches in the container lab environment. If this fails, ensure container lab is running, and the route to the container switches has been created. Once this succeeds, your instance creation has been completed.
6. Set up firewall rules to allow ports 9090 and 3000 inward for the server.
    1. In the Google Cloud Pinned Products, select VPC Network > Firewall 
    2. Click Create Firewall Rule
    3. Rule
        1. Direction: Ingress
        2. Action: Allow
        3. Targets: All instances
            1. You could also specify tags for specific servers, for simplicity we use all instances
        4. Source IPv4 ranges: 0.0.0.0/0
        5. Protocols: Specified
            1. TCP
                1. Ports: 9090, 3000
# Prometheus Installation

## Steps
1. Enter the below commands to install Prometheus in the /home directory.
    1.     cd /home
    2.     sudo wget https://github.com/prometheus/prometheus/releases/download/v2.50.1/prometheus-2.50.1.linux-amd64.tar.gz
    3.     sudo tar xvfs prometheus-2.50.1.linux-amd64.tar.gz
2. Enter the created Prometheus directory, check the contents, and open the Prometheus configuration file with the below commands.
    1. cd prometheus-2.50.1.linux-amd64
    2. ls
    3. sudo nano prometheus.yml
3. Modify the configuration file according to the below. This will make the Prometheus server grab information every 10 seconds, and direct the server to grab its targets from a file we specify. DO NOT USE TABS, use multiple spaces to align the text.
    1. Scrape interval: 10s
    2. Scrape_configs:
        1. Replace “static_configs:” with file_sd_configs:
        2. Below file_sd_configs:
            1. – files:
            2. – ‘/home/NautoPromo/NautobotTargets.yml’
    3. It should end up looking like the below
```
# my global config
global:
  scrape_interval: 10s # Set the scrape interval to every 15 seconds. Default is every 1 minute.
  evaluation_interval: 15s # Evaluate rules every 15 seconds. The default is every 1 minute.
  # scrape_timeout is set to the global default (10s).

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

# Load rules once and periodically evaluate them according to the global 'evaluation_interval'.
rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: "prometheus"

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'
    file_sd_configs:
    - files:
      - '/home/NautoPromo/NautobotTargets.yml'
```

4. We will be creating a service file so that we can enable the server to run on startup.
    1. Create a service file with the below command
        1.     sudo nano /etc/systemd/system/prometheus.service
    2. Add the below text to the file. This establishes it as a service that executes Prometheus.
```
[Unit]
Description=prometheus service file
After=network.target

[Service]
Type=simple
ExecStart=/home/prometheus-2.50.1.linux-amd64/prometheus --config.file=/home/prometheus-2.50.1.linux-amd64/prometheus.yml

[Install]
WantedBy=multi-user.target
```

5. Run the following commands to make the service file run on startup.
    1.     sudo systemctl daemon-reload
    2.     sudo systemctl enable prometheus
    3.     sudo systemctl start prometheus
6. Go to the public IP of your prometheus server on port 9090 to confirm its startup.
    1. Remember: No data will be transmitted to prometheus until we have obtained our targets with the next section, and installed ocprometheus on the target switches in another section.
# Nautobot Integration with Prometheus Through Custom Service Script

## Steps
1. On the telemetry VM, install the dependencies for the service with the below commands.
    1.     sudo apt install python3-pip -y
    2.     sudo pip install pynautobot
2. Exit to the home directory, and create the directory and file specified in the prometheus.yml file. This file will be managed by a custom service we will create to grab device targets from our nautobot server.
    1.     cd ..
    2.     sudo mkdir NautoPromo
    3.     cd NautoPromo
    4.     sudo nano NautobotTargets.yml
3. Enter an example target to the file such as “- targets [172.100.100.101:8080]”. This will be changed by the service later, but this is to show the formatting file_sd_configs uses.
4. Make a python file called NautoPromo.py under /home/NautoPromo using “sudo nano NautoPromo.py”and copy the below script to it.
    1. Use the IP address of Nautobot as the URL and get the API target key from Nautobot under Admin > API Tokens.
    2. Essentially, what this script does is query nautobot for targets using GraphQL, and then writing them to the target file we created earlier.
```
#### Imports ####
import pynautobot
import json
 
#### Query to Nautobot for list of Management0 addresses ####
query = """
query {
  devices {
    name
    interfaces {
      name
      ip_addresses {
        address
      }
    }
  }
}
"""
 
#### Nautobot API Connection stuff. verify=False for self signed certs ###
nb = pynautobot.api(
    url = "https://IP_ADDRESS",
    token = "API_NAUTOBOT_TOKEN",
    verify = False
)
print("Querying")
#### GraphQL Query to Nautobot, turn to json ####
gql = nb.graphql.query(query=query)
gqljson = (json.dumps(gql.json, indent=2))
data = json.loads(gqljson)
#### Parsing through each line in json for management0 address ####
 
## Create empty array to be filled with target addresses ##
arrayOfTargets = []
 
## iterate through the json data with the keys and values to obtain ip addresses
for device in data['data']['devices']:
  for interface in device['interfaces']:
    if interface['name'] == 'Management0':
      for ip_address in interface['ip_addresses']:
         address = ip_address['address']
         address = address[:address.find("/")]
         arrayOfTargets.append(address+":8080")
  
#### Create a string that has the one line of yaml that the file_sd_config target file needs. basically, "- targets:" and then a string array of the targets+port ####
prometheusTargets = "- targets: ["
for target in arrayOfTargets:
  prometheusTargets = prometheusTargets + "'" + target + "', "
prometheusTargets = prometheusTargets[:-2]
prometheusTargets = prometheusTargets + "]"
print(f"Targets found:\n{prometheusTargets}")
 
#### Read target file on machine, if it has not changed, do not write over it, if it has, write over it ####
writeOver = False
with open("/home/NautoPromo/NautobotTargets.yml", "r") as targetFile:
  for line in targetFile:
    if line != prometheusTargets:
      writeOver = True
if writeOver:
  with open("/home/NautoPromo/NautobotTargets.yml", "w") as file:
    file.write(prometheusTargets)
else:
  print("no differences found since last query, no changes made to target file")
```

5. Ensure you give the text files the permissions to be read, written, and executed such as with the below commands.
    1.     sudo chmod 777 NautobotTargets.yml
    2.     sudo chmod 777 NautoPromo.py
6. Create a service file called NautoPromo.service with the below command
    1.     sudo nano /etc/systemd/system/NautoPromo.service
    2. Add the below text to the file. This establishes it as a service that executes the script when called.
```
[Unit]
Description=Script that queries nautobot for Prometheus file_sd targets
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/NautoPromo/NautoPromo.py

[Install]
WantedBy=multi-user.target 
```

7. Now, make a service timer in the same location using the below command
    1.     sudo nano /etc/systemd/system/NautoPromo.timer
    2. Use the below text to establish a timer that will run the NautoPromo service every 5 minutes.
```
[Unit]
Description=Run NautoPromo every 5 minutes

[Timer]
OnUnitActiveSec=5m
Unit=NautoPromo.service

[Install]
WantedBy=timers.target
```

8. Run the below commands to allow the machine to see the changes in services and enable the timer to run on startup.
    1.     sudo systemctl daemon-reload
    2.     sudo systemctl enable NautoPromo.timer
    3.     sudo systemctl start NautoPromo.timer
    4.     sudo systemctl enable NautoPromo
    5.     sudo systemctl start NautoPromo
9. Check the NautobotTargets.yml file and view the changes.
    1. You can also view the logs of the script running with the below command
        1.     journalctl -u NautoPromo 
    2. You can see the next time this will run usin the below command
        1.     systemctl status NautoPromo.timer
10.	As a reminder, Prometheus won’t be able to scrape its targets until the exporters are running on the target switches.
# Grafana Installation

## Steps
