#!/usr/bin/env python3
import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from stacks.idp_web_app_backend import IdpWebAppBackend
from stacks.idp_web_app_auth import IdpWebAppAuth


app = cdk.App()
env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])
vpc_name =  os.environ["VPC_NAME"]

auth = IdpWebAppAuth(app, "ToolkitWebAppAuth", env=env,
                     vpc_name=vpc_name,
                     alb_domain=os.environ["ALB_DOMAIN_NAME"])

IdpWebAppBackend(app, "ToolkitWebAppBackend", env=env,
                 user_pool_client_id = auth.user_pool_client_id,
                 jwks_proxy_endpoint = auth.jwks_proxy_endpoint,
                 vpc_name=vpc_name,
                 users_table=os.environ["USERS_TABLE"],
                 idp_table=os.environ["IDP_TABLE"],
                 alb_domain=os.environ["ALB_DOMAIN_NAME"])
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()
