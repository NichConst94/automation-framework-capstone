## Prerequisites
- Container Labs Instance Created
- Route to Container Labs Arista Switches Created
# Google Cloud Instance Creation
In this section, we will be creating the base google cloud VM that the nautobot service will run on.
## Steps
1. In your project environment, go to Compute Engine > VM Instances > Create Instance.
2. Use the following choices for your VM instance.
    1. Name and Region
        1. Name: ntca-capstone-2024-nautobot
        2. Region: us-central1(Iowa)
        3. Zone: us-central1-a
    2. Machine Configuration
        1. General Purpose e2 Instance
        2. Machine type: Preset: e2-medium
        3. Availability policies: Standard
    3. Boot disk
        1. OS: Ubuntu
        2. Version: 20.04 LTS (x86)
        3. Size: 20 GB
    4. Firewall
        1. Allow HTTP traffic
        2. Allow HTTPS traffic
    5. Advanced Options
        1. Networking
            1. Network tags: nautobot-server
            2. Ip forwarding: Enable
    6. Create
6.	Once the instance is created, go to VM Instances, select the SSH button on the created Nautobot server to confirm connectivity.
7.	Run the command “sudo apt update && sudo apt upgrade -y”
8.	Ping the address of one of the switches in the container lab environment. If this fails, ensure container lab is running, and the route to the container switches has been created. Once this succeeds, your instance creation has been completed. 
# Nautobot Installation
In this section, we will be installing the Nautobot service as well as any dependencies for it's future configuration.
## Steps
1.	Run the following commands to install Nautobot dependencies.
    1.     sudo apt install -y git python3 python3-pip python3-venv python3-dev redis-server
    2.     sudo apt install -y postgresql
2.	Create the postgresql database with the following commands.
    1.     sudo -u postgres psql
        1.     CREATE DATABASE nautobot;
        2.     CREATE USER nautobot WITH PASSWORD '@Stout2024';
        3.     GRANT ALL PRIVILEGES ON DATABASE nautobot TO nautobot;
        4.     \connect nautobot
        5.     GRANT CREATE ON SCHEMA public TO nautobot;
        6.     \q
3.	Type the following commands to set up the Nautobot user and directory.
    1.     sudo useradd --system --shell /bin/bash --create-home --home-dir /opt/nautobot nautobot
    2.     sudo -u nautobot python3 -m venv /opt/nautobot
    3.     echo "export NAUTOBOT_ROOT=/opt/nautobot" | sudo tee -a ~nautobot/.bashrc
    4.     sudo -iu nautobot
4.	Type the following commands to start the initial Nautobot installation (output not shown due to length).
    1.     pip3 install --upgrade pip wheel
    2.     pip3 install nautobot
    3.     nautobot-server init
        1. Can choose y or n for sending installation metrics, we chose n.
5. We will now be editing some of the configuration file.
    1. Before making any changes, it is recommended to make a copy of the base configuration file with the command “cp nautobot_config.py nautobot_config.py.bak” in case you need to start over.
    2. Use the below command to edit the configuration file.
        1.     nano nautobot_config.py
    3. In the configuration file, there are several commented out sections of code that we will replace, or you can just paste in the code below its commented section.
        1. Find the commented section for "ALLOWED_HOSTS" and add the following line to the configuration file
            1.     ALLOWED_HOSTS = ["*"]
        2. Uncomment the DATABASES section and replace the credentials with the ones used in the postgresql database setup.
        3. Edit the following lines regarding Napalm, this is assuming your switches usernames and passwords are admin.
            1.     NAPALM_USERNAME = "admin"
            2.     NAPALM_PASSWORD = "admin"
            3.     NAPALM_ARGS = {"secret": "admin"}
        4. Edit the following line for plugins to include our desired plugins
            1.     PLUGINS = ["nautobot_device_onboarding", "nautobot_plugin_nornir", "nautobot_golden_config"]
        5. Add the following lines for the plugin configuration, this goes somewhere below the PLUGINS section we just added
