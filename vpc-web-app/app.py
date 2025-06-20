#!/usr/bin/env python3
import os

import aws_cdk as cdk
from cdk_nag import AwsSolutionsChecks

from stacks.idp_web_app_vpc import IdpWebAppVpc


app = cdk.App()
env = cdk.Environment(account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"])
IdpWebAppVpc(app, "ToolkitWebAppVpc", env=env)
cdk.Aspects.of(app).add(AwsSolutionsChecks(verbose=True))
app.synth()
