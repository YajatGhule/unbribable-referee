#!/bin/bash
# Runs once as root when the instance first boots (EC2 user data). Installs the game and
# serves Strands Decider 2B as a systemd service. Bedrock access comes from the instance's
# IAM role: there are no keys on this machine.
set -eux
exec > /var/log/referee-setup.log 2>&1

sudo -iu ubuntu bash -lc '
set -eux
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone -b __REF__ https://github.com/YajatGhule/unbribable-referee.git ~/unbribable-referee
cd ~/unbribable-referee
~/.local/bin/uv venv --python 3.12 .venv
if nvidia-smi; then
  ~/.local/bin/uv pip install --python .venv/bin/python "strands-decider[cuda]" "strands-agents>=1.61" rich boto3 pytest
else
  ~/.local/bin/uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
  ~/.local/bin/uv pip install --python .venv/bin/python "strands-decider[cpu]" "strands-agents>=1.61" rich boto3 pytest
fi
echo "export AWS_REGION=us-east-1" >> ~/.bashrc
echo "cd ~/unbribable-referee" >> ~/.bashrc
'

DEVICE=cpu; nvidia-smi >/dev/null 2>&1 && DEVICE=cuda
cat > /etc/systemd/system/decider.service <<EOF
[Unit]
Description=Strands Decider 2B server
After=network-online.target
Wants=network-online.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/unbribable-referee
ExecStart=/home/ubuntu/unbribable-referee/.venv/bin/strands-decider serve StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 --port 8099 --device $DEVICE
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now decider

for i in $(seq 1 120); do
  curl -sf http://127.0.0.1:8099/health && break
  sleep 10
done
touch /var/log/referee-ready
