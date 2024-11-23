# Version: 1.0.1

import threading
import paramiko
import time

class SetupConfig:
    NODE_LIST = "./serverlist.txt"
    KEY = "ovh1"
    SETUP_PASSWORD = "my cool ssh password"

class AppConfig:
    THREADS = 10
    ACTIVE_THREADS = 0

def setup_password(hostname: str):
    AppConfig.ACTIVE_THREADS += 1

    try:
        print(f"{hostname}: Setting up password")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, port=22, username="root", key_filename=SetupConfig.KEY)

        stdin, stdout, stderr = ssh_client.exec_command("passwd")
        stdin.write(f"{SetupConfig.SETUP_PASSWORD}\n")
        stdin.write(f"{SetupConfig.SETUP_PASSWORD}\n")

        ssh_client.close()

        print(f"{hostname}: Done setting up password")

    except Exception as e:
        print(f"setup password error: {e}")
        return
    
    finally:
        AppConfig.ACTIVE_THREADS -= 1

def setup_nginx(hostname: str, subdomains: list):
    AppConfig.ACTIVE_THREADS += 1

    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, port=22, username="root", key_filename=SetupConfig.KEY)

        stdin, stdout, stderr = ssh_client.exec_command("apt install nginx -y")
        stdout.read()

        for i, subdomain in enumerate(subdomains, start=2):
            loc1 = f"{hostname}: /etc/nginx/sites-enabled/{subdomain}.conf"

            stdin, stdout, stderr = ssh_client.exec_command(f"ls {loc1} >/dev/null 2>&1 && echo exists || echo not_exists")
            if not stdout.read().decode().strip() == "exists":
                print(f"{hostname}: Writing: {subdomain}.conf -> 10.0.0.{i}")

                stdin, stdout, stderr = ssh_client.exec_command(f"echo \"server {{\n        listen 80;\n    server_name {subdomain};\n      \n      location / {{\n         proxy_pass http://10.0.0.{i};\n         proxy_set_header Host \\$host;\n                proxy_set_header X-Real-IP \\$remote_addr;\n            proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;\n                proxy_set_header X-Forwarded-Proto \\$scheme;\n }}\n}}\" > /etc/nginx/sites-enabled/{subdomain}.conf")
                stdout.read()

                print(f"{hostname}: Done writing {subdomain}.conf -> 10.0.0.{i}")

                stdin, stdout, stderr = ssh_client.exec_command(f"ln -s {loc1} /etc/nginx/sites-available/")
                stdout.read()
            else:
                print(f"{hostname}: {loc1} already exists")
                continue
        
        stdin, stdout, stderr = ssh_client.exec_command("systemctl restart nginx.service")
        stdout.read()
        
        ssh_client.close()

        print(f"{hostname}: Done setting up nginx")

    except Exception as e:
        print(f"setup nginx error: {e}")
        return
    
    finally:
        AppConfig.ACTIVE_THREADS -= 1

