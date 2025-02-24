
# ECS and Lambda for hosting the Toolkit Admin UI 

This project creates an ECS service for hosting the Vue 3 web application,
Lambda functions for CRUDL operations to the 'transferidp_identity_providers' and 

## Requirements

You will need Docker Desktop (or a similar alternative), Python3 and the AWS CDK installed to deploy this project. 

If you have containerd-snapshotter installed, it will not be compatible with ECR, and deployments will fail.
To workaround this disable contianerd. 

## Install the Toolkit IdP Admin Application 

```
cp env.template.sh env.sh
chmod u+x env.sh
```

modify env.sh with your table names, preferred domain
env.sh is git ignored, so your changes won't clash, don't change the template file.
Now load your environment variables.

```
source ./env.sh
```

First manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

Finally, deploy your VPC infrastructure

```
$ cdk deploy
```

Now you can test connectivity.
If you are using the Session Manager port forwarding approach,
start your port forwarding tunnel with the following command.

```
aws ssm start-session --target $(aws ec2 describe-instances --filters 'Name=tag:Name,Values=TransferToolKitAdminClient' \
  --output text --query 'Reservations[*].Instances[*].InstanceId') --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters '{"portNumber":["80"],"localPortNumber":["8080"],"host":["toolkit.transferfamily.aws.com"]}'
```
Connect to the version of the web-app deployed on ECS like on port 80.

http://localhost:8080/idp


## Auth setup
```
export USER_POOL_ID=`aws cloudformation describe-stacks --stack-name CustomIdpAuthStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-paginate`

export USER_POOL_CLIENT_ID=`aws cloudformation describe-stacks --stack-name CustomIdpAuthStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text --no-paginate`

export USER_POOL_CLIENT_SECRET=`aws cognito-idp describe-user-pool-client --user-pool-id $USER_POOL_ID --client-id $USER_POOL_CLIENT_ID --query UserPoolClient.ClientSecret --output text`

aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+idpadmin@amazon.com \
    --user-attributes Name=email,Value=kschwa+idpadmin@amazon.com Name=given_name,Value=Idp Name=family_name,Value=Admin \
    --message-action SUPPRESS

aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+useradmin@amazon.com \
    --user-attributes Name=email,Value=kschwa+useradmin@amazon.com Name=given_name,Value=User Name=family_name,Value=Admin \
    --message-action SUPPRESS
    
export SECRET_HASH=`echo -n "kschwa+useradmin@amazon.com$USER_POOL_CLIENT_ID" | openssl dgst -sha256 -hmac $USER_POOL_CLIENT_SECRET -binary | openssl enc -base64`    
    
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --auth-parameters USERNAME=kschwa+useradmin@amazon.com,PASSWORD=8JC4ggg,SECRET_HASH=$SECRET_HASH \
  --client-id $USER_POOL_CLIENT_ID
    
aws cognito-idp change-password --previous-password --proposed-password --access-token    
```

