#!/bin/bash

# Simple deployment script for Key-Value Store
set -e

echo "Starting deployment..."

# Check requirements
if ! command -v ansible &> /dev/null; then
    echo "Error: Ansible not found. Install with: brew install ansible"
    exit 1
fi

# Check if inventory file exists
if [ ! -f ./ansible/inventory.yaml ]; then
    echo "Error: Inventory file not found at ./ansible/inventory.yaml"
    exit 1
fi

# Check if playbook file exists
if [ ! -f ./ansible/playbook.yaml ]; then
    echo "Error: Playbook file not found at ./ansible/playbook.yaml"
    exit 1
fi

# Check if SSH key exists
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    echo "Error: SSH public key not found at ~/.ssh/id_rsa.pub"
    echo "Please generate SSH keys first with: ssh-keygen -t rsa -b 4096 -C 'your_email@example.com'"
    exit 1
fi

# Setup SSH keys for all hosts
echo "Setting up SSH keys..."

# Extract host info from inventory (format: ansible_host ansible_user)
host_info=$(grep -A 5 -E "(gateway|servers):" ./ansible/inventory.yaml | grep -E "ansible_host:" | awk '{print $2}' | while read host; do
    user=$(grep -A 5 -B 5 "ansible_host: $host" ./ansible/inventory.yaml | grep "ansible_user:" | awk '{print $2}')
    echo "$host $user"
done)

while read -r host user; do
    if [ -n "$host" ] && [ -n "$user" ]; then
        echo "  Setting up $user@$host..."
        
        # Test if SSH key is already configured
        if ssh -o PasswordAuthentication=no -o ConnectTimeout=10 $user@$host "echo 'SSH key already configured'" 2>/dev/null; then
            echo "  SSH key already configured for $user@$host"
            continue
        fi
        
        # Try ssh-copy-id first
        if ssh-copy-id -i ~/.ssh/id_rsa.pub $user@$host 2>/dev/null; then
            echo "  SSH key copied successfully"
        else
            echo "  Manual setup for $user@$host..."
            echo "  You will need to enter the password for $user@$host"
            scp ~/.ssh/id_rsa.pub $user@$host:~/id_rsa.pub || {
                echo "Error: Failed to copy SSH key to $user@$host"
                echo "Please ensure you can SSH to $user@$host manually"
                exit 1
            }
            ssh $user@$host "mkdir -p ~/.ssh && cat ~/id_rsa.pub >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && rm ~/id_rsa.pub" || {
                echo "Error: Failed to setup SSH key on $user@$host"
                exit 1
            }
        fi
    fi
done <<< "$host_info"

echo "SSH keys configured"

# Create ansible config
cat > ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
inventory = ./ansible/inventory.yaml
remote_user = dbsoni
EOF

# Run deployment
echo "Running Ansible playbook..."
if ansible-playbook -i ./ansible/inventory.yaml ./ansible/playbook.yaml; then
    echo "Deployment complete!"
    gateway_ip=$(grep -A 3 "gateway:" ../ansible/inventory.yaml | grep "ansible_host:" | awk '{print $2}')
    echo "Gateway: http://$gateway_ip:8000"
    echo ""
    echo "You can test the deployment with:"
    echo "  curl http://$gateway_ip:8000/health"
    echo "  curl -X POST http://$gateway_ip:8000/set -H 'Content-Type: application/json' -d '{\"key\": \"test\", \"value\": \"hello\"}'"
    echo "  curl http://$gateway_ip:8000/get/test"
else
    echo "Deployment failed! Check the output above for errors."
    exit 1
fi