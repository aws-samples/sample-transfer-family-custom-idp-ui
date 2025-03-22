from constructs import Construct
from aws_cdk import (
    Stack,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_apigateway as apigw
)
import aws_cdk as cdk
import os


class CustomIdpAuthStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 alb_domain: str = 'toolkit.transferfamily.aws.com',
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        domain = user_pool.add_domain('TransferToolkitUiUserPoolDomain',
                                      cognito_domain=cognito.CognitoDomainOptions(
                                          domain_prefix=os.environ.get('COGNITO_DOMAIN_PREFIX', 'transfer-toolkit-ui')
                                      ))

        user_pool_client = cognito.UserPoolClient(self, 'TransferToolkitUiUserPoolClient',
                                                  user_pool=user_pool,
                                                  user_pool_client_name='TransferToolkitUiUserPoolClient',
                                                  generate_secret=False,
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
                                                  supported_identity_providers=[
                                                      cognito.UserPoolClientIdentityProvider.COGNITO],
                                                  )

        vpc = ec2.Vpc.from_lookup(self, 'ToolkitUiVpc', vpc_name='TransferToolkitUiVpcStack/ToolkitUiVpc')

        vpc_endpoint = vpc.add_interface_endpoint("ApiGatewayVpcEndpoint",
                                                  service=ec2.InterfaceVpcEndpointService(
                                                      "com.amazonaws.{}.execute-api".format(self.region)),
                                                  private_dns_enabled=True,
                                                  subnets=ec2.SubnetSelection(
                                                      subnets=vpc.isolated_subnets
                                                  )
                                                  )

        endpoint_policy = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    principals=[iam.AnyPrincipal()],
                    actions=["execute-api:Invoke"],
                    resources=["execute-api:/*"],
                    effect=iam.Effect.ALLOW
                )]
        )

        api = apigw.RestApi(self, "UserPoolEgressProxyAPI",
                            endpoint_types=[apigw.EndpointType.PRIVATE],
                            policy=endpoint_policy,
                            deploy_options=apigw.StageOptions(
                                logging_level=apigw.MethodLoggingLevel.INFO,
                                data_trace_enabled=True,
                                tracing_enabled=True
                            ))

        cognito_root =  api.root.add_resource("cognito")
        cognito_proxy = apigw.ProxyResource(self, "CognitoResource", parent=cognito_root, any_method=True)
        cognito_proxy.add_method("GET",
                         apigw.HttpIntegration(domain.base_url() + "/{proxy}",
                                               proxy=True,
                                               http_method="GET",
                                               options=apigw.IntegrationOptions(
                                                   request_parameters={
                                                       'integration.request.path.proxy': 'method.request.path.proxy'
                                                   },
                                                   integration_responses=[apigw.IntegrationResponse(
                                                       status_code="200",
                                                       response_parameters={
                                                           'method.response.header.Content-Type': "'application/json'"
                                                       }
                                                   )],
                                                   passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH
                                               )
                                               ),
                         request_parameters={
                             'method.request.path.proxy': True
                         },
                         method_responses=[apigw.MethodResponse(
                             status_code="200",
                             response_parameters={
                                 'method.response.header.Content-Type': True
                             }
                         )]
                         )

        # api.root.add_to_resource_policy(
        #     iam.PolicyStatement(
        #         principals=[iam.AnyPrincipal()],
        #         actions=["execute-api:Invoke"],
        #         resources=[f"arn:aws:execute-api:{self.region}:{self.account}:{api.rest_api_id}/*"],
        #         effect=iam.Effect.DENY,
        #         conditions={
        #             "StringNotEquals": {
        #                 "aws:SourceVpce": vpc_endpoint.vpc_endpoint_id
        #             }
        #         }
        #     )
        # )

        cdk.CfnOutput(self, 'UserPoolId', value=user_pool.user_pool_id)
        cdk.CfnOutput(self, 'UserPoolClientId', value=user_pool_client.user_pool_client_id)
        cdk.CfnOutput(self, 'ProxyEndpoint',  value=api.url_for_path(path="/pets"))
