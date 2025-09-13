# Key-Value Store Deployment Guide

This guide will help you deploy the Key-Value Store application across multiple Ubuntu servers using Ansible.

## Prerequisites

Before starting, ensure you have:

1. **Three Ubuntu servers**
   - 1 server for API Gateway
   - 2 servers for backend storage
2. **SSH access** to all servers with sudo privileges
3. **Ansible installed** on your local machine
4. **SSH keys configured** for passwordless authentication

## Quick Deployment

1. **Navigate to the ansible directory:**
   ```bash
   cd ansible
   ```

2. **Update the hosts file:**
   Edit `hosts.yaml` and replace the IP addresses with your actual server IPs:
   ```yaml
   gateway-server:
     ansible_host: YOUR_GATEWAY_IP    # Replace with your gateway IP
   server-1:
     ansible_host: YOUR_SERVER1_IP    # Replace with your first server IP  
   server-2:
     ansible_host: YOUR_SERVER2_IP    # Replace with your second server IP
   ```

3. **Deploy the application:**
   ```bash
   ansible-playbook -i hosts.yaml playbook.yaml
   ```

That's it! The playbook will handle everything automatically.

## What Gets Deployed

### API Gateway Server
- **Port**: 8000 (exposed to internet)
- **Function**: Routes requests to backend servers
- **Location**: `/opt/kv-store`

### Backend Servers (2 instances)
- **Port**: 8080 (internal only)
- **Function**: Store and retrieve key-value pairs
- **Data**: Persistent storage in `/opt/kv-store/data`

## Testing Your Deployment

After deployment, test your key-value store:

```bash
# Replace GATEWAY_IP with your gateway server IP

# Health check
curl http://GATEWAY_IP:8000/health

# Store a value
curl -X POST http://GATEWAY_IP:8000/set \
  -H "Content-Type: application/json" \
  -d '{"key": "hello", "value": "world"}'

# Retrieve the value
curl http://GATEWAY_IP:8000/get/hello

# Delete a key
curl -X DELETE http://GATEWAY_IP:8000/delete/hello
```

## Architecture Overview

```
Internet
    ↓
API Gateway (Port 8000)
    ↓
Backend Server 1 (Port 8080)
```

## Troubleshooting

### Common Issues

1. **"Permission denied (publickey)"**
   - Check SSH key path in hosts.yaml
   - Verify SSH key is added to ssh-agent: `ssh-add ~/.ssh/id_rsa`

2. **"Connection refused"**
   - Verify server IP addresses
   - Check firewall settings
   - Ensure SSH service is running

3. **"Docker installation failed"**
   - Check internet connectivity on target servers
   - Verify Ubuntu version (18.04+)

### Useful Commands

```bash
# Check server connectivity
ansible all -i hosts.yaml -m ping

# View running containers
ansible all -i hosts.yaml -m shell -a "docker ps"

# Check service logs
ansible all -i hosts.yaml -m shell -a "docker logs kv-store_api-gateway_1"
ansible all -i hosts.yaml -m shell -a "docker logs kv-store_kv-store-server_1"

# Restart services
ansible all -i hosts.yaml -m shell -a "docker-compose -f /opt/kv-store/docker-compose.yml restart"
```

## Security Notes

- Only port 8000 (API Gateway) should be exposed to the internet
- Backend servers (port 8080) should only be accessible from the gateway
- Use strong SSH keys and consider key rotation
- Keep Ubuntu systems updated with security patches

## Cleanup

To remove the deployment:

```bash
ansible all -i hosts.yaml -m shell -a "docker-compose -f /opt/kv-store/docker-compose.yml down -v"
ansible all -i hosts.yaml -m shell -a "rm -rf /opt/kv-store"
```

## File Structure

```
ansible/
├── hosts.yaml        # Server IP addresses
└── playbook.yaml     # Deployment process
```

Simple and clean! Just update the IPs and run the playbook.