```python
PLUGINS_CONFIG = {
    "nautobot_plugin_nornir": {
        "nornir_settings": {
            "credentials": "nautobot_plugin_nornir.plugins.credentials.settings_vars.CredentialsSettingsVars",
            "runner": {
                "plugin": "threaded",
                "options": {
                    "num_workers": 20,
                },
            },
        },
            "username": "admin",
            "password": "admin",
            "secret": "admin",
    },
    "nautobot_golden_config": {
        "per_feature_bar_width": 0.15,
        "per_feature_width": 13,
        "per_feature_height": 4,
        "enable_backup": True,
        "enable_compliance": True,
        "enable_intended": True,
        "enable_sotagg": True,
        "enable_plan": True,
        "enable_deploy": True,
        "enable_postprocessing": False,
        "sot_agg_transposer": None,
        "postprocessing_callables": [],
        "postprocessing_subscribed": [],
        "jinja_env": {
            "undefined": "jinja2.StrictUndefined",
            "trim_blocks": True,
            "lstrip_blocks": False,
        },
        # "default_deploy_status": "Not Approved",
        # "get_custom_compliance": "my.custom_compliance.func"
    },
}
```

5. Save and exit the configuration file
6. Use the following commands to add our needed plugins into a local requirements file, and then install them.
    1.     echo nautobot[napalm] >> $NAUTOBOT_ROOT/local_requirements.txt
    2.     echo nautobot-device-onboarding >> $NAUTOBOT_ROOT/local_requirements.txt
    3.     echo nautobot-golden-config >> $NAUTOBOT_ROOT/local_requirements.txt
    4.     echo nautobot-plugin-nornir >> $NAUTOBOT_ROOT/local_requirements.txt
    5.     pip3 install -r $NAUTOBOT_ROOT/local_requirements.txt
7.	Use the below commands to set up the database, create the admin user, create needed files, then check the server for errors
    1.     nautobot-server migrate
         1. This may take a few minutes.
    2.     nautobot-server createsuperuser
         1. Username: admin
         2. Email: Any
         3. Password: @Stout2024
    3.     nautobot-server collectstatic
    4.     nautobot-server check
    5. If there are no issues identified, procede to allow HTTPS access to Nautobot with self signed certificates and create service files
8. Use the below command to create a file known as uwsgi.ini
     1.     nano $NAUTOBOT_ROOT/uwsgi.ini
          1. Add the below code to the file. This code can be found in the official Nautobot documentation
```
[uwsgi]
; The IP address (typically localhost) and port that the WSGI process should listen on
socket = 127.0.0.1:8001
; Fail to start if any parameter in the configuration file isn’t explicitly understood by uWSGI
strict = true
; Enable master process to gracefully re-spawn and pre-fork workers
master = true
; Allow Python app-generated threads to run
enable-threads = true
;Try to remove all of the generated file/sockets during shutdown
vacuum = true
; Do not use multiple interpreters, allowing only Nautobot to run
single-interpreter = true
; Shutdown when receiving SIGTERM (default is respawn)
die-on-term = true
; Prevents uWSGI from starting if it is unable load Nautobot (usually due to errors)
need-app = true
; By default, uWSGI has rather verbose logging that can be noisy
disable-logging = true
; Assert that critical 4xx and 5xx errors are still logged
log-4xx = true
log-5xx = true
; Enable HTTP 1.1 keepalive support
http-keepalive = 1
 
;
; Advanced settings (disabled by default)
; Customize these for your environment if and only if you need them.
; Ref: https://uwsgi-docs.readthedocs.io/en/latest/Options.html
;
; Number of uWSGI workers to spawn. This should typically be 2n+1, where n is the number of CPU cores present.
; processes = 5
; If using subdirectory hosting e.g. example.com/nautobot, you must uncomment this line. Otherwise you'll get double paths e.g. example.com/nautobot/nautobot/.
; Ref: https://uwsgi-docs.readthedocs.io/en/latest/Changelog-2.0.11.html#fixpathinfo-routing-action
; route-run = fixpathinfo:
; If hosted behind a load balancer uncomment these lines, the harakiri timeout should be greater than your load balancer timeout.
; Ref: https://uwsgi-docs.readthedocs.io/en/latest/HTTP.html?highlight=keepalive#http-keep-alive
; harakiri = 65
; add-header = Connection: Keep-Alive
; http-keepalive = 1
```

9. Exit out of the nautobot user
    1.     exit
10. Use the below command to create a Nautobot service file
     1.     sudo nano /etc/systemd/system/nautobot.service
          1. Add the below code to the file. This code can be found in the official Nautobot documentation
