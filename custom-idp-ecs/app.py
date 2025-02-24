#!/usr/bin/env python3
import os

import aws_cdk as cdk

from custom_idp_ecs.custom_idp_ecs_stack import CustomIdpEcsStack
from custom_idp_ecs.custom_idp_auth_stack import CustomIdpAuthStack


app = cdk.App()
env=cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])
CustomIdpEcsStack(app, "CustomIdpEcsStack", env=env,
                  users_table=os.environ["USERS_TABLE"],
                  idp_table=os.environ["IDP_TABLE"],
                  alb_domain=os.environ["ALB_DOMAIN_NAME"])
CustomIdpAuthStack(app, "CustomIdpAuthStack", env=env,
                   alb_domain=os.environ["ALB_DOMAIN_NAME"])

app.synth()
