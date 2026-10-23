#!/usr/bin/env bash
# Is the instance up, set up, and serving the decider? Run in CloudShell.
set -euo pipefail
export AWS_DEFAULT_REGION=${REGION:-us-east-1}
ID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=unbribable-referee \
  "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,InstanceType]' --output text)
echo "instance: ${ID:-none}"
[ -n "$ID" ] || exit 0
IID=${ID%%[[:space:]]*}
CMD=$(aws ssm send-command --instance-ids "$IID" --document-name AWS-RunShellScript \
  --parameters 'commands=["test -f /var/log/referee-ready && echo SETUP=done || echo SETUP=running","tail -3 /var/log/referee-setup.log","curl -s http://127.0.0.1:8099/health || echo decider: not up yet"]' \
  --query Command.CommandId --output text 2>/dev/null) || { echo "SSM agent not registered yet; try again in a minute."; exit 0; }
sleep 4
aws ssm get-command-invocation --command-id "$CMD" --instance-id "$IID" --query StandardOutputContent --output text
