import questionary
import yaml
import os
import subprocess
import time
import paramiko

result = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
base_directory = result.decode('utf-8').strip()

def modify_cdn():
    org_name = questionary.text("Enter your org name:").ask()
    tenant_data = fetch_tenant_info(org_name)
    if not tenant_data:
        print("Tenant data not found.")
        return
    print(yaml.dump({"tenant": tenant_data}, sort_keys=False))

    modification_choice = questionary.select(
        "Do you want to add or delete a component?",
        choices=["Add", "Delete"]).ask()

    data = read_cdn_config()
    tenant_index = next((i for i, t in enumerate(data['tenants']) if t['name'] == org_name), None)
    if tenant_index is None:
        print("Tenant not found in the configuration.")
        return

    if modification_choice == "Add":
        add_choice = questionary.select(
            "What component would you like to add?",
            choices=["Subnet", "Container", "Existing Container"]).ask()
        add_component(data, tenant_index, add_choice)
    elif modification_choice == "Delete":
        delete_choice = questionary.select(
            "What component would you like to delete?",
            choices=["Subnet", "Container", "Existing Container"]).ask()
        delete_component(data, tenant_index, delete_choice)

    save_cdn_config(data)
    print(f"{modification_choice} operation completed.")


def add_component(data, tenant_index, component_type):
    tenant = data['tenants'][tenant_index]

    if component_type == "Subnet":
        vpc_name = questionary.select(
            "Choose the VPC for the new subnet:",
            choices=[vpc['name'] for vpc in tenant['vpcs']]
        ).ask()
        cidr = questionary.text("Enter CIDR block for the new subnet:").ask()
        subnet_name = f"{vpc_name[:2]}_{tenant['name'][:2].lower()}_{vpc_name[3:]}_S{len(tenant['subnets']) + 1}"
        tenant['subnets'].append({
            'name': subnet_name,
            'CIDR': cidr,
            'vpc': vpc_name,
            'subnet_state': 'requested'
        })

    elif component_type == "Container":
        vpc_name = questionary.select(
            "Choose the VPC for the new container:",
            choices=[vpc['name'] for vpc in tenant['vpcs']]
        ).ask()
        container_name = f"{vpc_name[:2].lower()}_{tenant['name'][:2].lower()}_{vpc_name[3:]}_container{len(tenant['containers']) + 1}"
        chosen_subnets = questionary.checkbox(
            "Select subnets for the container:",
            choices=[s['name'] for s in tenant['subnets'] if s['vpc'] == vpc_name]
        ).ask()
        tenant['containers'].append({
            'name': container_name,
            'vpc': vpc_name,
            'subnets': chosen_subnets,
            'container_state': 'requested'
        })

    elif component_type == "Existing Container":
        region = questionary.text("Enter the region where this container is deployed:").ask()
        public_ips = questionary.text("Enter the IPs to reach the container:").ask()
        tenant['existing_containers'].append({
            'region': region,
            'public_ips': public_ips,
            'state': 'requested'
        })

def update_tenant(original, updated):
    # Helper function to update tenant info in the full list
    original.update(updated)

def delete_component(data, tenant_index, component_type):
    tenant = data['tenants'][tenant_index]

    if component_type == "Subnet":
        subnet_name = questionary.select(
            "Select the Subnet to delete:",
            choices=[subnet['name'] for subnet in tenant['subnets']]
        ).ask()
        tenant['subnets'] = [subnet for subnet in tenant['subnets'] if subnet['name'] != subnet_name]

    elif component_type == "Container":
        container_name = questionary.select(
            "Select the Container to delete:",
            choices=[container['name'] for container in tenant['containers']]
        ).ask()
        tenant['containers'] = [container for container in tenant['containers'] if container['name'] != container_name]

    elif component_type == "Existing Container":
        existing_container_region = questionary.select(
            "Select the region of the existing container to delete:",
            choices=[container['region'] for container in tenant['existing_containers']]
        ).ask()
        tenant['existing_containers'] = [
            container for container in tenant['existing_containers']
            if container['region'] != existing_container_region
        ]

