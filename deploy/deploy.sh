#!/bin/bash

# Simple deployment script for Key-Value Store
set -e

echo "Starting deployment..."

# Check requirements
if ! command -v ansible &> /dev/null; then
    echo "Error: Ansible not found. Install with: brew install ansible"
    exit 1
fi

# Setup SSH keys for all hosts
echo "Setting up SSH keys..."

# Extract host info from inventory (format: hostname ansible_host ansible_user)
host_info=$(grep -A 3 -E "(gateway|servers):" ../ansible/inventory.yaml | grep -E "(ansible_host|ansible_user)" | paste - - | awk '{print $2, $4}')

while read -r host user; do
    echo "  Setting up $user@$host..."
    if ssh-copy-id -i ~/.ssh/id_rsa.pub $user@$host 2>/dev/null; then
        echo "  SSH key copied successfully"
    else
        echo "  Manual setup for $user@$host..."
        scp ~/.ssh/id_rsa.pub $user@$host:~/id_rsa.pub || {
            echo "Error: Failed to copy SSH key to $user@$host"
            exit 1
        }
        ssh $user@$host "mkdir -p ~/.ssh && cat ~/id_rsa.pub >> ~/.ssh/authorized_keys && rm ~/id_rsa.pub" || {
            echo "Error: Failed to setup SSH key on $user@$host"
            exit 1
        }
    fi
done <<< "$host_info"

echo "SSH keys configured"

# Create ansible config
cat > ansible.cfg << 'EOF'
[defaults]
host_key_checking = False
inventory = ../ansible/inventory.yaml
remote_user = dbsoni
EOF

# Run deployment
echo "Running Ansible playbook..."
ansible-playbook -i ../ansible/inventory.yaml ../ansible/playbook.yaml

echo "Deployment complete!"
echo "Gateway: http://$(grep -A 3 "gateway:" ../ansible/inventory.yaml | grep "ansible_host:" | awk '{print $2}'):8000"