```
[Unit]
Description=Nautobot WSGI Service
Documentation=https://docs.nautobot.com/projects/core/en/stable/
After=network-online.target
Wants=network-online.target
 
[Service]
Type=simple
Environment="NAUTOBOT_ROOT=/opt/nautobot"
 
User=nautobot
Group=nautobot
PIDFile=/var/tmp/nautobot.pid
WorkingDirectory=/opt/nautobot
ExecStart=/opt/nautobot/bin/nautobot-server start --pidfile /var/tmp/nautobot.pid --ini /opt/nautobot/uwsgi.ini
ExecStop=/opt/nautobot/bin/nautobot-server start --stop /var/tmp/nautobot.pid
ExecReload=/opt/nautobot/bin/nautobot-server start --reload /var/tmp/nautobot.pid
 
Restart=on-failure
RestartSec=30
PrivateTmp=true
 
[Install]
WantedBy=multi-user.target
```

11. Use the below command to create a Nautobot worker service file
     1.     sudo nano /etc/systemd/system/nautobot-worker.service
          1. Add the below code to the file. This code can be found in the official Nautobot documentation
```
[Unit]
Description=Nautobot Celery Worker
Documentation=https://docs.nautobot.com/projects/core/en/stable/
After=network-online.target
Wants=network-online.target
 
[Service]
Type=exec
Environment="NAUTOBOT_ROOT=/opt/nautobot"
 
User=nautobot
Group=nautobot
PIDFile=/var/tmp/nautobot-worker.pid
WorkingDirectory=/opt/nautobot
 
ExecStart=/opt/nautobot/bin/nautobot-server celery worker --loglevel INFO --pidfile /var/tmp/nautobot-worker.pid
 
Restart=always
RestartSec=30
PrivateTmp=true
 
[Install]
WantedBy=multi-user.target
```

12. Use the below command to create a Nautobot scheduler service file
     1.     sudo nano /etc/systemd/system/nautobot-worker.service
          1. Add the below code to the file. This code can be found in the official Nautobot documentation
```
[Unit]
Description=Nautobot Celery Beat Scheduler
Documentation=https://docs.nautobot.com/projects/core/en/stable/
After=network-online.target
Wants=network-online.target
 
[Service]
Type=exec
Environment="NAUTOBOT_ROOT=/opt/nautobot"
 
User=nautobot
Group=nautobot
PIDFile=/var/tmp/nautobot-scheduler.pid
WorkingDirectory=/opt/nautobot
 
ExecStart=/opt/nautobot/bin/nautobot-server celery beat --loglevel INFO --pidfile /var/tmp/nautobot-scheduler.pid
 
Restart=always
RestartSec=30
PrivateTmp=true
 
[Install]
WantedBy=multi-user.target
```
13.	Reload the systemd daemon and start the Nautobot services and enable them to initiate at boot time with the following commands.
    1.     sudo systemctl daemon-reload
    2.     sudo systemctl enable --now nautobot nautobot-worker nautobot-scheduler
    3.     sudo systemctl restart nautobot nautobot-worker nautobot-scheduler
14.	The next steps will be to enable HTTPS access to Nautobot. To do this, you will obtain an ssl certificate with the below commands.
    1.     sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        1.     -keyout /etc/ssl/private/nautobot.key \
        2.     -out /etc/ssl/certs/nautobot.crt
15.	Use the below command to install nginx.
    1.     sudo apt install -y nginx
16.	Once nginx is installed, enter the below into the terminal and paste the given configuration. This file can be found in the official Nautobot documentation.
    1.     sudo nano /etc/nginx/sites-available/nautobot.conf
```
server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
 
    server_name _;
 
    ssl_certificate /etc/ssl/certs/nautobot.crt;
    ssl_certificate_key /etc/ssl/private/nautobot.key;
 
    client_max_body_size 25m;
 
    location /static/ {
        alias /opt/nautobot/static/;
    }
 
    # For subdirectory hosting, you'll want to toggle this (e.g. `/nautobot/`).
    # Don't forget to set `FORCE_SCRIPT_NAME` in your `nautobot_config.py` to match.
    # location /nautobot/ {
    location / {
        include uwsgi_params;
        uwsgi_pass  127.0.0.1:8001;
        uwsgi_param Host $host;
        uwsgi_param X-Real-IP $remote_addr;
        uwsgi_param X-Forwarded-For $proxy_add_x_forwarded_for;
        uwsgi_param X-Forwarded-Proto $http_x_forwarded_proto;
 
        # If you want subdirectory hosting, uncomment this. The path must match
        # the path of this location block (e.g. `/nautobot`). For NGINX the path
        # MUST NOT end with a trailing "/".
        # uwsgi_param SCRIPT_NAME /nautobot;
    }
 
}
 
server {
    # Redirect HTTP traffic to HTTPS
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}
```

