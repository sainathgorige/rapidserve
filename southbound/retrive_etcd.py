import etcd3
import sys
import ipaddress

# Create an instance of Etcd3Client
client = etcd3.client()

def retrieve_data_from_etcd(key):
    # Retrieve data associated with the given key
    value, _ = client.get(key)
    return value.decode() if value else None

if __name__ == "__main__":
    # Example key to retrieve data
    tenant_name = sys.argv[1] #"netflix" #One/subnet11/n111"

    # Retrieve data from etcd
    data_str = retrieve_data_from_etcd(tenant_name)

    if data_str:
        # Convert retrieved data string to dictionary
        data = eval(data_str)
        # # print("Retrieved data: ", data)

        # # Iterate through each VPC
        # for vpc in data[tenant_name]['vpcs']:
        #     # Iterate through each subnet in the VPC
        #     for subnet in vpc['subnets']:
        #         cidr = subnet['CIDR']
                
        #         # Extract the network address and prefix length from the CIDR
        #         network = ipaddress.ip_network(cidr)
        #         ip = str(network.network_address + 1)  # IP is the first address in the CIDR block
        #         dhcp_start = str(network.network_address + 2)  # DHCP start is the second address
        #         dhcp_end = str(network.broadcast_address - 1)  # DHCP end is the last but one address

        #         # Add the new fields to the subnet
        #         subnet['ip'] = ip
        #         subnet['dhcp_start'] = dhcp_start
        #         subnet['dhcp_end'] = dhcp_end

        # # print("%s data is" % tenant_name)
        print("Updated data:")
        print(data)
    else:
        print("Data not found for the given key.")