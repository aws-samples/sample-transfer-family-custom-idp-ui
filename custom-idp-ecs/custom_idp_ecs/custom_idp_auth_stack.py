from constructs import Construct
from aws_cdk import (
    Stack,
    aws_cognito as cognito
)
import aws_cdk as cdk
import os


class CustomIdpAuthStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 alb_domain: str = 'toolkit.transferfamily.aws.com',
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # example applications
        # https://github.com/MauriceBrg/cognito-alb-fargate-demo/blob/master/infrastructure/demo_stack.py
        # https://aws.amazon.com/blogs/architecture/enriching-amazon-cognito-features-with-an-amazon-api-gateway-proxy/

        user_pool = cognito.UserPool(self, 'TransferToolkitUiUserPool',
                                     user_pool_name='TransferToolkitUiUserPool',
                                     self_sign_up_enabled=False,
                                     removal_policy=cdk.RemovalPolicy.DESTROY,
                                     sign_in_aliases=cognito.SignInAliases(email=True),
                                     auto_verify=cognito.AutoVerifiedAttrs(email=True),
                                     standard_attributes=cognito.StandardAttributes(
                                         email=cognito.StandardAttribute(required=True, mutable=False),
                                         given_name=cognito.StandardAttribute(required=True, mutable=True),
                                         family_name=cognito.StandardAttribute(required=True, mutable=True)
                                     ),
                                     password_policy=cognito.PasswordPolicy(
                                         min_length=8,
                                         require_digits=True,
                                         require_lowercase=True,
                                         require_uppercase=True,
                                         require_symbols=True,
                                         temp_password_validity=cdk.Duration.days(1)
                                     ),
                                     advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED,
                                     mfa=cognito.Mfa.REQUIRED,
                                     mfa_second_factor=cognito.MfaSecondFactor(
                                         otp=True,
                                         sms=False
                                     ),
                                     )

        user_pool_client = cognito.UserPoolClient(self, 'TransferToolkitUiUserPoolClient',
                                                  user_pool=user_pool,
                                                  user_pool_client_name='TransferToolkitUiUserPoolClient',
                                                  generate_secret=True,
                                                  prevent_user_existence_errors=True,
                                                  access_token_validity=cdk.Duration.hours(1),
                                                  id_token_validity=cdk.Duration.hours(1),
                                                  refresh_token_validity=cdk.Duration.days(30),
                                                  o_auth=cognito.OAuthSettings(
                                                      callback_urls=[
                                                          # This is the endpoint where the ALB accepts the
                                                          # response from Cognito
                                                          f"https://{alb_domain}/oauth2/idpresponse",
                                                          # This is here to allow a redirect to the login page
                                                          # after the logout has been completed
                                                          f"https://{alb_domain}"],
                                                      flows=cognito.OAuthFlows(
                                                          authorization_code_grant=True
                                                      ),
                                                      scopes=[cognito.OAuthScope.OPENID],
                                                      logout_urls=[f"https://{alb_domain}"]
                                                  ),
                                                  supported_identity_providers=[cognito.UserPoolClientIdentityProvider.COGNITO],
                                                  )

        cdk.CfnOutput(self, 'UserPoolId', value=user_pool.user_pool_id)
        cdk.CfnOutput(self, 'UserPoolClientId', value=user_pool_client.user_pool_client_id)




