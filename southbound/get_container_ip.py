import yaml
import sys

def get_next_ip(cidr):
    base_ip = cidr.split('/')[0].rsplit('.', 1)[0]
    last_octet = int(cidr.split('.')[3].split('/')[0]) + 3  # Start from .3 as per your logic
    return f"{base_ip}.{last_octet}"

if __name__ == "__main__":
    vpc_name = sys.argv[1]
    config_path = "/home/vmadm/demo/RapidServe/config.yaml"  # Adjust the path as necessary

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    for tenant in config['tenants']:
        for vpc in tenant['vpcs']:
            if vpc['name'] == vpc_name:
                for subnet in tenant['subnets']:
                    cidr = subnet['CIDR']
                    print(get_next_ip(cidr))
                    break
                break
