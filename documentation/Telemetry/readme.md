## Prerequisites
- Nautobot Setup and Onboarding
# Installations and Initial Setup
## Telemetry VM Creation
### Steps
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
## Prometheus Installation

### Steps
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
## Nautobot Integration with Prometheus Through Custom Service Script

### Steps
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
## Grafana Installation

### Steps
1. On the telemetry VM, install Grafana with the below commands.
    1.     sudo apt-get install -y apt-transport-https software-properties-common wget
    2.     sudo mkdir -p /etc/apt/keyrings/
    3.     wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
    4.     echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
    5.     sudo apt-get update
    6.     sudo apt-get install grafana -y
2. Start and enable the Grafana server on startup with the below commands.
    1.     sudo systemctl daemon-reload
    2.     sudo systemctl enable grafana-server.service
    3.     sudo systemctl start grafana-server
3. Check the status of the server with the below command
    1.     sudo systemctl status grafana-server
## Prometheus Exporter (ocprometheus) Setup

### Steps
1. Clone the ocprometheus repository in the /home directory using the commands.
    1.     cd /home
    2.     sudo git clone https://github.com/aristanetworks/goarista.git
2. Enter the below commands to install GO and compile the ocprometheus code.
    1.     cd /home/goarista/cmd/ocprometheus
    2.     sudo snap install go --classic
    3.     sudo GOOS=linux GOARCH=amd64 go build -buildvcs=false
3. Create a yaml file in that directory called ocprometheus.yml, we will be sending this to the switches.
    1.     sudo nano ocprometheus.yml
    2. Enter the below code to the yaml file. This is based on the 
```
# Subscription paths.
subscriptions:
        - /Kernel/proc/cpu/utilization/
        - /Sysdb/interface/status/eth/phy/slice/1/intfStatus/
        - /Smash/routing/bgp
# Prometheus metrics configuration.
# If you use named capture groups in the path, they will be extracted into labels with the same name.
# All fields are mandatory.

metrics:
        - name: cpuinfo
          path: /Kernel/proc/cpu/utilization/total/(?P<usageType>(?:system|user|idle))
          help: CPU Info
        - name: basestatus
          path: /Sysdb/interface/status/eth/phy/slice/1/intfStatus/(?P<intf>.+)/linkStatus
          help: BaseStatus
          valuelabel: linkStatus
          defaultvalue: 0
        - name: bgppeerstatus
          path: /Smash/routing/bgp/bgpPeerInfoStatus/default/bgpPeerStatusEntry/(?P<peerAddress>.+)/bgpState
          help: BGP Peer status
          valuelabel: bgpState
          defaultvalue: 0
```

You can follow the steps below to set up ocprometheus manually on the switches, or you could copy those files over to our desktop VM and use the ocprometheus ansible playbook to set it up on the switches.

4. Copy the files to the switches with the below commands. Enter them one at a time so that you can enter in a password when prompted.
    1.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus.yml admin@172.100.100.101://mnt/flash
    2.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus admin@172.100.100.101://mnt/flash
    3.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus.yml admin@172.100.100.102://mnt/flash
    4.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus admin@172.100.100.102://mnt/flash
    5.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus.yml admin@172.100.100.103://mnt/flash
    6.     sudo scp /home/goarista/cmd/ocprometheus/ocprometheus admin@172.100.100.103://mnt/flash
5. SSH into each switch and add the following additional configuration.
    1. Take a few seconds before entering the “no shutdown” command for the ocprometheus daemon. This gives the TerminAttr daemon time to start up and use port 6042 before ocprometheus can get info from that port.
```
conf t
ip access-list capstone
permit ip any any
permit tcp any any
permit tcp any any eq 8080
permit tcp any any eq 6042
!
exit
conf t
system control-plane
ip access-group capstone in
ip access-group capstone vrf MGMT in
daemon TerminAttr
  exec /usr/bin/TerminAttr -disableaaa -grpcaddr MGMT/127.0.0.1:6042
no shutdown
!
daemon ocprometheus
  exec /sbin/ip netns exec ns-MGMT /mnt/flash/ocprometheus -config /mnt/flash/ocprometheus.yml -addr localhost:6042 -username admin -password admin
no shutdown
```

6. Go to the public IP address of the telemetry server on port 9090 where Prometheus can be viewed to confirm data is being received.
    1. Go to Status > Targets to confirm reachability to all devices.

