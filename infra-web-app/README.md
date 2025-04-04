
# ECS and Lambda for hosting the Toolkit Admin UI 

This project creates an ECS service for hosting the Vue 3 web application,
Lambda functions for CRUDL operations to the 'transferidp_identity_providers' and ECS hosted UI

## Requirements

You will need Docker Desktop (or a similar alternative), Python3 and the AWS CDK installed to deploy this project. 

If you have containerd-snapshotter installed, it will not be compatible with ECR, and deployments will fail.
To workaround this disable contianerd. 

## setup Lambda layer
```
rm -rf lambda_layers
mkdir -p lambda_layers/python_jwt_layer/python/lib/python3.11/site-packages/
cd lambda_layers/python_jwt_layer
docker run  --platform linux/x86_64 -v "$PWD":/var/task "python:3.11-slim-bullseye" /bin/sh -c "cd /var/task; pip3 install --root-user-action=ignore --upgrade pip; pip3 install --root-user-action=ignore python-jose --target=python/lib/python3.11/site-packages/ --only-binary=:all:; exit"
zip -r python_jwt.zip python > /dev/null
cd ../..
```

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
Note - docker fails on disk space in CloudShell, to clear space I deleted the VPC stack folder and the python deps after building the layer zip. 

```
$ cdk synth
```

Next, deploy the auth infrastructure

```
$ cdk deploy CustomIdpAuthStack --require-approval never
```

Now, create a new terminal session, leave the others open.
cd into the UI project, load your AWS credentials if needed. 
run 
```
source ./env.sh
cd custom-idp-ui
npm install
npm run configure
```
You should see an output message "Successfully created src/amplifyConfiguration.js"
Feel free to open this file and review, it allows the amplify hosted login UI to load for your user pool and user pool web app client. 

Back to the terminal for the ECS project

Now, deploy the web app and lambdas
```
$ cdk deploy CustomIdpEcsStack --require-approval never
```


Now you can test connectivity.
If you are using the Session Manager port forwarding approach, use below, if not adjust for your environment


Test VPC private connectivity to your JWKS endpoint. This step might take a few minutes.

```
export JWKS__PROXY_ENDPOINT=`aws cloudformation describe-stacks --region us-east-1 --stack-name CustomIdpAuthStack --query "Stacks[0].Outputs[?OutputKey=='JwksProxyEndpoint'].OutputValue" --output text --no-paginate`
echo $JWKS__PROXY_ENDPOINT
```
Copy down the value for the next step. 
Now start an SSM session to EC2. 

```
aws ssm start-session --region $CDK_DEFAULT_REGION --target $(aws ec2 describe-instances --filters 'Name=tag:Name,Values=TransferToolKitAdminClient' \
  --output text --query 'Reservations[*].Instances[*].InstanceId') 
```

Replace JWKS_ENDPOINT with your endpoint value, and curl the endpoint. 

```
curl <JWKS_ENDPOINT>
```

You should see your user pool public keys printed to the screen. Now exit the SSM session by typing `exit` then start your port forwarding tunnel with the following command. If you have been doing your installation from cloudshell, this step must be run locally so that your broswer can communicate with this proxy. 

```
aws ssm start-session --region $CDK_DEFAULT_REGION --target $(aws ec2 describe-instances --filters 'Name=tag:Name,Values=TransferToolKitAdminClient' \
  --output text --query 'Reservations[*].Instances[*].InstanceId') --document-name AWS-StartPortForwardingSessionToRemoteHost --parameters '{"portNumber":["80"],"localPortNumber":["8080"],"host":["toolkit.transferfamily.aws.com"]}'
```

Connect to the version of the web-app deployed on ECS like on port 80.

http://localhost:8080/


## Auth setup
```
export USER_POOL_ID=`aws cloudformation describe-stacks --stack-name CustomIdpAuthStack --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text --no-paginate`


```


```
# create an idp admin user
aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+idpadmin@amazon.com \
    --user-attributes Name=email,Value=kschwa+idpadmin@amazon.com Name=given_name,Value=Idp Name=family_name,Value=Admin

aws cognito-idp admin-add-user-to-group \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+idpadmin@amazon.com \
    --group-name IdpAdmins
aws cognito-idp admin-add-user-to-group \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+idpadmin@amazon.com \
    --group-name UserAdmins

# create a user admin user
aws cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+useradmin@amazon.com \
    --user-attributes Name=email,Value=kschwa+useradmin@amazon.com Name=given_name,Value=User Name=family_name,Value=Admin      
    
aws cognito-idp admin-add-user-to-group \
    --user-pool-id $USER_POOL_ID \
    --username kschwa+useradmin@amazon.com \
    --group-name UserAdmins
```


##Cleanup
in the ECS project dir (accept destroy prompt). If you see errors about capacity provider, you may need to run this again after it fails the first time. Second time will succeed and both stacks will be deleted. 
```
cdk destroy --all
```

Next in the VPC project dir
```
cdk destroy --all
```
