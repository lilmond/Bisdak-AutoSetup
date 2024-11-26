# Version: 1.1.0

SERVER_LIST = "serverlist.txt"
OUTPUT_FILE = "nodes_info.txt"

def get_num_domain(num: int):
    x = 0

    while True:
        if num <= x + 50:
            domain_num = f"{x + 1}-{x + 50}"
            break

        x += 50

    domain = f"bisdaknode{domain_num}.ovh"

    return domain

def servername_to_subdomains(server_name: str):
    x1, x2 = server_name.split("-")
    n1 = int(x1[1:])
    n2 = int(x2[1:])

    subdomains = []

    i = n1
    while True:
        domain = get_num_domain(i)
        subdomains.append(f"n{i}.{domain}")

        if i == n2:
            break

        i += 1
    
    return subdomains

def main():
    with open(SERVER_LIST, "r") as file:
        node_list = [x.strip() for x in file.read().splitlines() if x.strip() and not x.strip().startswith("#")]
        file.close()

    log_text = ""

    for node in node_list:
        server_name, server_hostname = node.split(" ")

        subdomains = servername_to_subdomains(server_name=server_name)
        
        evernode_port = 42000
        start_ssh_port = 30002

        log_text += f"{server_name}\n"
        for i, subdomain in enumerate(subdomains, start=2):
            vps_ip = f"10.0.0.{i}"
            peer_port = evernode_port
            user_port = evernode_port + 50
            tcp_port = evernode_port + 100
            udp_port = evernode_port + 150
            ssh_port = start_ssh_port
            start_ssh_port += 1
            evernode_port += 1000

            log_text += f"{subdomain}\nVPS IP: 10.0.0.{i}\nSSH Port: {ssh_port}\nPeer Port: {peer_port}\nUser Port: {user_port}\nGeneral TCP Port: {tcp_port}\nUDP Port: {udp_port}\n\n"
        log_text += "\n"
    
    with open(OUTPUT_FILE, "w") as file:
        file.write(log_text)
        file.close()    

if __name__ == "__main__":
    main()
