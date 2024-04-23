# Ansible
Ansible is an open-source IT automation tool that helps automate common IT tasks. 

Prerequisites:
- Linux desktop instance created in Google Cloud
- Remote Desktop Protocol (RDP) client installed on the host computer

## Creating a Dynamic Inventory using the Nautobot GraphQL Dynamic Inventory Plugin
When adjusting device configurations on a Source of Truth (SoT) platform like Nautobot, managing hundreds or even thousands of devices can quickly become overwhelming. As a result, a static host file is not a practical or scalable solution for integrating a network automation framework, as it must be stored on the control node. Fortunately, Nautobot provides a dynamic inventory plugin that uses GraphQL to query our Nautobot instance for the desired host. This plugin can be found on Ansible Galaxy, a free platform that allows users to discover, download, and share community-generated roles and collections. This simplifies the process of incorporating a dynamic inventory into both your network automation framework and any other playbooks you may require. 

### Steps
When adjusting device configurations on a Source of Truth (SoT) platform like Nautobot, managing hundreds or even thousands of devices can quickly become overwhelming. As a result, a static host file is not a practical or scalable solution for integrating a network automation framework, as it must be stored on the control node. Fortunately, Nautobot provides a dynamic inventory plugin that uses GraphQL to query our Nautobot instance for the desired host. This plugin can be found on Ansible Galaxy, a free platform that allows users to discover, download, and share community-generated roles and collections. This simplifies the process of incorporating a dynamic inventory into both your network automation framework and any other playbooks you may require. 

1. On the Linux desktop instance in Google Cloud, open the Terminal and run a system update using apt

```bash
sudo apt update && sudo apt full-upgrade -y
```

2. Install Ansible using Ansible’s apt repository

```bash
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible -y
```

3. Install the required packages for Nautobot’s Ansible collection

```bash
sudo apt install python3-pip -y
sudo pip install netutils
```

4.	Switch to the /etc/ansible directory

```bash
cd /etc/ansible/
```

5.	Use the chmod command to change the file permissions of the ansible.cfg file to allow full access to the file by all users.

```bash
sudo chmod 777 ansible.cfg
```

6.	Create a complete initial Ansible configuration using the ansible-config init command. This creates a complete configuration that includes all currently installed plugins.

```bash
ansible-config init --disabled -t all > ansible.cfg
```

7.	Install the Nautobot Ansible collection using Ansible Galaxy

```bash
ansible-galaxy collection install networktocode.nautobot
```

8.	Navigate to the internal IP address of the Nautobot instance and login using a web browser. 
9.	In the Nautobot GUI, navigate to Admin > Profile > API Tokens
10.	Click ”Add a token”
11.	Click Create to accept the default settings. This will create an API token so Ansible can query Nautobot for device information. This token will never expire unless an expiration date is entered. Save this token to a text file as we will use it later. 
12.	Right-click on the desktop to create a folder named ansible-gql. We will use this folder to store our dynamic inventory plugin configuration and Ansible playbooks.
13.	Open the ansible-gql folder and create a YAML configuration file for the dynamic inventory plugin. We will name it inventory.yml.
14.	Open inventory.yml in a text editor such as nano or Visual Studio Code 
15.	Enter the following configuration details for the dynamic inventory plugin into the file:

```yaml
plugin: networktocode.nautobot.gql_inventory
api_endpoint: https://<IP_of_nautobot>
token: API token created from step 11
validate_certs: false
```
 
This is the minimum required configuration for the dynamic inventory plugin to work. The validate_certs parameter, while optional, is required for our environment because of Nautobot’s use of self-signed SSL/TLS certificates. 

16.	In the Terminal, use the ansible-inventory command to test the inventory plugin. Ansible will query the Nautobot SoT using the GraphQL dynamic inventory plugin to display information for each device onboarded in Nautobot.

```bash
ansible-inventory -v --list -i inventory.yml
```
## BGP

## Prometheus

In this section, we will walk through how to set up OCPrometheus using an Ansible playbook. This will automate the process of initializing it on the network devices by using the dynamic inventory. 

1. Ansible can be used to configure OCPrometheus on all devices referenced in the dynamic inventory file. Create a new file titled “init-prometheus.yml” for the playbook.  

2. Create the first play on SWITCH1 to configure the switch and copy the files from the Linux machine to the switch. Use the ansible.builtin.copy module to transfer the ocprometheus file from its location on the local device to the switch. Ensure it is placed in the /mnt/flash/ directory on the switch.

3. Create the second play. It is identical to the first except that this time the ocprometheus.yml file will be transferred from the local machine to the switch.

4. Create the third play. This will create ACLs on the switch using the arista.eos.eos_config module using the arista.eos.eos_config module. 

5. Create the fourth play. This will initialize the Prometheus Daemon on SWITCH1 using the arista.eos.eos_command module.

6. Copy the previous plays in the playbook twice, once for SWITCH2 and once for SWITCH3. Ensure to alter the names and hosts areas to reflect each switch name.

7. Run the playbook with the command:
   ```bash
   ansible-playbook init-prometheus.yml
   ```
8. Go to the public IP of the Prometheus server and go to Status > Targets. Verify that the state is set to “UP” for the devices.

9. Here is the SWITCH1 excerpt from the playbook:
```yaml
    - name: Configure Prometheus on SWITCH1 

  hosts: SWITCH1 

  gather_facts: false 

  connection: network_cli 

  vars: 

    ansible_connection: network_cli 

    ansible_network_os: eos 

    ansible_user: admin 

    ansible_password: admin 

    ansible_become: true 

    ansible_become_method: enable 

    ansible_become_password: admin 

    ansible_python_interpreter: /usr/bin/python3 

  tasks: 

    - name: Copy Prometheus Configuration Files to SWITCH1 (1/2) 

      ansible.builtin.copy: 

        src: /home/ubuntu/Desktop/ansible-gql/prometheus/ocprometheus 

        dest: /mnt/flash/ 

        mode: '0777' 

        group: root 

  

    - name: Copy Prometheus Configuration Files to SWITCH1 (2/2) 

      ansible.builtin.copy: 

        src: /home/ubuntu/Desktop/ansible-gql/prometheus/ocprometheus.yml 

        dest: /mnt/flash/ 

        mode: '0777' 

        group: root 

  

    - name: Create ACL 

      arista.eos.eos_config: 

        lines: 

          - permit ip any any 

          - permit tcp any any 

          - permit tcp any any eq 8080 

          - permit tcp any any eq 6042 

        parents: ip access-list capstone 

  

    - name: Initialize Prometheus Daemon on SWITCH1 

      arista.eos.eos_command: 

        commands: 

          - configure terminal 

          - system control-plane 

          - ip access-group capstone in 

          - ip access-group capstone vrf MGMT in 

          - daemon TerminAttr 

          - exec /usr/bin/TerminAttr -disableaaa -grpcaddr MGMT/127.0.0.1:6042 

          - no shutdown 

          - daemon ocprometheus 

          - exec /sbin/ip netns exec ns-MGMT /mnt/flash/ocprometheus 

              -config /mnt/flash/ocprometheus.yml -addr localhost:6042 -username admin -password admin 

          - no shutdown 
```        
