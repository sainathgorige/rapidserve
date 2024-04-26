import etcd3

# Create an instance of Etcd3Client
client = etcd3.client()

def retrieve_data_from_etcd(key):
    # Retrieve data associated with the given key
    value, _ = client.get(key)
    return value.decode() if value else None

if __name__ == "__main__":
    # Example key to retrieve data
    example_key = "hotstar" #One/subnet11/n111"

    # Retrieve data from etcd
    data_str = retrieve_data_from_etcd(example_key)

    if data_str:
        # Convert retrieved data string to dictionary
        data = eval(data_str)
        print("Retrieved data:")

        # Iterate through each VPC
        for vpc in data[example_key]['vpcs']:
            # Iterate through each subnet in the VPC
            for subnet in vpc['subnets']:
                cidr = subnet['CIDR']
                
                # Extract the first three octets from the CIDR
                first_three_octets = '.'.join(cidr.split('.')[:3])

                # Construct IP, DHCP start, and DHCP end using the first three octets
                ip = f"{first_three_octets}.1"
                dhcp_start = f"{first_three_octets}.2"
                dhcp_end = f"{first_three_octets}.254"

                # Add the new fields to the subnet
                subnet['ip'] = ip
                subnet['dhcp_start'] = dhcp_start
                subnet['dhcp_end'] = dhcp_end

                # Print the updated subnet information
                print(f"CIDR: {cidr}")
                print(f"  IP: {ip}")
                print(f"  DHCP Start: {dhcp_start}")
                print(f"  DHCP End: {dhcp_end}")
                print()
    else:
        print("Data not found for the given key.")

    print(data)



    # # Retrieve data from etcd
    # data = retrieve_data_from_etcd(example_key)

    # if data:
    #     print("Retrieved data:")
    #     print(data)
    # else:
    #     print("Data not found for the given key.")
