import yaml
import etcd3

# Create an instance of Etcd3Client
client = etcd3.client()

def store_yaml_data_to_etcd(filename, client):
    with open(filename, 'r') as file:
        data = yaml.safe_load(file)

    for tenant in data['tenants']:
        tenant_name = tenant['name']
        tenant_data = {tenant_name: tenant}
        client.put(tenant_name, str(tenant_data))

if __name__ == "__main__":
    # Store YAML data in etcd
    store_yaml_data_to_etcd('customer_input_infra.yaml', client)
    # store_yaml_data_to_etcd('../config.yaml', client)