def setup_firewall(hostname: str, length: int):
    AppConfig.ACTIVE_THREADS += 1

    try:
        print(f"{hostname}: Setting up firewall")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=hostname, port=22, username="root", key_filename=SetupConfig.KEY)

        stdin, stdout, stderr = ssh_client.exec_command("sudo DEBIAN_FRONTEND=noninteractive apt install iptables-persistent -y")
        stdout.read()

        stdin, stdout, stderr = ssh_client.exec_command("echo net.ipv4.ip_forward=1 > /etc/sysctl.conf")
        stdout.read()

        stdin, stdout, stderr = ssh_client.exec_command("""sysctl -p
# Check if the MASQUERADE rule exists in POSTROUTING chain
if ! sudo iptables -t nat -C POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE 2>/dev/null; then
    # Add the rule if it doesn't exist
    sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o vmbr0 -j MASQUERADE
    echo "MASQUERADE rule added."
else
    echo "MASQUERADE rule already exists, skipping."
fi

# Check if the FORWARD rule (RELATED,ESTABLISHED) exists
if ! sudo iptables -C FORWARD -i vmbr0 -o vmbr1 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null; then
    # Add the rule if it doesn't exist
    sudo iptables -A FORWARD -i vmbr0 -o vmbr1 -m state --state RELATED,ESTABLISHED -j ACCEPT
    echo "RELATED,ESTABLISHED FORWARD rule added."
else
    echo "RELATED,ESTABLISHED FORWARD rule already exists, skipping."
fi

# Check if the FORWARD rule (general ACCEPT) exists
if ! sudo iptables -C FORWARD -i vmbr1 -o vmbr0 -j ACCEPT 2>/dev/null; then
    # Add the rule if it doesn't exist
    sudo iptables -A FORWARD -i vmbr1 -o vmbr0 -j ACCEPT
    echo "ACCEPT FORWARD rule added."
else
    echo "ACCEPT FORWARD rule already exists, skipping."
fi
""")
        stdout.read()

        for i in range(2, length + 2):
            ovh_ip = hostname
            vps_ip = f"10.0.0.{i}"
            peer_port = int(f"4{i}000")
            user_port = int(f"4{i}050")
            tcp_port = int(f"4{i}100")
            udp_port = int(f"4{i}150")
            ssh_port = int(f"3000{i}")

            stdin, stdout, stderr = ssh_client.exec_command(f"""# Check and add the SNAT rule for peer_port range
if ! sudo iptables -t nat -C POSTROUTING -d {vps_ip} -p tcp --dport {peer_port}:{peer_port + 7} -j SNAT --to-source {ovh_ip} 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -d {vps_ip} -p tcp --dport {peer_port}:{peer_port + 7} -j SNAT --to-source {ovh_ip}
    echo "SNAT rule for peer_port added."
else
    echo "SNAT rule for peer_port already exists, skipping."
fi

# Check and add the SNAT rule for user_port range
if ! sudo iptables -t nat -C POSTROUTING -d {vps_ip} -p tcp --dport {user_port}:{user_port + 7} -j SNAT --to-source {ovh_ip} 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -d {vps_ip} -p tcp --dport {user_port}:{user_port + 7} -j SNAT --to-source {ovh_ip}
    echo "SNAT rule for user_port added."
else
    echo "SNAT rule for user_port already exists, skipping."
fi

# Check and add the SNAT rule for tcp_port range
if ! sudo iptables -t nat -C POSTROUTING -d {vps_ip} -p tcp --dport {tcp_port}:{tcp_port + 13} -j SNAT --to-source {ovh_ip} 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -d {vps_ip} -p tcp --dport {tcp_port}:{tcp_port + 13} -j SNAT --to-source {ovh_ip}
    echo "SNAT rule for tcp_port added."
else
    echo "SNAT rule for tcp_port already exists, skipping."
fi

# Check and add the SNAT rule for udp_port range
if ! sudo iptables -t nat -C POSTROUTING -d {vps_ip} -p udp --dport {udp_port}:{udp_port + 13} -j SNAT --to-source {ovh_ip} 2>/dev/null; then
    sudo iptables -t nat -A POSTROUTING -d {vps_ip} -p udp --dport {udp_port}:{udp_port + 13} -j SNAT --to-source {ovh_ip}
    echo "SNAT rule for udp_port added."
else
    echo "SNAT rule for udp_port already exists, skipping."
fi

# Check and add the DNAT rule for peer_port range
if ! sudo iptables -t nat -C PREROUTING -d {ovh_ip} -p tcp --dport {peer_port}:{peer_port + 7} -j DNAT --to-destination {vps_ip} 2>/dev/null; then
    sudo iptables -t nat -A PREROUTING -d {ovh_ip} -p tcp --dport {peer_port}:{peer_port + 7} -j DNAT --to-destination {vps_ip}
    echo "DNAT rule for peer_port added."
else
    echo "DNAT rule for peer_port already exists, skipping."
fi

# Check and add the DNAT rule for user_port range
if ! sudo iptables -t nat -C PREROUTING -d {ovh_ip} -p tcp --dport {user_port}:{user_port + 7} -j DNAT --to-destination {vps_ip} 2>/dev/null; then
    sudo iptables -t nat -A PREROUTING -d {ovh_ip} -p tcp --dport {user_port}:{user_port + 7} -j DNAT --to-destination {vps_ip}
    echo "DNAT rule for user_port added."
else
    echo "DNAT rule for user_port already exists, skipping."
fi

# Check and add the DNAT rule for tcp_port range
if ! sudo iptables -t nat -C PREROUTING -d {ovh_ip} -p tcp --dport {tcp_port}:{tcp_port + 13} -j DNAT --to-destination {vps_ip} 2>/dev/null; then
    sudo iptables -t nat -A PREROUTING -d {ovh_ip} -p tcp --dport {tcp_port}:{tcp_port + 13} -j DNAT --to-destination {vps_ip}
    echo "DNAT rule for tcp_port added."
else
    echo "DNAT rule for tcp_port already exists, skipping."
fi

# Check and add the DNAT rule for udp_port range
if ! sudo iptables -t nat -C PREROUTING -d {ovh_ip} -p udp --dport {udp_port}:{udp_port + 13} -j DNAT --to-destination {vps_ip} 2>/dev/null; then
    sudo iptables -t nat -A PREROUTING -d {ovh_ip} -p udp --dport {udp_port}:{udp_port + 13} -j DNAT --to-destination {vps_ip}
    echo "DNAT rule for udp_port added."
else
    echo "DNAT rule for udp_port already exists, skipping."
fi

# Check and add the DNAT rule for SSH
if ! sudo iptables -t nat -C PREROUTING -p tcp -d {ovh_ip} --dport {ssh_port} -j DNAT --to-destination {vps_ip}:22 2>/dev/null; then
    sudo iptables -t nat -A PREROUTING -p tcp -d {ovh_ip} --dport {ssh_port} -j DNAT --to-destination {vps_ip}:22
    echo "DNAT rule for SSH added."
else
    echo "DNAT rule for SSH already exists, skipping."
fi

# Check and add the FORWARD rule for SSH
if ! sudo iptables -C FORWARD -p tcp -d {vps_ip} --dport 22 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT 2>/dev/null; then
    sudo iptables -A FORWARD -p tcp -d {vps_ip} --dport 22 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
    echo "FORWARD rule for SSH added."
else
    echo "FORWARD rule for SSH already exists, skipping."
fi

sudo iptables-save > /etc/iptables/rules.v4""")
            
        ssh_client.close()

        print(f"{hostname}: Done setting up firewall")

    except Exception as e:
        print(f"setup firewall error: {e}")
        return
    
    finally:
        AppConfig.ACTIVE_THREADS -= 1
    

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

