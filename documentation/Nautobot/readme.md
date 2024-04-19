## Prerequisites
- Container Labs Instance Created
- Route to Container Labs Arista Switches Created
# Google Cloud Instance Creation
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


