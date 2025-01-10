#!/usr/bin/env python3
import os

import aws_cdk as cdk

from custom_idp_ecs.custom_idp_ecs_stack import CustomIdpEcsStack


app = cdk.App()
env=cdk.Environment(account='401350835130', region='us-east-1')
CustomIdpEcsStack(app, "CustomIdpEcsStack", env=env)

app.synth()