17.	 Enter the below commands to delete the default nginx file and set up a link with the configuration file you just made. Then, restart nginx.
     1.     sudo rm -f /etc/nginx/sites-enabled/default 
     2.     sudo ln -s /etc/nginx/sites-available/nautobot.conf /etc/nginx/sites-enabled/nautobot.conf
     3.     sudo systemctl restart nginx
18.	Switch to the nautobot user and set the $NAUTOBOT_ROOT permissions to 755 with the below commands.
    1.     sudo -iu nautobot
    2.     chmod 755 $NAUTOBOT_ROOT
# Nautobot Device Onboarding
In this section, we will be onbaording the Arista switches into our Nautobot service. For any of our Nautobot features, ansible playbooks, and telemetry related services to work, Nautobot must have devices onboarded into its system.
## Steps
First, to help organize our devices into a proper hierarchy, we need to create a system of organization for our devices. This includes location types, locations, and tags
1.	Go to Organization > Location Types > Add.
    1. Name: Container Lab
    2. Content Types: dcim | device
2.	 Next, go to Organization > Locations > Add to add 3 Site locations numbered 1-3, one for each switch
    1. For each site:
        1. Location Type: Container Lab
        2. Name: Capstone Site #
             1. Site number based on switches. 1,2, and 3 for S1 S2 and S3
        3. Status: Active
3. Many devices can be onboarded with little no setup, Arista devices require you to add a platform by going to Devices > Platform > Add.
    1. Name: AristaEOS
    2. Network driver: arista_eos
    3. NAPALM driver: eos
4. Prepare to Onboard an Arista container device.
    1. Go to Jobs > Jobs and click the edit button on the disabled “perform device onboarding” job.
    2. Set the job to enabled.
    3. Click update.
5. Onboard Arista container device.
    1. Click the run job button in the jobs menu.
    2. Use the following data for the job.
        1. Location: Capstone Site #
            1. 1 for switch 1, 2 for switch 2, etc
        2. IP address: address of device being onboarded
            1. 172.100.100.1 for this example
        3. Port: 443
        4. Platform: AristaEOS
    3. Click “Run Job Now”, the job should complete with the final result of the device being onboarded.
6.	Go to Devices > Devices to confirm the onboarding of the device, proceed to onboard the rest of the devices.
# Nautobot Golden Configuration
With the golden configuration and nornir plugins, you can generate configurations, backup configurations, and examine configuration compliance.
## GitHub Setup
1. In order for many of the golden configuration plugin features to work, you need to give nautobot access to a GitHub repository. These next steps will give you a token key you can give to nautobot.
    1. Make a GitHub repository created for backups and generated configurations. In this instance we will be getting an API token for Nautobot that allows it to access the repo. We will be using a classic key with all permissions for simplicity, but you can likely make a less permission heavy token.
    2. Click your profile and choose Settings > Developer settings > Personal access tokens > Tokens (classic) > Generate new token (classic).
    3. Give the token a note of its name and set the duration for however long you need. Then, assign it the necessary permissions and click Generate Token. Once the token is generated, copy it into a text file for now, we will need it for the next step.
        1. In this instance we gave the token full permissions.
        2. If the token expires, simply make a new one and replace the one in the file we specify later.
2. As the nautobot user, create a file that can store the token. In this instance, the command “nano gittoken.txt” is being used to create a file called gittoken, then the token is pasted in and saved. This file was created in /opt/nautobot/. Remember the absolute path that this file was created in.
3. On the nautobot server, go to Secrets > Secrets < Add.
    1. Give the secret a name.
    2. Provider: Text File
    3. Form: Path of the text file: "/opt/nautobot/gittoken.txt"
4. Now, go to Secrets > Secret Groups > Add.
    1. Assign the group a name.
    2. Access Type: HTTP(s)
    3. Secret Type: Token
    4. Secret: Token Secret created last step
