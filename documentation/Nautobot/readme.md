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





