import yaml
import questionary
import subprocess
import time
import os

result = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'])
base_directory = result.decode('utf-8').strip()

def create_infra(existing_tenants=None, tenant_name='default'):
    if existing_tenants is None:
        existing_tenants = []

    tenant = {
        'name': tenant_name,
        'numberOfVpcs': questionary.text("Enter the number of VPCs you want (max 4):").ask(),
        'tunnel_state': 'requested',
        'vpcs': [],
        'subnets': [],
        'containers': []
    }

    regions = ['India', 'Japan', 'Germany', 'France']
    subnet_counters = {}
    container_counters = {}

    # VPCs
    for _ in range(int(tenant['numberOfVpcs'])):
        region = questionary.select("Choose the region for the VPC:", choices=regions).ask()
        vpc_name = f"{tenant['name'][:2].lower()}_{region[:2].lower()}"
        vpc = {
            'name': vpc_name,
            'vpc_state': 'requested'
        }
        tenant['vpcs'].append(vpc)
        subnet_counters[vpc_name] = 0
        container_counters[vpc_name] = 0


    # Subnets
    total_subnets = int(questionary.text("Enter the total number of subnets you want:").ask())
    for _ in range(total_subnets):
        vpc_name = questionary.select("Choose the VPC you want to deploy the subnet in:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        subnet_counters[vpc_name] += 1
        subnet_name = f"{vpc_name}_S{subnet_counters[vpc_name]}"
        cidr = questionary.text(f"Enter CIDR block for subnet {subnet_name}:").ask()
        subnet = {
            'name': subnet_name,
            'CIDR': cidr,
            'vpc': vpc_name,
            'subnet_state': 'requested'
        }
        tenant['subnets'].append(subnet)

    # containers
    total_containers = int(questionary.text("Enter total number of containers:").ask())
    for _ in range(total_containers):
        vpc_name = questionary.select("Choose the VPC you want to deploy the container in:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        # container_type = questionary.text("What type of container do you want it be (origin or edge)").ask()
        container_counters[vpc_name] += 1
        container_name = f"{vpc_name.lower()}_container{container_counters[vpc_name]}"
        # Loop until at least one subnet is chosen
        chosen_subnets = []
        while not chosen_subnets:
            chosen_subnets = questionary.checkbox("Select subnets (multiple possible):", choices=[s['name'] for s in tenant['subnets'] if s['vpc'] == vpc_name]).ask()
            if not chosen_subnets:
                print("Warning: No subnets selected. Container cannot be deployed without a subnet. Please select at least one subnet.")

        container = {
            'name': container_name,
            'vpc': vpc_name,
            'subnets': chosen_subnets,
            'container_state': 'requested'
        }
        tenant['containers'].append(container)

    # VMs
    # total_vms = int(questionary.text("Enter total number of VMs:").ask())
    # for _ in range(total_vms):
    #     vm = {
    #         'name': questionary.text("Enter VM name:").ask(),
    #         'VM_state': 'requested',
    #         'subnets': questionary.checkbox("Select subnets (multiple possible):", choices=[s['name'] for s in tenant['subnets']]).ask(),
    #         'model': 'ubuntu',
    #         'RAM_size': '2048',
    #         'CPUs': '2',
    #         'disk_size': '12G'
    #     }
    #     tenant['VMs'].append(vm)

    existing_tenants.append(tenant)
    return {'tenants': existing_tenants}

def save_infra_config(data):
    with open("config.yaml", "w") as file:
        yaml.safe_dump(data, file, sort_keys=False)

def read_infra_config():
    try:
        with open("config.yaml", "r") as file:
            data = yaml.safe_load(file)
            if data is None:  # If file is empty, return an empty dictionary
                return {'tenants': []}
            return data
    except FileNotFoundError:
        return {'tenants': []}

def fetch_tenant_info(org_name):
    data = read_infra_config()
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

def modify_infra():
    org_name = questionary.text("Enter your org name:").ask()
    tenant_data = fetch_tenant_info(org_name)
    print(yaml.dump({"tenant": tenant_data}, sort_keys=False))

    modification_choice = questionary.select(
        "Please find your existing Infra above. Do you want to add or delete a component?",
        choices=["Add", "Delete"]).ask()

    if modification_choice == "Add":
        add_choice = questionary.select(
            "What component would you like to add?",
            choices=["VPC", "Subnet", "Container"]).ask()
        add_component({'tenant': tenant_data}, add_choice, org_name)

    elif modification_choice == "Delete":
        delete_choice = questionary.select(
            "What component would you like to delete?",
            choices=["VPC", "Subnet", "Container"]).ask()
        delete_component({'tenant': tenant_data}, delete_choice, org_name)

def add_component(data, component_type, org_name):
    tenant = data['tenant']  
    if component_type == "VPC":
        region = questionary.select("Choose the region for the new VPC:", choices=['India', 'Japan', 'Germany', 'France']).ask()
        vpc_name = f"{tenant['name'][:2].lower()}_{region[:2].lower()}"
        tenant['vpcs'].append({
            'name': vpc_name,
            'vpc_state': 'requested'
        })
    elif component_type == "Subnet":
        vpc_name = questionary.select("Choose the VPC for the new subnet:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        cidr = questionary.text("Enter CIDR block for the new subnet:").ask()
        subnet_name = f"{vpc_name}_S{len(tenant['subnets'])+1}"  # Simple naming strategy
        tenant['subnets'].append({
            'name': subnet_name,
            'CIDR': cidr,
            'vpc': vpc_name,
            'subnet_state': 'requested'
        })
    elif component_type == "Container":
        vpc_name = questionary.select("Choose the VPC for the new container:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()
        container_name = f"{vpc_name.lower()}_container{len(tenant['containers'])+1}"
        chosen_subnets = questionary.checkbox("Select subnets for the container:", choices=[s['name'] for s in tenant['subnets'] if s['vpc'] == vpc_name]).ask()
        tenant['containers'].append({
            'name': container_name,
            'vpc': vpc_name,
            'subnets': chosen_subnets,
            'container_state': 'requested'
        })
    full_data = read_infra_config()  # Load the full structure
    for t in full_data['tenants']:
        if t['name'] == org_name:
            update_tenant(t, tenant)  # Update the tenant info in the full data
    save_infra_config(full_data)
    print(f"{component_type} added successfully.")
    print("Running state controller to deploy the Infra")
    controller = os.path.join(base_directory, 'southbound', 'infra_controller.py')
    time.sleep(1)
    run_script(controller, [tenant['name']])


def update_tenant(original, updated):
    # Helper function to update tenant info in the full list
    original.update(updated)

def delete_component(data, component_type, org_name):
    tenant = data['tenant']
    if component_type == "VPC":
        vpc_name = questionary.select("Select the VPC to delete:", choices=[vpc['name'] for vpc in tenant['vpcs']]).ask()        
        # Delete all subnets in the VPC
        remaining_subnets = [subnet for subnet in tenant['subnets'] if subnet['vpc'] != vpc_name]
        tenant['subnets'] = remaining_subnets
        # Delete all containers where all their subnets are no longer available
        tenant['containers'] = [container for container in tenant['containers'] if all(subnet in [s['name'] for s in remaining_subnets] for subnet in container['subnets'])]
        # Delete the VPC
        tenant['vpcs'] = [vpc for vpc in tenant['vpcs'] if vpc['name'] != vpc_name]
    elif component_type == "Subnet":
        subnet_name = questionary.select("Select the Subnet to delete:", choices=[subnet['name'] for subnet in tenant['subnets']]).ask()
        tenant['subnets'] = [subnet for subnet in tenant['subnets'] if subnet['name'] != subnet_name]
    elif component_type == "Container":
        container_name = questionary.select("Select the Container to delete:", choices=[container['name'] for container in tenant['containers']]).ask()
        tenant['containers'] = [container for container in tenant['containers'] if container['name'] != container_name]
    full_data = read_infra_config()  # Load the full structure
    for t in full_data['tenants']:
        if t['name'] == org_name:
            update_tenant(t, tenant)  # Update the tenant info in the full data
    save_infra_config(full_data)
    print(f"{component_type} deleted successfully.")

def run_script(script_path, args):
    try:
        subprocess.run(["python3", script_path, *args],  check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running script: {e}")

def main():
    print("Welcome to RapidServe Iaas")
    new_customer = questionary.select("Are you a new customer or looking for existing services?",
                                        choices=["New Customer", "Existing Services"]).ask()
    if new_customer.startswith("New Customer"):
        iaas_choice = questionary.select("Do you want to create a new Infrastructure?",choices=["yes", "no"]).ask()
        if iaas_choice.startswith("yes"):
            tenant_name = questionary.text("Enter your org name:").ask()
            print("Provide infromation for your Infrastructure")
            data = read_infra_config()
            current_tenants = data.get('tenants', [])
            new_infra = create_infra(current_tenants, tenant_name)
            save_infra_config(new_infra)
            print("Infrastructure saved to database")
            print("Running infra controller to deploy the Infra")
            controller = os.path.join(base_directory, 'southbound', 'infra_controller.py')
            time.sleep(1)
            run_script(controller, [tenant_name])

        elif iaas_choice.startswith("no"):
            print("Good Bye.")
        else:
            print("Invalid choice.")

    elif new_customer.startswith("Existing Services"):
        service_option = questionary.select("What service are you looking for?",
                                            choices=["Modify Infra", "Infra Status"]).ask()
        if service_option == "Modify Infra":
            print("Modify your Infrastructure.")
            modify_infra()
        elif service_option == "Infra Status":
            org_name = questionary.text("Enter your org name to fetch the status:").ask()
            tenant_data = fetch_tenant_info(org_name)
            print(yaml.dump({"tenant": tenant_data}, sort_keys=False))

if __name__ == "__main__":
    main()