5. Now that the access secret has been created, go to Extensibility > Git Repositories > Add.
    1. Give the repository a name, in this case it will be Test Repo
    2. Remote URL: URL of the GitHub repository you have edit access to that you wish for nautobot to send and receive config data.
    3. Secrets group: the group created last step.
    4. Ctl+Click backup configs, intended configs, and jinja templates.
        1. These could also be stored in 3 separate repositories, but for such a small example environment these will be kept together.
    5. Create and Sync.
6. Next, we will be going over a few steps to finalize the needed aspects of the golden configuration plugin. First, go to Jobs > Jobs and enable all golden configuration jobs the same way the onboarding job was enabled.
7. Go to Extensibility > GraphQL Queries > Add.
    1. Call this query SoTAgg (Source of truth aggregate).
        1. This query will be used in the generation of device configs. This query will grab information from the device data in nautobot, as well as a feature known as config contexts that we will discuss later
    2. Paste the below text into the query. This may change depending on your individual information needs if your setup differs from ours, so check the Nautobot golden configuration installation guide for more information regarding this query as that is what this one is based on.
```
query ($device_id: ID!) {
  device(id: $device_id) {
    config_context
    hostname: name
    position
    serial
    primary_ip4 {
      id
      primary_ip4_for {
        id
        name
      }
    }
    tags {
      name
    }
    platform {
      name
      manufacturer {
        name
      }
      napalm_driver
    }
    location {
      name
      vlans {
        id
        name
        vid
      }
      vlan_groups {
        id
      }
    }
    interfaces {
      description
      mac_address
      enabled
      name
      ip_addresses {
        address
        tags {
          id
        }
      }
      tags {
        id
      }
    }
  }
}
```

8. Using Nautobot’s golden configuration plugin, you can specify a GitHub repository where folders and files will be created by the plugin for its purposes. 
    1. Go to Golden Config > Golden Config Settings.
    2. Click on the Default Settings link, then click edit.
    3. Backup Repository: this is where backups of your device configs will be stored. The backup path we use will create a folder in your GitHub repository with the name of a location, and all of the devices in that location in nautobot will have their configs saved there. We use one location for all devices so there will only be one folder created.
        1. Backup Repository: the repository we created.
        2. Backup path: {{obj.location.name|slugify}}/{{obj.name}}.cfg.bak
        3. Backup test: checked
    4. Intended Configuration: Similar to the backup config in structure. This is where intended configs will be generated based on the templates and config context specified later.
        1. Intended repo: created repo
        2. Path: {{obj.location.name|slugify}}/{{obj.name}}.cfg
    5. Templates Configuration: this is a bit different from the others. This is where jinja templates for each device OS should be found in the repository, and is used by nautobot to generate device configs. In this case, a jinja template for EOS configuration will be stored in no folder, but instead in the main section of the repository. We will make this template later
        1. Jinja Repo: created repo
        2. Path: {{obj.platform.network_driver}}.j2
    6. Save
9. To test connection with the GitHub repo, go to Jobs > Jobs and run the backup configuration job.
    1. You could filter which devices will be backed up, but since we have 3, we will leave the default for no filters and all devices.
    2. You should see informational messages about the job being completed and the devices being backed up.
10. Go to the GitHub repository and confirm the files and folders have been created.
## Automatic Backups
1. Go to Jobs > Jobs > Run/Schedule Backup Configuration.
2. Under Job Execution,
    1. Type: Hourly (The VM instance hosting the switches is rarely on)
    2. Name: Scheduled Backups
    3. Start Date/Time: Whenever you wish to start.
        1. You must click on the field, select a date on the calendar, and type the time at the bottom of the calendar.
3. Under Jobs > Scheduled Jobs should be the created scheduled job.
4. Wait until the time of the job passes and check the GitHub page where the backups were directed to be located and confirm they are there.
    1. Backups will not be committed if no changes have been made to the config since last backup.
## Generating Configs
In order for configurations to be generated, we will create a jinja template in our GitHub repository that nautobot uses for generating device configurations. Then, we must create what are called config contexts, which are also added to that generated configuration depending on organizational features such as location and tags.
1. In your GitHub repository, create a file called “arista_eos.j2” and enter the below code
    1. This code will call upon other snippets of code that we will create. The reason for this organization is so you can find and modify sections of your template easier than looking through one large file.