def fetch_dns_log(tenant_name):
    hosts = ["192.168.38.8", "192.168.38.9"]
    username = "vmadm"
    password = "vmadm"
    log_file_name = f"{tenant_name}_dns_queries.log"

    for host in hosts:
        try:
            # Establish SSH connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password)

            # Check if log file exists and fetch its contents
            stdin, stdout, stderr = client.exec_command(f"cat /tmp/{log_file_name}")
            contents = stdout.read().decode('utf-8')
            if contents:
                print(f"Contents of {log_file_name} from {host}:\n{contents}\n")
            else:
                print(f"No DNS log file found for tenant '{tenant_name}' on host {host}.")
            
            client.close()
        except Exception as e:
            print(f"Failed to fetch DNS log from {host}: {e}")

def fetch_nginx_log(tenant_name):
    hosts = ["192.168.38.8", "192.168.38.9"]
    username = "vmadm"
    password = "vmadm"
    log_file_name = f"rs_{tenant_name[:2]}.log"

    for host in hosts:
        try:
            # Establish SSH connection
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, username=username, password=password)

            # Check if log file exists and fetch its contents
            stdin, stdout, stderr = client.exec_command(f"cat /tmp/{log_file_name} | tail -50")
            contents = stdout.read().decode('utf-8')
            if contents:
                print(f"Contents of {log_file_name} from {host}:\n{contents}\n")
            else:
                print(f"No nginx log file found for tenant '{tenant_name}' on host {host}.")
            
            client.close()
        except Exception as e:
            print(f"Failed to fetch nginx log from {host}: {e}")

