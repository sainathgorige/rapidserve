import questionary
import yaml
import os
import subprocess
import time

result = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
base_directory = result.decode('utf-8').strip()

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
        elif cdn_choice.startswith("no"):
            print("Good Bye.")
        else:
            print("Invalid choice.")

    elif new_customer.startswith("Existing Services"):
        service_option = questionary.select("What service are you looking for?",
                                            choices=["Modify cdn", "cdn Status"]).ask()
        if service_option == "Modify cdn":
            print("Modify your Infrastructure.")
            # modify_cdn()
        elif service_option == "cdn Status":
            org_name = questionary.text("Enter your org name to fetch the status:").ask()
            tenant_data = fetch_tenant_info(org_name)
            print(yaml.dump({"tenant": tenant_data}, sort_keys=False))

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