```
{% include './eos/hostname.j2' %}

spanning-tree mode mstp
!
{% include './eos/aaa.j2' %}
!
{% include './eos/local_user.j2' %}
!
{% include './eos/ocprometheus.j2' %}
!
{% include './eos/interfaces.j2' %}
!
{% if config_context["routes"] is defined %}
{% if config_context["routes"]["static"] is defined %}
{% for static in config_context["routes"]["static"] %}
{{ static }}
{% endfor %}
{% endif %}
{% endif %}
!
ip routing
!
{% if config_context["bgp"] is defined %}
{% include './eos/bgp.j2' %}
{% endif %}
!
{% include './eos/services.j2' %}
!
end 
```

2. Create a file “hostname.j2” under a directory called “eos”
    1. Writing “eos/hostname.j2” as the filename will create the eos directory
    2. Enter the below data
```
hostname {{ hostname.split('.')[0] }}
```

3. Create a file “_loopback.j2” under the eos directory and enter the below data
```
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined %}
   ip address {{ addr["address"] }}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == false %}
   no shutdown
{% endif %}
```

4. Create a file “_mgmt.j2” under the eos directory and enter the below data
```
{% if interface["description"] | length > 1 %}
   description {{ interface["description"] }}
{% endif %}
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined %}
   ip address {{ addr["address"] }}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == false %}
   shutdown
{% endif %}
```

5. Create a file “_physical.j2” under the eos directory and enter the below data
```
{% if interface["ip_addresses"] | length > 0 %}
   no switchport
{% endif %}
{% if interface["mac_address"] != none %}
   mac-address {{ interface["mac_address"] }}
{% endif %}
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined %}
   ip address {{ addr["address"] }}
{% endif %}
{% endfor %}
{% endif %}
{% if interface["enabled"] == false %}
   shutdown
{% endif %}
```

6. Create a file “_svi.j2” under the eos directory and enter the below data
```
{% if interface["ip_addresses"] | length > 0 %}
{% for addr in interface["ip_addresses"] %}
{% if addr["address"] is defined %}
   ip address {{ addr["address"] }}
{% endif %}
{% endfor %}
{% else %}
   no ip address
{% endif %}
{% if interface["enabled"] == true %}
   no shutdown
{% endif %}
```

7. Create a file “aaa.j2” under the eos directory and enter the below data
```
aaa authorization exec default local
!
no aaa root
!
```

8. Create a file “bgp.j2” under the eos directory and enter the below data
```
router bgp {{ config_context["bgp"]["asn"] }}
   router-id {{ config_context["bgp"]["rid"] }}
{% for neighbor in config_context["bgp"]["neighbors"] %}
   neighbor {{ neighbor["ip"] }} remote-as {{ neighbor["remote-asn"] }}
   neighbor {{ neighbor["ip"] }} description {{neighbor["description"]}}
{% endfor %}
{% for network in config_context["bgp"]["networks"] %}
   network {{ network }}
{% endfor %}
```

9.	Create a file “interfaces.j2” under the eos directory and enter the below data
```
{% for interface in interfaces %}
interface {{ interface["name"] }}
{% if interface["cpf_ntc_description"] is defined and interface["cpf_ntc_description"] != "" %}
   description {{ interface["cpf_ntc_description"] }}
{% elif interface["description"] | length > 1 %}
   description {{ interface["description"] }}
{% endif %}
{% if 'lan' in interface["name"] %}
{% include "./eos/_svi.j2" %}
{% elif 'thernet' in interface["name"] %}
{% include "./eos/_physical.j2" %}
{% elif 'Loop' in interface["name"] %}
{% include "./eos/_loopback.j2" %}
{% elif 'anagement' in interface["name"] %}
{% include "./eos/_mgmt.j2" %}
{% endif %}
{% endfor %}
```

10.	Create a file “local_user.j2” under the eos directory and enter the below data
```
username admin privilege 15 role network-admin secret sha512 $6$eucN5ngreuExDgwS$xnD7T8jO..GBDX0DUlp.hn.W7yW94xTjSanqgaQGBzPIhDAsyAl9N4oScHvOMvf07uVBFI4mKMxwdVEUVKgY/.
```

