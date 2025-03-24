#!/usr/bin/env python3
import os

import aws_cdk as cdk

from custom_idp_ecs.custom_idp_ecs_stack import CustomIdpEcsStack
from custom_idp_ecs.custom_idp_auth_stack import CustomIdpAuthStack


app = cdk.App()
env=cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])


auth = CustomIdpAuthStack(app, "CustomIdpAuthStack", env=env,
                   alb_domain=os.environ["ALB_DOMAIN_NAME"])

CustomIdpEcsStack(app, "CustomIdpEcsStack", env=env,
                  user_pool_client_id = auth.user_pool_client_id,
                  jwks_proxy_endpoint = auth.jwks_proxy_endpoint,
                  users_table=os.environ["USERS_TABLE"],
                  idp_table=os.environ["IDP_TABLE"],
                  alb_domain=os.environ["ALB_DOMAIN_NAME"])

app.synth()
