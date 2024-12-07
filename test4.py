length = 12

evernode_port = 42000
start_ssh_port = 30002

for i in range(2, length + 2):
    vps_ip = f"10.0.0.{i}"
    peer_port = evernode_port
    user_port = evernode_port + 50
    tcp_port = evernode_port + 100
    udp_port = evernode_port + 150
    ssh_port = start_ssh_port
    start_ssh_port += 1

    evernode_port += 1000

    print(f"VPS IP: {vps_ip}\nPeer Port: {peer_port}\nUser Port: {user_port}\nTCP Port: {tcp_port}\nUDP Port: {udp_port}\nSSH Port: {ssh_port}\n\n")