11.	Create a file “ocprometheus.j2” under the eos directory and enter the below data
```
{% if config_context["ocprometheus"] is defined %}
ip access-list capstone
   10 permit ip any any
   20 permit tcp any any
   30 permit tcp any any eq 8080
   40 permit tcp any any eq 6042
!
system control-plane
   ip access-group capstone in
   ip access-group capstone vrf MGMT in
!
daemon TerminAttr
   exec /usr/bin/TerminAttr -disableaaa -grpcaddr MGMT/127.0.0.1:6042
   no shutdown
!
daemon ocprometheus
   exec /sbin/ip netns exec ns-MGMT /mnt/flash/ocprometheus -config /mnt/flash/ocprometheus.yml -addr localhost:6042 -username admin -password admin
   no shutdown
{% endif %}
```

12.	Create a file “services.j2” under the eos directory and enter the below data
```
management api http-commands
   no shutdown
   vrf MGMT
      no shutdown
!
```

As you may have noticed, certain templates drew from something known as config context. In order for this data to be parsed in the templates and added to the configuration, we need to define these in nautobot and assign them to organizational features like locations and tags.

13. An organizational feature we will use to attach to config context are tags.
    1. Go to Organization > Tags > Add
        1. Name: Border
        2. Content Type: dcim | device
14.	Assign the tag to each switch by going to Devices > Devices > Switch #
    1. Click edit
    2. Tag: Border
16.	Now that organizational features have been implemented, we can easily assign config contexts to those locations and tags. Config contexts are used when generating device configuration and are applied depending on the organizational features specified.
    1. Go to Extensibility > Config Contexts
        1. Name: Site 1 BGP
        2. Description: BGP for the border router of site 1
        3. Tags: Border
        4. Locations: Capstone Site 1
        5. Data: Data is represented in JSON, use the below config for Site 1. This JSON data will allow the configuration jinja templates to grab data by using the keys and values
```
{
    "bgp": {
        "asn": "100",
        "neighbors": [
            {
                "description": "description Peer with SWITCH2",
                "ip": "192.168.10.2",
                "password": "null",
                "remote-asn": 200
            },
            {
                "description": "description Peer with SWITCH3",
                "ip": "192.168.11.2",
                "password": "null",
                "remote-asn": 300
            }
        ],
        "networks": [
            "192.168.1.0/24",
            "192.168.2.0/24",
            "192.168.3.0/24"
        ],
        "rid": "1.1.1.1"
    }
}
```

17.	Repeat step 16 for sites 2 and 3, except use the below data and rename appropriately. Use the border tag for both, use the appropriate locations for both sites (2 for 2, 2 for 3)
Site 2
```
{
    "bgp": {
        "asn": "200",
        "neighbors": [
            {
                "description": "description Peer with SWITCH1",
                "ip": "192.168.10.1",
                "password": "null",
                "remote-asn": 100
            },
            {
                "description": "description Peer with SWITCH3",
                "ip": "192.168.12.2",
                "password": "null",
                "remote-asn": 300
            }
        ],
        "networks": [
            "192.168.4.0/24",
            "192.168.5.0/24",
            "192.168.6.0/24"
        ],
        "rid": "2.2.2.2"
    }
}
```

Site 3
```
{
    "bgp": {
        "asn": "300",
        "neighbors": [
            {
                "description": "description Peer with SWITCH1",
                "ip": "192.168.11.1",
                "password": "null",
                "remote-asn": 100
            },
            {
                "description": "description Peer with SWITCH2",
                "ip": "192.168.12.1",
                "password": "null",
                "remote-asn": 200
            }
        ],
        "networks": [
            "192.168.7.0/24",
            "192.168.8.0/24",
            "192.168.9.0/24"
        ],
        "rid": "3.3.3.3"
    }
}
```

18.	Make a config context for global default management route. No organizational features specified means it will apply to all devices
    1. Name: Default Management Route
    2. Locations: None
    3. Tags: None 
    4. Data:
```
{
    "routes": {
        "static": [
            "ip route vrf MGMT 0.0.0.0/0 172.100.100.1"
        ]
    }
}
```

19.	Make a config context for ocprometheus, assign the context to the Arista EOS platform so it will only apply to arista devices
    1. Platform: Arista EOS
    2. Data:
```
{
    "ocprometheus": true
}
```

