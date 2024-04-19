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
In this section, we will be onbaording the Arista switches into our Nautobot service.
## Steps


