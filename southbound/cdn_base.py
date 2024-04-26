import subprocess

def run_ansible_playbook(playbook_path, inventory_path, extra_vars):
    # Construct the extra variables string for the ansible-playbook command
    extra_vars_string = ' '.join([f"{key}='{value}'" for key, value in extra_vars.items()])

    try:
        # Prepare the command to run the Ansible playbook with extra variables
        command = [
            'ansible-playbook',
            playbook_path,
            '-i', inventory_path,
            '--extra-vars', extra_vars_string
        ]
        # Execute the command and stream the output
        print(f"Running playbook {playbook_path} with inventory {inventory_path} and variables {extra_vars}")
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Ansible playbook: {e}")
        print("Return code:", e.returncode)

def setup_logging():
    playbook_path = './implement_dns_logging.yml'
    inventory_path = './host_inventory.ini'
    logging_vars = {'some_variable': 'some_value'}
    run_ansible_playbook(playbook_path, inventory_path, logging_vars)

def main():
    # Define paths to your playbooks and inventories
    playbook_vpc = './deploy_vpc.yaml'
    playbook_dns = './create_dns_base_mh.yml'
    playbook_base_routes = './cdn_base_routes.yml'
    inventory_asia = './host_inventory_asia.ini'
    inventory_europe = './host_inventory_europe.ini'
    inventory_host = './host_inventory.ini'  # General host inventory for DNS playbook

    # Define VPC names for each inventory
    asia_vpc_names = ["rs_ba", "rs_th"]
    europe_vpc_names = ["rs_gr", "rs_ir"]

    #Run the VPC playbook for each inventory with the appropriate VPC names
    # for vpc_name in asia_vpc_names:
    #     run_ansible_playbook(playbook_vpc, inventory_asia, {'vpc_name': vpc_name})
    
    # for vpc_name in europe_vpc_names:
    #     run_ansible_playbook(playbook_vpc, inventory_europe, {'vpc_name': vpc_name})

    # #Run the DNS playbook using the host_inventory.ini
    # dns_vars = {'some_variable': 'some_value'}  # Define if there are specific variables for the DNS playbook
    # run_ansible_playbook(playbook_dns, inventory_host, dns_vars)

    setup_logging()

    #Run the base route creation playbook using the host_inventory.ini
    # route_vars = {'some_variable': 'some_value'} # Define if there are specific variables for the route creation playbook
    # run_ansible_playbook(playbook_base_routes, inventory_host, route_vars)

if __name__ == '__main__':
    main()