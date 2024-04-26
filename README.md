# RapidServe: CDN as a Service (CDNaaS)

## Introduction

RapidServe is a comprehensive CDNaaS (Content Delivery Network as a Service) solution designed to streamline and enhance the delivery of web content. By leveraging RapidServe, tenants can efficiently distribute content closer to their users, reducing latency and improving user experience. This documentation provides a step-by-step guide on setting up and deploying the RapidServe CDN infrastructure.

## Getting Started
Follow these steps to deploy the RapidServe CDN infrastructure.

### Prerequisites
Ensure you have the following installed on your system before proceeding:
- etcd database
- Python3 and associated packages (etcd, pyyaml, ansible-runner, netaddr)
- dnsmasq

### Installation and Setup
#### Step 1: Install Dependencies
1. Setup the etcd database following the etcd setup document.
2. Install etcd:

   `sudo apt install python3-etcd`
4. Install the necessary dependencies:

    `sudo apt install python3-etcd python3-pyyaml python3-ansible-runner python3-netaddr dnsmasq`
5. Upgrade ansible collections

   `ansible-galaxy collection install ansible.netcommon --upgrade`

#### Step 2: Update Shell Script Permissions
Update the permissions for all shell script files to ensure they are executable:

`chmod +x <filename.sh>`

#### Step 3: Verify Tenant Input
Run the `verify_input.py` script to validate the input provided by the tenant:

`python3 verify_input.py`

#### Step 4: Parse Tenant input
Use `input_parser.py` to parse the tenant's input YAML file and store the data in the etcd database:

`python3 input_parser.py`

#### Step 5: Deploy base infrastructure, origin server and DNS server
Execute `state_controller.py` to check the state of the specified fields and deploy the necessary resources using the appropriate playbook:

`python3 state_controller.py <tenant_name>`

#### Step 6: Wait for DNS and Origin servers to launch. 
Use `virsh console` to access the dns and origin server's console and wait for the login prompt. Note the DNS server VM's IP address with `ip addr`, which will be used in Step 8:

`virsh console dns_server_vm`

`virsh console origin_server_vm`

#### Step 7: Implement DNS Functionality
Once the DNS server is operational, run `post_dns_deployment.sh` to activate DNS features and create load balancing rules for each VPC:

`./post_dns_deployment.sh <tenant_name>`

### Step 8: Update DNS Server List
For testing purposes, update the DNS server list on the user under test (e.g., the host VM) to include the DNS server VM's IP address:

`sudo vi /etc/resolv.conf`

`nameserver <DNS_VM_IP>`

Note: Ensure that the subnet of the user under test is present under the listed subnets in the implement_dns.yaml script.

### Step 9: Verify Pull Model
Test the pull model by executing the following command from the user's system:

`curl <tenant_name>.cdn.com`

### Step 10: Implement Push Model
Deploy the push model, which enables automatic content updates on edge servers from the origin server upon content changes:

`sudo ansible-playbook push_caching.yaml -i origin_server.ini`

### Step 11: Edit Application Content for testing
Test the push model by editing the `index.html` file on the origin server VM:

`virsh console origin_server_vm`

`vi /var/www/html/index.html` # Make any edit to the file

### Step 12: Verify Content Update through Push 
To confirm that content updates are properly propagated and to check cache status, execute the following command on any VM within the infrastructure:

`curl -i localhost`

Note: If `X-Cache-Status` is `HIT`, the content was successfully fetched from the cache. If it's `MISS`, the content was retrieved directly from the origin server.
