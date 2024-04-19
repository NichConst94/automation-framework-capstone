# Google Cloud Instance Creation
1. In your project environment, go to Compute Engine > VM Instances > Create Instance.
2.     Use the following choices for your VM instance.
a.	Name and Region
i.	Name: ntca-capstone-2024-nautobot
ii.	Region: us-central1(Iowa)
iii.	Zone: us-central1-a
 
b.	Machine Configuration
i.	General Purpose e2 Instance
ii.	Machine type:  Preset: e2-medium
iii.	Availability policies: Standard
 
 
c.	Boot disk
i.	OS: Ubuntu
ii.	Version: 20.04 LTS (x86)
iii.	Size: 20 GB
 
 
d.	Firewall
i.	Allow HTTP traffic
ii.	Allow HTTPS traffic
 
e.	Advanced Options
i.	Networking
1.	Network tags: nautobot-server
2.	Ip forwarding: Enable
 
f.	 Create
 
6.	Once the instance is created, go to VM Instances, select the SSH button on the created Nautobot server to confirm connectivity.
 
 
7.	Run the command “sudo apt update && sudo apt upgrade -y”
 
8.	Ping the address of one of the switches in the container lab environment. If this fails, ensure container lab is running, and the route to the container switches has been created. Once this succeeds, your instance creation has been completed. 