# Configuration
## Ocprometheus Custom Configuration Guide
1. For clarification, we have configured ocprometheus in the installation instructions to grab data for BGP peering statues, interface up/down states, and tracking current CPU. These configuration instructions are an introduction to metric and subscription paths to show you how to find and configure your own metrics to be sent to Prometheus.
2. The ocprometheus.yml file is a collection of subscription paths and metric paths with regular expressions. To customize what metrics are sent to Prometheus, the following background knowledge is needed.
    1. Layout of EOS_native paths.
    2. What metric paths are.
    3. How to use regular expressions to match data in metric paths.
    4. What subscription paths are.
### EOS Native Paths
3. Layout of EOS_native paths
    1. There is a wellspring of data surrounding the current state of the switch stored at any given time on the switch. To find this information, one could: 
        1. Use the metric explorer in Arista Cloud Vision to find metric paths of info you need.
        2. Make curl requests to crawl through the directories. This is what we will be using in this example.
    2. Curl requests
        1. In order to see these paths and information, you should temporarily add a subscription path to / in your ocprometheus.yml file. This is the root subscription path and will allow you to make curl requests to look through all of the switch config and decide what you want to track.
            1. Once you have finished adding metric and subscription paths, this should be removed.
        2. Root subscription path looks like “- /” and is in the same indentation as the other subscription paths in the ocprometheus.yml file.
        3. Once the root path has been added, restart the ocprometheus daemon by entering the below commands in the switch configuration terminal.
            1.     daemon ocprometheus
            2.     shutdown
            3.     no shutdown
        4. Once ocprometheus is restarted, enter the below commands in the switch configuration terminal to enter bash and make a curl request to see the root directory of eos native paths.
            1.     bash
            2.     curl localhost:6060/rest
        5. Examine the paths you see. Generally, the most important ones are /Smash and /Sysdb. These directories can have a lot of information about routing protocols and interface statuses.
            1. To dig further down the path, simply add the directory to your curl request. This method can be used to look through the paths and find the information you want to track.
                1.     curl localhost:6060/rest/Smash
### Metric Paths
4. Intro to metric paths
    1. Where do they go?
        1. Metric paths are written in the ocprometheus.yml file under the “metrics:” section.
    2. Structure of a metric path
        1. The structure of a metric path and how it can be used to grab data is very straightforward. A metric path is very similar to a file path, with keys from key value pairs making up what looks like a directory path, and that is essentially what they are.
        2. Looking at the above curl image regarding /rest/Smash, it can be viewed that you are requesting the contents of “rest”, and from those contents you find a subdirectory called “Smash”. Looking at the result of the command you can see several more subdirectories, such as “arp”.
        3. Once you go far enough into subdirectories, you can find key value pairs to strings and numerical values. A key in the below example is “name”, and its value is “arp”. What we have been looking at so far have just been getting further into the directory, but this is where we see a standalone key-value pair that won't take you to more subdirectories. This would be the end of a metric path. Which would look like “/Smash/arp/name” and return the value of “arp”.
            1. This will not work by itself however in our setup, since “arp” is a string and not a numerical value. Prometheus needs to be sent numerical data with labels to function properly. We need to set a default value in the ocprmetheus.yml file for it to be recognized in the database as a numerical value that can be tracked. This can be done with the “defaultvalue” key to set a label.
                1. In addition, we need to set a label for it to be filtered by, this is usually handled by regular expressions however, in this example we can also use the keys “valuelabel” to set a label in most cases.
            1. This can be leveraged to count certain status messages if you add a count operation to grafana. The grafana query by itself will only chart the default value that it was set to.
            2. A much more simplistic use of these paths would be to track a numerical value over time, such as CPU utilization.
            3. The below is an example of a matric path used to get the system CPU usage from a processor on a switch.
                1. /Kernel/proc/cpu/utilization/cpu/0/system
    3. In order to track cpu of the types user, idle, and system without regular expressions, one would need three metric paths:
        1. /Kernel/proc/cpu/utilization/cpu/0/system
        2. /Kernel/proc/cpu/utilization/cpu/0/user
        3. /Kernel/proc/cpu/utilization/cpu/0/idle
    4. With regular expressions, this can be brought down to one path, showing the convenience of using them.
        1. /Kernel/proc/cpu/utilization/cpu/0/(?P<usageType>(?:system|user|idle))
