#!/usr/bin/env bash
# Launch the whole stack on one EC2 GPU instance in your account. Run it in AWS CloudShell.
#
#   curl -fsSL https://raw.githubusercontent.com/YajatGhule/unbribable-referee/main/deploy/aws/launch.sh | bash
#
# No credentials are created or stored anywhere: the instance gets an IAM role that can call
# Amazon Bedrock and Systems Manager. No inbound ports are opened; you connect with SSM.
# Cost: g6.xlarge (NVIDIA L4) is about $0.80/hour in us-east-1. Stop it with stop.sh.
set -euo pipefail

REGION=${REGION:-us-east-1}
TYPE=${TYPE:-g6.xlarge}
REF=${REF:-main}
NAME=unbribable-referee
ROLE=$NAME-ec2
RAW=https://raw.githubusercontent.com/YajatGhule/unbribable-referee/$REF/deploy/aws
export AWS_DEFAULT_REGION=$REGION

existing=$(aws ec2 describe-instances --filters "Name=tag:Name,Values=$NAME" \
  "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query 'Reservations[].Instances[].InstanceId' --output text)
if [ -n "$existing" ]; then
  echo "Already have $NAME: $existing. Start it with: aws ec2 start-instances --instance-ids $existing"
  exit 0
fi

if [[ $TYPE == g* ]]; then
  quota=$(aws service-quotas get-service-quota --service-code ec2 --quota-code L-DB2E81BA \
    --query Quota.Value --output text 2>/dev/null || echo 0)
  echo "GPU (G and VT on-demand) vCPU quota: $quota"
  if (( ${quota%.*} < 4 )); then
    echo "Your account can't launch a GPU instance yet. Ask for 4 vCPUs (often approved within hours):"
    echo "  aws service-quotas request-service-quota-increase --service-code ec2 --quota-code L-DB2E81BA --desired-value 4"
    echo "Or run on CPU instead (slow, like a laptop):  TYPE=m7i.2xlarge bash launch.sh"
    exit 1
  fi
fi

if ! aws iam get-instance-profile --instance-profile-name "$ROLE" >/dev/null 2>&1; then
  echo "Creating IAM role $ROLE (Bedrock + SSM only)"
  aws iam create-role --role-name "$ROLE" --assume-role-policy-document \
    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name "$ROLE" --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
  aws iam attach-role-policy --role-name "$ROLE" --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
  aws iam create-instance-profile --instance-profile-name "$ROLE" >/dev/null
  aws iam add-role-to-instance-profile --instance-profile-name "$ROLE" --role-name "$ROLE"
  sleep 15  # let the new profile propagate
fi

AMI=""
for p in base-oss-nvidia-driver-gpu-ubuntu-24.04 base-oss-nvidia-driver-gpu-ubuntu-22.04; do
  AMI=$(aws ssm get-parameter --name "/aws/service/deeplearning/ami/x86_64/$p/latest/ami-id" \
    --query Parameter.Value --output text 2>/dev/null) && break
done
[ -n "$AMI" ] || { echo "Couldn't find a Deep Learning AMI"; exit 1; }
echo "AMI: $AMI"

VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 describe-security-groups --filters Name=group-name,Values=$NAME Name=vpc-id,Values=$VPC \
  --query 'SecurityGroups[0].GroupId' --output text)
if [ "$SG" = None ]; then
  SG=$(aws ec2 create-security-group --group-name $NAME --vpc-id "$VPC" \
    --description "Unbribable Referee: no inbound, connect with SSM" --query GroupId --output text)
fi

curl -fsSL "$RAW/user-data.sh" | sed "s/__REF__/$REF/g" > /tmp/referee-user-data.sh

ID=""
for SUBNET in $(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC Name=default-for-az,Values=true \
    --query 'Subnets[].SubnetId' --output text); do
  if ID=$(aws ec2 run-instances --image-id "$AMI" --instance-type "$TYPE" --subnet-id "$SUBNET" \
      --iam-instance-profile Name=$ROLE --security-group-ids "$SG" \
      --metadata-options HttpTokens=required \
      --user-data file:///tmp/referee-user-data.sh \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME}]" \
      --query 'Instances[0].InstanceId' --output text 2>/tmp/referee-launch.err); then
    break
  fi
  echo "  $SUBNET: $(tail -1 /tmp/referee-launch.err)"
  ID=""
done
[ -n "$ID" ] || { echo "Launch failed in every subnet."; exit 1; }

echo "Launched $ID ($TYPE). Setup takes ~10 minutes. Check progress with:"
echo "  curl -fsSL $RAW/status.sh | bash"
