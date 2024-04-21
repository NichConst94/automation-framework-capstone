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

