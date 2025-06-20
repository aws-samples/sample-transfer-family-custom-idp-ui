from cdk_nag import NagSuppressions
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


class IdpWebAppAuth(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 vpc_name: str,
                 alb_domain: str = 'toolkit.transferfamily.aws.com',
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        user_pool = cognito.UserPool(self, 'ToolkitWebAppUserPool',
                                     user_pool_name='ToolkitWebAppUserPool',
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
                                     feature_plan=cognito.FeaturePlan.ESSENTIALS,
                                     mfa=cognito.Mfa.REQUIRED,
                                     mfa_second_factor=cognito.MfaSecondFactor(
                                         otp=True,
                                         sms=False
                                     ))

        user_pool.add_group('ToolkitWebAppIdpAdminsGroup',
                            group_name='IdpAdmins',
                            description='IdpAdmins group for the Transfer Toolkit UI',
                            precedence=0)
        user_pool.add_group('ToolkitWebAppUserAdminsGroup',
                            group_name='UserAdmins',
                            description='UserAdmins group for the Transfer Toolkit UI',
                            precedence=0)

        user_pool_client = cognito.UserPoolClient(self, 'ToolkitWebAppUserPoolClient',
                                                  user_pool=user_pool,
                                                  user_pool_client_name='ToolkitWebAppUserPoolClient',
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

        vpc = ec2.Vpc.from_lookup(self, 'ToolkitWebAppVpc', vpc_name=vpc_name)

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
                    principals=[iam.AnyPrincipal(), iam.AccountPrincipal(self.account)],
                    actions=["execute-api:Invoke"],
                    resources=["execute-api:/*"],
                    effect=iam.Effect.ALLOW
                )]
        )

        api = apigw.RestApi(self, "UserPoolEgressProxyAPI",
                            endpoint_types=[apigw.EndpointType.PRIVATE],
                            policy=endpoint_policy,
                            cloud_watch_role=True,
                            deploy_options=apigw.StageOptions(
                                logging_level=apigw.MethodLoggingLevel.INFO,
                                data_trace_enabled=True,
                                tracing_enabled=True
                            ))

        cognito_root =  api.root.add_resource("cognito")
        cognito_proxy = apigw.ProxyResource(self, "CognitoResource", parent=cognito_root, any_method=True)
        cognito_proxy.add_method("GET",
                         apigw.HttpIntegration(user_pool.user_pool_provider_url + "/{proxy}",
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
                         )],
                         authorization_type=apigw.AuthorizationType.NONE,
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
        cdk.CfnOutput(self, 'JwksProxyEndpoint',  value=api.url_for_path(path=f"/cognito/.well-known/jwks.json"))

        self.user_pool_client_id = user_pool_client.user_pool_client_id
        self.jwks_proxy_endpoint = api.url_for_path(path=f"/cognito/.well-known/jwks.json")

        NagSuppressions.add_resource_suppressions(user_pool,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-COG3",
                                                          "reason": "Security ESSENTIALS for cost management during PoCs cognito.FeaturePlan.ESSENTIALS"
                                                      },
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_resource_suppressions(cognito_proxy,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-APIG4",
                                                          "reason": "This proxy API points to a public for performing auth"
                                                      },
                                                      {
                                                          "id": "AwsSolutions-COG4",
                                                          "reason": "This proxy API points to a public for performing auth"
                                                      }
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_resource_suppressions(api,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-APIG2",
                                                          "reason": "This proxy API, JWKS keys request has no input"
                                                      },
                                                      {
                                                          "id": "AwsSolutions-APIG1",
                                                          "reason": "Default stage, public asset"
                                                      },
                                                      {
                                                          "id": "AwsSolutions-APIG3",
                                                          "reason": "WAF omitted to keep PoC costs down, proxy to Cognito public endpoint"
                                                      }
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_stack_suppressions(self, [
            {
                "id": "AwsSolutions-IAM4",
                "reason": "AWSLambdaBasicExecutionRole and CloudWatchRole is sufficient",
            },
        ])