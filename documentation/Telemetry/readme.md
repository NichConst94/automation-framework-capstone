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





