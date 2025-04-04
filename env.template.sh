export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
export CDK_DEFAULT_REGION=us-east-1

export USERS_TABLE=transferidp_users
export IDP_TABLE=transferidp_identity_providers

export ALB_DOMAIN_NAME=toolkit.transferfamily.aws.com
export VPC_NAME=ToolkitWebAppVpc/ToolkitWebAppVpc