20.	Another important thing to do in order to generate configurations properly is to add interfaces and IP addresses to our switches in nautobot, so that those interfaces can be shown in the generated config. Before this, we need to create IP addresses to use for those interfaces.
    1. Go to IPAM > Prefixes > Add
        1. Add the prefix 192.168.0.0/16 as a global prefix, this will encompass all of our addresses needed in our BGP configuration
21.	Now that the prefix has been added, we can create IP addresses that fall under that global prefix.
    1. Go to IPAM > IP Addresses > Add
        1. Add every IP address used in the Ethernet and Loopback interfaces. 192.168.9.1/24 as an example
            1. Address: IP Address
            2. Namespace: Global
            3. Status: Active
23.	Now that we have the addresses for the interfaces, we will add those interfaces and IPs to our switches.
    1. Edit each device and click Add Components > Interfaces
        1. Name: Name each interface appropriately
            1. Ex: Ethernet1, Loopback3, etc
        2. Status : Active
        3. IP Address: Select appropriate address from the ones created
25.	Now that Our jinja templates have been made, our tags assigned, and our config contexts created, it is time to generate the device configs.
    1. Go to Jobs > Generate Intended Configurations > Run 
        1. Run the job with no filters
26.	Go to the GitHub Repository, a configuration for the switches should have been created

# Compliance
One of the most useful tools available in the golden configuration plugin, is the configuration compliance feature. This feature allows you to define compliance rules, and make a report of how many of your devices are compliant to those rules.
1. Go to Golden Configuration > Compliance Features > Add and add each feature described below
    1. 2024 Capstone AAA 
        1. Name: 2024 Capstone AAA
        2. Description: aaa must be default local
    2. Ocprometheus acl
        1. Name: Ocprometheus acl
        2. Description: Acl needed for ocprometheus
    3. Ocprometheus ocprometheus
        1. Name: Ocprometheus ocprometheus
        2. Description: ocprometheus daemon
    4. Ocprometheus system control plane
        1. Name: Ocprometheus system control plane
        2. Description: control plane allow acl in
    5. Ocprometheus terminattr
        1. Name: Ocprometheus terminattr
        2. Description: terminattr daemon
2. Now that compliance features have been created, let us assign rules to them. Most will be related to Ocprometheus. Go to Golden Configuration > Compliance Rules > Add
3. Add this ACL Rule
    1. Platform: AristaEOS
    2. Feature: ocprometheus_acl
    3. Config Type: CLI
    4. Config to match:
```
ip access-list capstone
permit ip any any
permit tcp any any
permit tcp any any eq 8080
permit tcp any any eq 6042
```

4. Add this AAA Rule
    1. Platform: AristaEOS
    2. Feature: 2024_capstone_aaa
    3. Config Type: CLI
    4. Config to match:
```
aaa authorization exec default local
```

5. Add this daemon Rule
    1. Platform: AristaEOS
    2. Feature: ocprometheus_ocprometheus
    3. Config Type: CLI
    4. Config to match:
```
daemon ocprometheus
exec /sbin/ip netns exec ns-MGMT /mnt/flash/ocprometheus -config /mnt/flash/ocprometheus.yml -addr localhost:6042 -username admin -password admin
no shutdown
```

6. Add this control plane Rule
    1. Platform: AristaEOS
    2. Feature: ocprometheus_system_control_plane
    3. Config Type: CLI
    4. Config to match:
```
system control-plane
ip access-group capstone in
ip access-group capstone vrf MGMT in
```

7. Add this daemon Rule
    1. Platform: AristaEOS
    2. Feature: ocprometheus_terminattr
    3. Config Type: CLI
    4. Config to match:
```
daemon TerminAttr
exec /usr/bin/TerminAttr -disableaaa -grpcaddr MGMT/127.0.0.1:6042
no shutdown
```
8. Run these jobs in order
    1. Backup Configurations
    2. Generate Intended Configurations
    3. Perform Configuration Compliance
9. Go to Golden Config > Compliance Report
    1. This is where you can observe a graphed visual of compliance. In this instance the ocprometheus related configuration has been removed from the devices to show noncompliance
10.	Go to Golden Config > Config Compliance
    1. This is where you can see a different visual of the device compliance, you can also click on a device and examine into further depth the reasons behind noncompliance