def create_cdn(existing_tenants=None, tenant_name='default'):
    if existing_tenants is None:
        existing_tenants = []

    tenant = {
        'name': tenant_name,
        'numberOfVpcs': '4',
        'tunnel_state': 'requested',
        'vpcs': [],
        'subnets': [],
        'containers': [],
        'origin_ip': questionary.text("Enter the origin server IP:").ask(),
        #'origin_url': questionary.text("Enter the origin server URL to fetch from customer info and deploy in CDN infra:").ask(),
        'domain_name': questionary.text("Enter the domain name:").ask(),
        'existing_containers': get_existing_containers_info(),
        'origin_replication_region': questionary.select("Where do you want to place the proxy server?", choices=['ireland', 'greece', 'bangladesh', 'thailand']).ask()

    }

    regions = ['ireland', 'greece', 'thailand', 'bangladesh']
    subnet_counters = {}
    container_counters = {}

    fixed_vpcs = [
        {'name': 'rs_gr', 'vpc_state': 'active'},
        {'name': 'rs_ir', 'vpc_state': 'active'},
        {'name': 'rs_ba', 'vpc_state': 'active'},
        {'name': 'rs_th', 'vpc_state': 'active'}
    ]

    for vpc in fixed_vpcs:
        tenant['vpcs'].append(vpc)
        subnet_counters[vpc['name']] = 0
        container_counters[vpc['name']] = 0

    # Subnets
    total_subnets = int(questionary.text("Enter the total number of subnets you want:").ask())
    for _ in range(total_subnets):
        vpc_name = questionary.select("Choose the VPC you want to deploy the subnet in:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        subnet_counters[vpc_name] += 1
        subnet_name = f"{vpc_name[:2]}_{tenant['name'][:2].lower()}_{vpc_name[3:]}_S{subnet_counters[vpc_name]}"
        # subnet_name = f"{vpc_name}_{tenant['name'][:2].lower()}_S{subnet_counters[vpc_name]}"
        cidr = questionary.text(f"Enter CIDR block for subnet {subnet_name}:").ask()
        subnet = {
            'name': subnet_name,
            'CIDR': cidr,
            'vpc': vpc_name,
            'subnet_state': 'requested'
        }
        tenant['subnets'].append(subnet)

    # containers
    total_containers = int(questionary.text("Enter total number of additional containers you need:").ask())
    for _ in range(total_containers):
        vpc_name = questionary.select("Choose the VPC you want to deploy the container in:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        container_counters[vpc_name] += 1
        container_name = f"{vpc_name[:2].lower()}_{tenant['name'][:2].lower()}_{vpc_name[3:]}_container{container_counters[vpc_name]}"
        #container_name = f"{vpc_name.lower()}_{tenant['name'][:2].lower()}_container{container_counters[vpc_name]}"
        # Loop until at least one subnet is chosen
# Before the checkbox prompt
        subnet_choices = [s['name'] for s in tenant['subnets'] if s['vpc'] == vpc_name]
        if not subnet_choices:
            print("No subnets available for selection. Please check your data.")
            chosen_subnets = []
        else:
            chosen_subnets = questionary.checkbox("Select subnets (multiple possible):", choices=subnet_choices).ask()
        container = {
            'name': container_name,
            'vpc': vpc_name,
            'subnets': chosen_subnets,
            'container_state': 'requested'
        }
        tenant['containers'].append(container)

    existing_tenants.append(tenant)
    return {'tenants': existing_tenants}

# Function to get information about existing containers
def get_existing_containers_info():
    num_existing_containers = questionary.text("How many containers do you already have that can run as edge containers?:").ask()
    existing_containers = []

    for _ in range(int(num_existing_containers)):
        container_info = {
            'region': questionary.text("Enter the region where this container is deployed:").ask(),
            'public_ips': questionary.text("Enter the IPs to reach the container").ask(),
            'state': 'requested'
        }
        existing_containers.append(container_info)

    return existing_containers

def main():
    print("Welcome to RapidServe CDNaaS")
    new_customer = questionary.select("Are you a new customer or looking for existing services?",
                                        choices=["New Customer", "Existing Services"]).ask()
    if new_customer.startswith("New Customer"):
        cdn_choice = questionary.select("Do you want to use RapidServe CDN?",choices=["yes", "no"]).ask()
        if cdn_choice.startswith("yes"):
            tenant_name = questionary.text("Enter your org name:").ask()
            print("Provide infromation for your existing Infrastructure")
            data = read_cdn_config()
            current_tenants = data.get('tenants', [])
            new_cdn = create_cdn(current_tenants, tenant_name)
            save_cdn_config(new_cdn)
            print("cdn created and saved to database")
            print("Please fetch customer_sync.yaml from https://github.com/karthikmp5/RapidServe and run it on the host where origin server is located. This will allow us to replicate your origin server")
        elif cdn_choice.startswith("no"):
            print("Good Bye.")
        else:
            print("Invalid choice.")

    elif new_customer.startswith("Existing Services"):
        service_option = questionary.select(
            "What service are you looking for?",
            choices=["Modify CDN Infrastructure", "Verify CDN Status", "Fetch DNS Logs", "Fetch Nginx Logs"]
        ).ask()
        
        if service_option == "Modify CDN Infrastructure":
            print("Modify your Infrastructure.")
            modify_cdn()
        elif service_option == "Verify CDN Status":
            org_name = questionary.text("Enter your org name to fetch the status:").ask()
            tenant_data = fetch_tenant_info(org_name)
            print(yaml.dump({"tenant": tenant_data}, sort_keys=False))
        elif service_option == "Fetch DNS Logs":
            tenant_name = questionary.text("Enter tenant name to fetch DNS logs:").ask()
            fetch_dns_log(tenant_name)
        elif service_option == "Fetch Nginx Logs":
            tenant_name = questionary.text("Enter tenant name to fetch Nginx logs:").ask()
            fetch_nginx_log(tenant_name)

def run_script(script_path, args):
    try:
        subprocess.run(["python3", script_path, *args],  check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")

def save_cdn_config(cdn_config):
    with open("cdn_config.yaml", "w") as file:
        yaml.safe_dump(cdn_config, file, sort_keys=False)

def read_cdn_config():
    try:
        with open("cdn_config.yaml", "r") as file:
            data = yaml.safe_load(file)
            if data is None:  # If file is empty, return an empty dictionary
                return {'tenants': []}
            return data
    except FileNotFoundError:
        return {'tenants': []}

def fetch_tenant_info(org_name):
    data = read_cdn_config()
    if data is None:
        print("Failed to read data.")
        return
    
    # Find the specific tenant based on the organization name
    tenant_data = next((tenant for tenant in data.get('tenants', []) if tenant['name'] == org_name), None)
    if tenant_data is None:
        print(f"No data found for the organization named {org_name}. Please check the organization name and try again.")
        return

    # Print the data in a structured format
    print("Fetching cdn data for organization:", org_name)
    return(tenant_data)

if __name__ == "__main__":
    main()