### Regular Expressions
5. Using regular expressions to help obtain metric data.
    1. Once you have decided on information you would like to track, you can use regular expressions to format your metric paths, grab specific information, and label it for the database so you can filter by that label.
    2. One example of a metric path with regular expressions is the below. This tracks the up/down status of all interfaces on a switch.
        1. /Sysdb/interface/status/eth/phy/slice/1/intfStatus/(?P<intf>.+)/linkStatus
        2. The (?P<intf>.+) is the regular expression.
            1. <intf> is a label given to the directory it matches.
            2. .+ is the terms on which it will match input. For this example, the period means match any one character and the plus means to match any of the preceding symbol after the preceding symbols placement. So, this will match any character because of the period.
        3. This expression takes the place of a directory, and essentially says “match any directory that would be in this spot in the path”. In this instance, it is taking the place of interface names.
        4. What this essentially means, is that instead of specifying 4 specific metric paths for each interface to get their status, you can use the expression to make it match any interface, so you only have to write one metric path and it will track your specified info from all of them
            1. Thinking about our cpu with multiple types example from earlier, you could track each individual processor by replacing the /0/ with the regular expression “/(?P<cpuNum>)/”, and then replacing the end with the “(?P<usageType>(?:system|user|idle))” expression. This would let you sort by specific processor number, or just see each of those 3 metrics from each of the many processors.
        5. It then basically creates a label called intf that you can use to sort through information by interface in prometheus/Grafana.
    3. Using metric paths can also let you filter information.
        1. Look at the below metric path.
        2. /Kernel/proc/cpu/utilization/total/(?P<usageType>(?:system|user|idle))
            1. The regular expression is (?P<usageType>(?:system|user|idle)) and is similar to having two queries to label and filter info.
                1. (P?<usageType> as we know from the previous example will label that part of the path, in this case it is labeling the type of cpu usage, so system, user, and idle will be labeled as a usageType
                2. Notice that (?:system|user|idle) is the specification on what needs to be matched instead of “.+”. What this section does is filter the output by saying “only match keys called system, user, or idle, so that you can track each of their values”. This will make it track several key value pairs in one directory.
### Subscription Paths
6. How to use subscription paths
    1. Subscription paths tell the switch what directory to subscribe to to get its information from. A subscription to a directory is a subscription to all of the data within that directory. This is the reason that “/” gives us all information under root, and “/Smash/” gives us all information under Smash, but not under Sysdb. Subscription paths should not be much shorter than required.
    2. Subscription paths are essentially smaller metric paths.
        1. If you have a metric path of “/Kernel/proc/cpu/utilization/total/(?P<usageType>(?:system|user|idle)) ” then a subscription path of “/Kernel/proc/cpu/utilization/” would suffice.
        2. These subscription paths occur above the metric paths under “subscriptions:”.
## Grafana Dashboard Configuration
1. Go to the public Ip of the telemetry server at port 3000
    1. Remember to create a firewall rule for ports 9090 and 3000 in google cloud.
    2. Enter admin admin for the credentials, it will ask you to make new credentials.
        1. @Stout2024
2. Go to Connections > Data Sources > Add New Data Source.
    1. Select Prometheus as the data source.
3. Modify the data source by setting the connection to localhost at the Prometheus port.
    1. Click Save and Test, you should see a validation.
    2. Click building a dashboard in the validation message.
4. Click Add Visualization and select our Prometheus datasource.
5. Go to Query > code.
    1. Input the below for our first query.
        1.     count by(linkStatus) (basestatus{linkStatus=~"linkUp|linkDown"})
        2. Click the blue “run queries” button next to the code button.
6. On the right side of the screen, switch the type of panel from “Time Series” to Stat.
    1. Under Panel Options,
        1. Change the panel title to “Interface Link States”.
    2. Under Stat Styles,
        1. Text mode: Value and name
        2. Graph Mode: None
7. Click Save at the top right of the screen.
    1. When the Save Dashboard menu pops up call it something along the lines of Current States.
    2. If it doesn’t exit out of the current scene click apply next to save.
8. Click Add > Visualization.
9. Do the same setup as the interface status panel except with the below query code and panel name.
    1. Panel Name: BGP Peer Count
    2. Code:
        1.     count by(bgpState) (bgppeerstatus)
        2. Click the blue “run queries” button next to the code button.
10. Change the time duration to from now to now.
11. Make a new dashboard by going to Dashboards > new > new dashboard.
    1. Click Add visualization like the other dashboard and once again select Prometheus as the data source.
12. Use the following to set up a systemCPU tracker.
    1. Under Query > Code enter the below.
        1.     cpuinfo{usageType="system"}
        2. Click the blue “run queries” button next to the code button.
    2. Panel option
        1. Panel Title: SystemCPU
    3. Save and name the dashboard CPU Tracker.
    d. Click apply next to save.
13.	Make another visualization panel in the dashboard like step 12, but change the word “system” in the code to “user”.
    1. Title: UserCPU
    2. Click the blue “run queries” button next to the code button before you save it.
    3. Click apply next to save.



