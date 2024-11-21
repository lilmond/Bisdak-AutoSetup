import threading
import paramiko
import time

class Config:
    server_list = "serverlist.txt"
    server_key = "ovh1"
    threads = 10
    active_threads = 0

def remove_firewall(server_hostname: str):
    Config.active_threads += 1

    try:
        print(f"{server_hostname}: Deleting firewall")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(policy=paramiko.AutoAddPolicy())
        ssh_client.connect(hostname=server_hostname, port=22, username="root", key_filename=Config.server_key)

        for i in range(2, 6):
            stdin, stdout, stderr = ssh_client.exec_command(f"""sudo iptables -t nat -D PREROUTING -p tcp -d {server_hostname} --dport 3000{i} -j DNAT --to-destination 10.0.0.{i}:22
sudo iptables -D FORWARD -p tcp -d 10.0.0.{i} --dport 22 -m state --state NEW,ESTABLISHED,RELATED -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4""")
            stdout.read()

        print(f"{server_hostname}: Done deleting firewall")

        ssh_client.close()

    except Exception as e:
        print(f"remove firewall error: {e}")
        return
    
    finally:
        Config.active_threads -= 1

def main():
    with open(Config.server_list, "r") as file:
        node_list = [x.strip() for x in file.read().splitlines() if x.strip() and not x.strip().startswith("#")]
        file.close()
    
    for node in node_list:
        server_name, server_hostname = node.split(" ")

        while True:
            if Config.active_threads >= Config.threads:
                time.sleep(0.05)
                continue
            break

        threading.Thread(target=remove_firewall, args=[server_hostname], daemon=True).start()
    
    while True:
        if Config.active_threads <= 0:
            break
        time.sleep(0.05)

if __name__ == "__main__":
    main()