def wait_threads():
    while True:
        time.sleep(0.05)
        if AppConfig.ACTIVE_THREADS <= 0:
            break

def main():
    with open(SetupConfig.NODE_LIST, "r") as file:
        node_list = [x.strip() for x in file.read().splitlines() if x.strip() and not x.strip().startswith("#")]
        file.close()
    
    for node in node_list:
        server_name, server_hostname = node.split(" ")

        while True:
            if AppConfig.ACTIVE_THREADS >= AppConfig.THREADS:
                time.sleep(0.05)
                continue

            threading.Thread(target=setup_password, args=[server_hostname], daemon=True).start()
            break

    wait_threads()

    for node in node_list:
        server_name, server_hostname = node.split(" ")

        while True:
            if AppConfig.ACTIVE_THREADS >= AppConfig.THREADS:
                time.sleep(0.05)
                continue

            subdomains = servername_to_subdomains(server_name=server_name)
            threading.Thread(target=setup_nginx, args=[server_hostname, subdomains], daemon=True).start()
            break

    wait_threads()

    for node in node_list:
        server_name, server_hostname = node.split(" ")
        subdomains = servername_to_subdomains(server_name=server_name)

        while True:
            if AppConfig.ACTIVE_THREADS >= AppConfig.THREADS:
                time.sleep(0.05)
                continue
            threading.Thread(target=setup_firewall, args=[server_hostname, len(subdomains)], daemon=True).start()
            break

    wait_threads()

if __name__ == "__main__":
    main()
