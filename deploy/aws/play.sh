#!/usr/bin/env bash
# Open the game on the instance, in this CloudShell terminal (SSM session, no SSH keys).
#   bash play.sh                 # referee on
#   bash play.sh --no-referee    # referee off
#   bash play.sh shell           # a plain shell on the instance
set -euo pipefail
export AWS_DEFAULT_REGION=${REGION:-us-east-1}
IID=$(aws ec2 describe-instances --filters Name=tag:Name,Values=unbribable-referee Name=instance-state-name,Values=running \
  --query 'Reservations[0].Instances[0].InstanceId' --output text)
[ "$IID" != None ] || { echo "No running unbribable-referee instance."; exit 1; }
if [ "${1:-}" = shell ]; then
  exec aws ssm start-session --target "$IID" --document-name AWS-StartInteractiveCommand \
    --parameters command="sudo -iu ubuntu"
fi
exec aws ssm start-session --target "$IID" --document-name AWS-StartInteractiveCommand \
  --parameters command="sudo -iu ubuntu bash -lc 'cd ~/unbribable-referee && AWS_REGION=us-east-1 .venv/bin/python -m referee.game --seed 7 $*'"
