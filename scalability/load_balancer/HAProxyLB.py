import os
import subprocess

# HAProxy configuration parameters
HAPROXY_CONFIG_FILE = "/haproxy/haproxy.cfg"
BACKEND_SERVERS = [
    {"name": "web_server1", "address": "192.168.1.10", "port": 8080},
    {"name": "web_server2", "address": "192.168.1.11", "port": 8080},
    {"name": "web_server3", "address": "192.168.1.12", "port": 8080}
]
FRONTEND_PORT = 80
FRONTEND_WS_PORT = 8081

# Function to write HAProxy configuration file
def write_haproxy_config():
    config_lines = [
        "global",
        "    log /dev/log local0",
        "    log /dev/log local1 notice",
        "    chroot /var/lib/haproxy",
        "    stats socket /run/haproxy/admin.sock mode 660 level admin",
        "    stats timeout 30s",
        "    user haproxy",
        "    group haproxy",
        "    daemon",
        "    maxconn 4096",
        "",
        "defaults",
        "    log global",
        "    option httplog",
        "    option dontlognull",
        "    timeout connect 5000",
        "    timeout client 50000",
        "    timeout server 50000",
        "",
        f"frontend http_in",
        f"    bind *:{FRONTEND_PORT}",
        "    mode http",
        "    option httplog",
        "    default_backend servers_http",
        "",
        f"frontend ws_in",
        f"    bind *:{FRONTEND_WS_PORT}",
        "    mode tcp",
        "    option tcplog",
        "    default_backend servers_ws",
        "",
        "backend servers_http",
        "    mode http",
        "    balance roundrobin",
    ]

    for server in BACKEND_SERVERS:
        config_lines.append(f"    server {server['name']} {server['address']}:{server['port']} check")

    config_lines.extend([
        "",
        "backend servers_ws",
        "    mode tcp",
        "    balance roundrobin"
    ])

    for server in BACKEND_SERVERS:
        config_lines.append(f"    server {server['name']} {server['address']}:{server['port']} check")

    with open(HAPROXY_CONFIG_FILE, "w") as f:
        f.write("\n".join(config_lines))

# Function to restart HAProxy service
def restart_haproxy():
    try:
        subprocess.run(["systemctl", "restart", "haproxy"], check=True)
        print("HAProxy restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart HAProxy: {e}")

# Function to add a new backend server
def add_backend_server(name, address, port):
    BACKEND_SERVERS.append({"name": name, "address": address, "port": port})
    write_haproxy_config()
    restart_haproxy()

# Function to remove a backend server
def remove_backend_server(name):
    global BACKEND_SERVERS
    BACKEND_SERVERS = [s for s in BACKEND_SERVERS if s["name"] != name]
    write_haproxy_config()
    restart_haproxy()

# Function to show HAProxy status
def show_haproxy_status():
    try:
        result = subprocess.run(["haproxy", "-c", "-f", HAPROXY_CONFIG_FILE], capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error showing HAProxy status: {e}")

# Setup monitoring for the HAProxy using stats
def enable_haproxy_stats():
    config_lines = [
        "",
        "listen stats",
        "    bind *:8404",
        "    mode http",
        "    stats enable",
        "    stats uri /haproxy?stats",
        "    stats refresh 10s",
        "    stats show-node",
        "    stats auth admin:password"
    ]

    with open(HAPROXY_CONFIG_FILE, "a") as f:
        f.write("\n".join(config_lines))

    restart_haproxy()

# Start configuring HAProxy
def setup_haproxy():
    if not os.path.exists(HAPROXY_CONFIG_FILE):
        print(f"HAProxy configuration file not found at {HAPROXY_CONFIG_FILE}. Creating a new one.")
        write_haproxy_config()
    restart_haproxy()

# Load balancing testing
def test_load_balancer():
    print("Simulating requests to test load balancer...")
    try:
        for i in range(10):
            print(f"Request {i+1}:")
            result = subprocess.run(["curl", "-I", f"http://localhost:{FRONTEND_PORT}"], capture_output=True, text=True)
            print(result.stdout)
    except Exception as e:
        print(f"Error in load balancing test: {e}")

# Entry point for the script
if __name__ == "__main__":
    # Initial setup
    setup_haproxy()

    # Add/remove servers dynamically
    add_backend_server("web_server4", "192.168.1.13", 8080)
    remove_backend_server("web_server2")

    # Enable HAProxy stats page
    enable_haproxy_stats()

    # Show the current HAProxy status
    show_haproxy_status()

    # Test load balancing
    test_load_balancer()