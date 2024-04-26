import yaml
import subprocess
from ansible_runner import run
import ipaddress
import sys
import os
import json

result = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
base_directory = result.decode('utf-8').strip()

def select_inventory(vpc_name):
    if vpc_name.endswith(('ba', 'th')):
        print("selected asia")
        return os.path.join(base_directory, 'southbound', 'host_inventory_asia.ini')
    elif vpc_name.endswith(('ir', 'gr')):
        print("selected europe")
        return os.path.join(base_directory, 'southbound', 'host_inventory_europe.ini')
    else:
        print("selected default")
        return os.path.join(base_directory, 'southbound', 'host_inventory.ini')

def build_ansible_command(filename, vars_dict, inventory_file):
    # Convert vars_dict to a JSON-like string for the --extra-vars argument
    extra_vars = json.dumps(vars_dict)
    
    command = [
        'ansible-playbook',
        '-i', inventory_file,
        filename,
        '--extra-vars', f"'{extra_vars}'",
        '-vvv'  
    ]
    return command

# def run_playbook(filename, vars_dict, vpc_name='default'):
#     print(f"playbook {filename} is running")
#     inventory_file = select_inventory(vpc_name)
#     print(f"the inventory is {inventory_file}")
#     print(f"{vars_dict}")
#     command = build_ansible_command(filename, vars_dict, inventory_file)
#     print("Command to be executed:")
#     print(command)
#     config = {
#         'private_data_dir': './',
#         'playbook': filename,
#         'extravars': vars_dict,
#         'verbosity': 1,
#         'inventory': inventory_file
#         }
#     result = run(**config)
#     return result

