#!/usr/bin/env bash
# Stop paying for the GPU.
#   bash stop.sh             # stop (keeps the disk, ~$6/month; start again later)
#   bash stop.sh terminate   # delete the instance and its disk
set -euo pipefail
export AWS_DEFAULT_REGION=${REGION:-us-east-1}
IDS=$(aws ec2 describe-instances --filters Name=tag:Name,Values=unbribable-referee \
  "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)
[ -n "$IDS" ] || { echo "Nothing to stop."; exit 0; }
if [ "${1:-}" = terminate ]; then
  aws ec2 terminate-instances --instance-ids $IDS --query 'TerminatingInstances[].CurrentState.Name' --output text
else
  aws ec2 stop-instances --instance-ids $IDS --query 'StoppingInstances[].CurrentState.Name' --output text
fi
