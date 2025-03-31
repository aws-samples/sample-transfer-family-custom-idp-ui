= Isolated VPC for the Transfer Family Toolkit Admin UI

This project contains a private isolated VPC that you can target to run your Toolkit Admin UI in.
The VP contains a bastion host EC2 instance
used for connecting to the UI with the AWS Systems Manager Session Manager port forwarding.
Depending on your organization,
you may remove this resource and instead route to your VPC from AWS Transit Gateway or other network configurations.

== Requirements

You will need Python3 and the AWS CDK installed to deploy this project. 

== Install the VPC

First manually create a virtualenv on MacOS and Linux:

----
$ python3 -m venv .venv
----

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

----
$ source .venv/bin/activate
----

If you are a Windows platform, you would activate the virtualenv like this:

----
% .venv\Scripts\activate.bat
----

Once the virtualenv is activated, you can install the required dependencies.

----
$ pip install -r requirements.txt
----

At this point you can now synthesize the CloudFormation template for this code.

----
$ cdk synth
----

Finally, deploy your VPC infrastructure

----
$ cdk deploy --require-approval never
----

Now continue on to install the custom IdP ECS project