def run_playbook(filename, vars_dict, vpc_name='default'):
    inventory_file = select_inventory(vpc_name)
    extra_vars = json.dumps(vars_dict)
    try:
        command = [
            'ansible-playbook',
            # '-vvvv',
            filename,
            '-i', inventory_file,
            '--extra-vars', extra_vars
        ]
        subprocess.run(command, check=True, text=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error running Ansible playbook: {e}")
        print("Return code:", e.returncode)
        return 1

def calculate_ip(tenant_name, tenant_data):
    for subnet in tenant_data['subnets']:
        cidr = subnet['CIDR']
        
        # Extract the network address and prefix length from the CIDR
        network = ipaddress.ip_network(cidr)
        ip = str(network.network_address + 1)  # IP is the first address in the CIDR block
        dhcp_start = str(network.network_address + 2)  # DHCP start is the second address
        dhcp_end = str(network.broadcast_address - 1)  # DHCP end is the last but one address

        # Add the new fields to the subnet
        subnet['ip'] = ip
        subnet['dhcp_start'] = dhcp_start
        subnet['dhcp_end'] = dhcp_end
    save_updated_tenant_data(tenant_name, tenant_data)

# def segregate_vpcs(tenant_name, tenant_data):
#     regional_vpcs = {'asia_vpcs': [], 'europe_vpcs': []}
#     for vpc in tenant_data['vpcs']:
#         if vpc['name'].endswith(('ba', 'th')):
#             regional_vpcs['asia_vpcs'].append({'name': vpc['name']})  # Append VPC to Asia list
#         elif vpc['name'].endswith(('ir', 'gr')):
#             regional_vpcs['europe_vpcs'].append({'name': vpc['name']})  # Append VPC to Europe list

#     num_asia_vpcs = len(regional_vpcs['asia_vpcs'])
#     num_europe_vpcs = len(regional_vpcs['europe_vpcs'])

#     tenant_data['regional_vpcs'] = regional_vpcs  # Add regional VPCs to tenant data
#     save_updated_tenant_data(tenant_name, tenant_data)  # Save the updated tenant data

# def get_subnet():
#     # Run the subnetting script and capture the output
#     result = subprocess.run(['python3', 'subnetting.py', '192.168.4.0/24'], capture_output=True, text=True)
#     if result.returncode == 0:
#         return result.stdout.strip()  # Ensure whitespace is trimmed
#     else:
#         raise Exception("Failed to get subnet: " + result.stderr)

# 

def check_and_create_subnet(tenant_name, tenant_data):
    for subnet in tenant_data['subnets']:
        if subnet['subnet_state'] == 'requested':
            vars_dict = {
                'tenant_name': tenant_name,
                'tenant_data': tenant_data,
                'subnet_name': subnet['name'],
                'vpc_name': subnet['vpc'],
                'subnet_CIDR': subnet['CIDR'],
                'ip': subnet['ip'],
                'dhcp_start': subnet['dhcp_start'],
                'dhcp_end': subnet['dhcp_end']
            }
            playbook_path = os.path.join(base_directory, 'southbound', 'deploy_subnet.yaml')
            result = run_playbook(playbook_path, vars_dict, subnet['vpc'])
            if result == 0:
                subnet['subnet_state'] = 'active'
                save_updated_tenant_data(tenant_name, tenant_data)
            else:
                print("Error occurred while creating subnet resources.")
                sys.exit(1)

def check_and_create_containers(tenant_name, tenant_data):
    for container in tenant_data['containers']:
        if container['container_state'] == 'requested':
            # gateway_subnet = container['subnets'][0]
            # for subnet in tenant_data['subnets']:
            #     if subnet['name'] == gateway_subnet:
            #         container_gateway_ip = subnet['ip']
            vars_dict = {
                'tenant_name': tenant_name,
                'container_name': container['name'],
                'vpc_name': container['vpc'],
                'subnets': container['subnets'],
                # 'container_gateway_ip': container_gateway_ip
            }
            playbook_path = os.path.join(base_directory, 'southbound', 'deploy_con.yaml')
            result = run_playbook(playbook_path, vars_dict, container['vpc'])

            if result == 0:
                container['container_state'] = 'active'
                save_updated_tenant_data(tenant_name, tenant_data)
            else:
                print("Error occurred while creating container resources.")
                sys.exit(1)

def create_origin_replica(tenant_name, tenant_data):
    vars_dict = {
        'tenant_prefix': tenant_name[:2],
        'region': tenant_data['origin_replication_region'][:2]
    }
    playbook_path = os.path.join(base_directory, 'southbound', 'provider_replicate_origin.yaml')
    result = run_playbook(playbook_path, vars_dict)

    if result == 0:
        print("successfully replicated origin")
    else:
        print("Error occurred while replicating origin.")
        sys.exit(1)

def implement_scaling(tenant_name, tenant_data):
    vars_dict = {
        'tenant_name': tenant_name
    }
    playbook_path = os.path.join(base_directory, 'southbound', 'provider_scaling.yaml')
    result = run_playbook(playbook_path, vars_dict)

    if result == 0:
        print("successfully implemented scaling")
    else:
        print("Error occurred while implementing scaling.")
        sys.exit(1)

def implement_nginx_logging(tenant_name, tenant_data):
    vars_dict = {
        'tenant_name': tenant_name
    }
    playbook_path = os.path.join(base_directory, 'southbound', 'logging.yaml')
    result = run_playbook(playbook_path, vars_dict)
    
    if result == 0:
        print("successfully implemented nginx logging")
    else:
        print("Error occurred while implementing nginx logging.")
        sys.exit(1)

# def check_and_implement_dns(tenant_name, tenant_data):
#     regions = []
#     print(f"{tenant_data}")
#     print(f"defaut {regions}")
#     print(f"containers are {tenant_data['containers']}")
#     for container in tenant_data['containers']:
#         print(f"{container}")
#         if container['vpc'].endswith('gr') and 'greece' not in regions:
#             regions.append('greece')
#             print(f"gre {regions}")
#         if container['vpc'].endswith('ba') and 'bangladesh' not in regions:
#             regions.append('bangladesh')
#             print(f"ban {regions}")
#         if container['vpc'].endswith('th') and 'thailand' not in regions:
#             regions.append('thailand')
#             print(f"tha {regions}")
#         if container['vpc'].endswith('ir') and 'ireland' not in regions:
#             regions.append('ireland')
#             print(f"ire {regions}")
#     vars_dict = {
#             'tenant_name': tenant_name,
#             'regions': regions,
#             'domainName': tenant_data['domain_name'],
#             'origin_vpc_public_subnet_ip': tenant_data['origin_ip'],
#             'existing_regions': tenant_data['existing_containers']
#         }
#         print(f"vars for dns is {vars_dict}")
#         playbook_path = os.path.join(base_directory, 'southbound', 'implement_dns_new3.yml')
#         result = run_playbook(playbook_path, vars_dict)
#         if result == 0:
#             print("success")
#         else:
#             print("Error occurred while implementing DNS.")
#             sys.exit(1)

def check_and_implement_dns(tenant_name, tenant_data):
    regions = []
    # Populate the regions list
    for container in tenant_data['containers']:
        if container['vpc'].endswith('gr') and 'greece' not in regions:
            regions.append('greece')
        if container['vpc'].endswith('ba') and 'bangladesh' not in regions:
            regions.append('bangladesh')
        if container['vpc'].endswith('th') and 'thailand' not in regions:
            regions.append('thailand')
        if container['vpc'].endswith('ir') and 'ireland' not in regions:
            regions.append('ireland')

    # Prepare variables for playbook
    vars_dict = {
        'tenant_name': tenant_name,
        'regions': regions,
        'domainName': tenant_data['domain_name'],
        'origin_vpc_public_subnet_ip': tenant_data['origin_ip'],
        'existing_regions': tenant_data['existing_containers']
    }

    # Execute playbook
    playbook_path = os.path.join(base_directory, 'southbound', 'implement_dns_new4.yml')
    result = run_playbook(playbook_path, vars_dict)
    if result == 0:
        print("Successfully implemented DNS.")
    else:
        print("Error occurred while implementing DNS.")
        sys.exit(1)

def save_yaml(data):
    config_path = os.path.join(base_directory, 'cdn_config.yaml')
    with open(config_path, "w") as file:
        yaml.safe_dump(data, file, sort_keys=False)

def read_yaml():
    try:
        config_path = os.path.join(base_directory, 'cdn_config.yaml')
        with open(config_path, "r") as file:
            data = yaml.safe_load(file)
            if data is None:  # If file is empty, return an empty dictionary
                return {'tenants': []}
            return data
    except FileNotFoundError:
        return {'tenants': []}

def fetch_tenant_info(org_name):
    data = read_yaml()
    if data is None:
        print("Failed to read data.")
        return
    # Find the specific tenant based on the organization name
    tenant_data = next((tenant for tenant in data.get('tenants', []) if tenant['name'] == org_name), None)
    if tenant_data is None:
        print(f"No data found for the organization named {org_name}. Please check the organization name and try again.")
        return
    # Print the data in a structured format
    print("Fetching data for organization:", org_name)
    return(tenant_data)

def save_updated_tenant_data(tenant_name, tenant_data):
    full_data = read_yaml()  # Load the full structure
    for tenant in full_data['tenants']:
        if tenant['name'] == tenant_name:
            update_tenant(tenant, tenant_data)  # Update the tenant info in the full data
    save_yaml(full_data)


def update_tenant(original, updated):
    # Helper function to update tenant info in the full list
    original.update(updated)

if __name__ == "__main__":
    tenant_name = sys.argv[1] if len(sys.argv) > 1 else "default_tenant"
    # tenant_data = {"tenant": fetch_tenant_info(tenant_name)}
    tenant_data = fetch_tenant_info(tenant_name)
    if tenant_data:
        print("Tenant data loaded successfully.")
        # print(yaml.dump({"tenant": tenant_data}, sort_keys=False))
        # print(yaml.dump(tenant_data, sort_keys=False))
        # segregate_vpcs(tenant_name, tenant_data)
        calculate_ip(tenant_name, tenant_data)
        tenant_data = fetch_tenant_info(tenant_name)
        print(yaml.dump({"tenant": tenant_data}, sort_keys=False))
        # check_and_create_subnet(tenant_name, tenant_data)
        # check_and_create_containers(tenant_name, tenant_data)
        # create_origin_replica(tenant_name, tenant_data)
        check_and_implement_dns(tenant_name, tenant_data)
        # implement_scaling(tenant_name, tenant_data)
        # implement_nginx_logging(tenant_name, tenant_data)
    else:
        print(f"No data found for tenant: {tenant_name}")














# import yaml
# import sys

# def load_yaml(filename):
#     with open(filename, 'r') as file:
#         return yaml.safe_load(file)

# def get_tenant_data(tenants, tenant_name):
#     for tenant in tenants:
#         if tenant['name'] == tenant_name:
#             return tenant
#     return None

# def main(tenant_name):
#     data = load_yaml('cdn_config.yaml')
#     tenant_data = get_tenant_data(data['tenants'], tenant_name)
#     if tenant_data:
#         print(f"Data for tenant '{tenant_name}':")
#         print(tenant_data)
#     else:
#         print(f"No data found for tenant '{tenant_name}'.")
    
# if __name__ == "__main__":
#     if len(sys.argv) != 2:
#         print("Usage: python cdn_controller.py <tenant_name>")
#         sys.exit(1)
#     tenant_name = sys.argv[1]
#     main(tenant_name)
