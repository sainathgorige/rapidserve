import etcd3
import subprocess
from ansible_runner import run
import yaml
import sys
import ipaddress

client = etcd3.client()

# Function to run Ansible playbook
def run_playbook(filename, vars_dict):
    config = {
        'private_data_dir': './',
        'playbook': filename,
        'extravars': vars_dict
    }
    result = run(**config)
    return result

def create_subnet_resources(tenant_name, vars_dict):
    result = run_playbook('deploy_subnet.yaml', vars_dict)
    return result

def create_vpc_resources(tenant_name, vars_dict):
    result = run_playbook('deploy_vpc.yaml', vars_dict)
    return result

def create_VM(tenant_name, vars_dict):
    
    result = run_playbook('create_VM.yaml', vars_dict)
    return result


def create_cdn_resources(tenant_name, tenant_data):
    result = run_playbook('deploy_cdn.yaml', {'tenant_name': [tenant_name],
                                                'tenant_data': tenant_data})
    return result

def create_dns_resources(tenant_name, tenant_data):
    result = run_playbook('deploy_dns_final.yaml', {'tenant_name': [tenant_name],
                                                'tenant_data': tenant_data})
    return result

def create_container(tenant_name, vars_dict):
    result = run_playbook('deploy_con.yaml', vars_dict)
    return result

def check_and_update_subnet_state(tenant_name, tenant_data):
    for subnet in tenant_data[tenant_name]['subnets']:
        if subnet['subnet_state'] == 'requested':
            vars_dict = {'tenant_name': tenant_name,
                         'tenant_data': tenant_data,
                         'subnet_name': subnet['name'],
                         'vpc_name': subnet['vpc'],
                         'subnet_CIDR': subnet['CIDR'],
                         'ip': subnet['ip'],
                         'dhcp_start': subnet['dhcp_start'],
                         'dhcp_end': subnet['dhcp_end']}                             
            result = create_subnet_resources(tenant_name, vars_dict)

            if result.rc == 0:
                subnet['subnet_state'] = 'active'
                client.put(tenant_name, str(tenant_data))
                # break
            else:
                print("Error occurred while creating vpc resources.")
                sys.exit(1)

def check_and_update_vpc_state(tenant_name, tenant_data):
    for vpc in tenant_data[tenant_name]['vpcs']:
        if vpc['vpc_state'] == 'requested':
            vars_dict = {'tenant_name': tenant_name,
                         'tenant_data': tenant_data,
                         'vpc_name': vpc['name']}                            
            result = create_vpc_resources(tenant_name, vars_dict)

            if result.rc == 0:
                vpc['vpc_state'] = 'active'
                client.put(tenant_name, str(tenant_data))
                # break
            else:
                print("Error occurred while creating vpc resources.")
                sys.exit(1)

def check_and_update_cdn_with_dns(tenant_name, tenant_data):
    if  tenant_data[tenant_name]['cdn']['state'] == 'requested':
        result = create_cdn_resources(tenant_name, tenant_data)
        
        if result.rc == 0:
            result = create_dns_resources(tenant_name, tenant_data)
            if result.rc == 0:
                tenant_data[tenant_name]['cdn']['state'] = 'active'
                client.put(tenant_name, str(tenant_data))
            else:
                print("Error occurred while creating dns resources.")
                sys.exit(1)
        else:
            print("Error occurred while creating cdn resources.")
            sys.exit(1)


def check_and_create_VM(tenant_name, tenant_data):
    # for vpc in tenant_data[tenant_name]['vpcs']:
    for VM in tenant_data[tenant_name]['VMs']:
        if VM['VM_state'] == 'requested':
            vars_dict = {'tenant_name': [tenant_name],
                        'vm_name': VM['name'],
                        'vm_disk_size': VM['disk_size'],
                        'vm_ram': VM['RAM_size'],
                        'vm_cpus': VM['CPUs'],
                        'vm_network_bridges': VM['subnets'],
                        'origin_server_ip': '192.168.5.2'
                        }
            result = create_VM(tenant_name, vars_dict)

            if result.rc == 0:
                VM['VM_state'] = 'active'
                client.put(tenant_name, str(tenant_data))
            else:
                print("Error occurred while creating VM resources.")
                sys.exit(1)

def check_and_create_containers(tenant_name, tenant_data):
    for container in tenant_data[tenant_name]['containers']:
        if container['container_state'] == 'requested':
            vars_dict = {'tenant_name': [tenant_name],
                         'container_num': container['number'],
                         'server_type': "edge",
                         'vpc_name': container['vpc'],
                        #  'origin_vm_ip': container['origin_server_ip'],
                         'bridges': container['subnets']
                        #  'origin_server_ip': '192.168.5.2'
                        }
            result = create_container(tenant_name, vars_dict)

            if result.rc == 0:
                container['container_state'] = 'active'
                client.put(tenant_name, str(tenant_data))
            else:
                print("Error occurred while creating container resources.")
                sys.exit(1)

def calculate_ip(tenant_name, tenant_data):
    # for vpc in tenant_data[tenant_name]['vpcs']:
    #     # Iterate through each subnet in the VPC
    for subnet in tenant_data[tenant_name]['subnets']:
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
    client.put(tenant_name, str(tenant_data))
    return tenant_data

    # print("%s tenant_data is" % tenant_name)
    # print("Updated tenant_data:")
    # print(tenant_data)


if __name__ == "__main__":

    # tenant_name = "netflix" 
    tenant_name = sys.argv[1]

    # Retrieve data from etcd
    value, _ = client.get(tenant_name)
    if value:
        tenant_data = eval(value.decode())

        tenant_data = calculate_ip(tenant_name, tenant_data)


        print("tenant_data = ", tenant_data)
        

        check_and_update_vpc_state(tenant_name, tenant_data)

        check_and_update_subnet_state(tenant_name, tenant_data)

        check_and_create_containers(tenant_name, tenant_data)

        # check_and_create_VM(tenant_name, tenant_data)
        
        # check_and_update_cdn_with_dns(tenant_name, tenant_data)  
    else:
        print(f"No data found for key: {tenant_name}")


