# Creating a Dynamic Inventory using the Nautobot GraphQL Dynamic Inventory Plugin

When adjusting device configurations on a Source of Truth (SoT) platform like Nautobot, managing hundreds or even thousands of devices can quickly become overwhelming. As a result, a static host file is not a practical or scalable solution for integrating a network automation framework, as it must be stored on the control node. Fortunately, Nautobot provides a dynamic inventory plugin that uses GraphQL to query our Nautobot instance for the desired host. This plugin can be found on Ansible Galaxy, a free platform that allows users to discover, download, and share community-generated roles and collections. This simplifies the process of incorporating a dynamic inventory into both your network automation framework and any other playbooks you may require.

# Steps
1. On the Linux desktop instance in Google Cloud, open the Terminal and run a system update using apt
`sudo apt update && sudo apt full-upgrade -y`
2. Install Ansible using Ansible's apt repository
`sudo apt install software-properties-common`
`sudo add-apt-repository --yes --update ppa:ansible/ansible`
`sudo apt install ansible -y`
