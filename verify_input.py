import yaml
import ipaddress

def verify_parameters(file_path):
    error_messages = []

    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)

    vpc_names = set()  # Set to track VPC names across all tenants

    for tenant in data.get('tenants', []):
        tenant_name = tenant.get('name', '')
        for vpc in tenant.get('vpcs', []):
            vpc_name = vpc.get('name', '')
            if vpc_name in vpc_names:
                error_messages.append(f"[E] Duplicate VPC name '{vpc_name}' in tenant '{tenant_name}'")
            else:
                vpc_names.add(vpc_name)

            subnet_names = set()
            for subnet in vpc.get('subnets', []):
                if subnet['name'] in subnet_names:
                    error_messages.append(f"[E] Duplicate subnet name '{subnet['name']}' in VPC '{vpc_name}'")
                else:
                    subnet_names.add(subnet['name'])

    if error_messages:
        for error in error_messages:
            print(error)
    else:
        print("No errors found.")
if __name__ == "__main__":
    verify_parameters("customer_input_infra.yaml")

