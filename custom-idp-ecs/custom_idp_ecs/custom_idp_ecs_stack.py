from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_targets as elbv2_targets,
    aws_lambda as lambda_,
    aws_dynamodb as ddb,
    aws_iam as iam,
    aws_route53 as route53,
    aws_route53_targets as route53_targets
)
import aws_cdk as cdk
import os


# setup logs retention

class CustomIdpEcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # if you are not using the provided vpc, update this to use your vpc name or id.
        vpc = ec2.Vpc.from_lookup(self, 'ToolkitUiVpc', vpc_name='TransferToolkitUiVpcStack/ToolkitUiVpc')

        cluster = ecs.Cluster(self, "TransferToolkitUiCluster", vpc=vpc, enable_fargate_capacity_providers=True)
        task_definition = ecs.FargateTaskDefinition(self, 'TransferToolkitUiTaskDefinition',
                                                    runtime_platform=ecs.RuntimePlatform(
                                                        operating_system_family=ecs.OperatingSystemFamily.LINUX,
                                                        cpu_architecture=ecs.CpuArchitecture.ARM64
                                                    ),
                                                    memory_limit_mib=1024, cpu=256
                                                    )

        image = ecr_assets.DockerImageAsset(self, 'TransferToolkitUiWebAppImage',
                                            directory=os.path.join(os.path.dirname('../.'), 'custom-idp-ui'))
        image.repository.image_scan_on_push = True

        container = task_definition.add_container('TransferToolkitUiWebApp',
                                                  image=ecs.ContainerImage.from_docker_image_asset(asset=image),
                                                  logging=ecs.LogDrivers.aws_logs(
                                                      stream_prefix='TransferToolkitUiEcsLog',
                                                      mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                                                      max_buffer_size=cdk.Size.mebibytes(25)
                                                  ))
        container.add_port_mappings(ecs.PortMapping(container_port=80))

        service = ecs.FargateService(self, "Service",
                                     cluster=cluster,
                                     task_definition=task_definition,
                                     capacity_provider_strategies=[ecs.CapacityProviderStrategy(
                                         capacity_provider="FARGATE_SPOT",
                                         weight=2
                                     ), ecs.CapacityProviderStrategy(
                                         capacity_provider="FARGATE",
                                         weight=1
                                     )
                                     ],
                                     circuit_breaker=ecs.DeploymentCircuitBreaker(
                                         enable=True,
                                         rollback=True
                                     )
                                     )

        runtime = lambda_.Runtime.PYTHON_3_11

        # Todo: enable application signals -> https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-Lambda.html

        idp_function = lambda_.Function(self, 'TransferToolkitUiLambda',
                                        runtime=runtime,
                                        handler='manage_idps.handler',
                                        code=lambda_.Code.from_asset(
                                            os.path.join(os.path.dirname("./functions/manage_idps.py"))),
                                        vpc=vpc,
                                        environment={
                                            'POWERTOOLS_METRICS_NAMESPACE': 'TransferFamilyToolkit',
                                            'POWERTOOLS_SERVICE_NAME': "ToolkitIdpAdmin",
                                            "LOG_LEVEL": "DEBUG",
                                            'IDP_TABLE_NAME': 'transferidp_identity_providers'  # todo paramaterize
                                        },
                                        tracing=lambda_.Tracing.ACTIVE,
                                        log_retention=cdk.aws_logs.RetentionDays.FIVE_DAYS,
                                        timeout=cdk.Duration.seconds(3))

        user_function = lambda_.Function(self, 'TransferToolkitUiUsersLambda',
                                         runtime=runtime,
                                         handler='manage_users.handler',
                                         code=lambda_.Code.from_asset(
                                             os.path.join(os.path.dirname("./functions/manage_users.py"))),
                                         vpc=vpc,
                                         environment={
                                             'POWERTOOLS_METRICS_NAMESPACE': 'TransferFamilyToolkit',
                                             'POWERTOOLS_SERVICE_NAME': "ToolkitIdpAdmin",
                                             "LOG_LEVEL": "DEBUG",
                                             'USER_TABLE_NAME': 'transferidp_users'  # todo paramaterize
                                         },
                                         tracing=lambda_.Tracing.ACTIVE,
                                         log_retention=cdk.aws_logs.RetentionDays.FIVE_DAYS,
                                         timeout=cdk.Duration.seconds(3))

        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(self, id='lambdapowertools',
                                                                       layer_version_arn=f"arn:aws:lambda:{cdk.Stack.of(self).region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86_64:3")
        idp_function.add_layers(powertools_layer)
        user_function.add_layers(powertools_layer)

        idp_table = ddb.Table.from_table_name(self, 'idpTable', table_name='transferidp_identity_providers')
        idp_table.grant_read_write_data(idp_function)
        user_table = ddb.Table.from_table_name(self, 'userTable', table_name='transferidp_users')
        user_table.grant_read_write_data(user_function)

        ddb_endpoint = vpc.add_gateway_endpoint("DynamoDbGatewayEndpoint",
                                                     service=ec2.GatewayVpcEndpointAwsService.DYNAMODB)
        ddb_endpoint.add_to_policy(iam.PolicyStatement(
            actions=['dynamodb:DeleteItem', 'dynamodb:GetItem', 'dynamodb:UpdateItem', 'dynamodb:PutItem',
                     'dynamodb:Query', 'dynamodb:Scan'],
            principals=[iam.ArnPrincipal(idp_function.role.role_arn),
                        iam.ArnPrincipal(user_function.role.role_arn),
                        iam.ServicePrincipal('lambda.amazonaws.com'),
                        iam.AnyPrincipal() # because I'm stuck
                        ],
            resources=[idp_table.table_arn, user_table.table_arn]  # if multi-region add regional ARNs
        ))

        # needed to pull ECR images
        s3_endpoint = vpc.add_gateway_endpoint("S3GatewayEndpoint", service=ec2.GatewayVpcEndpointAwsService.S3)
        s3_endpoint.add_to_policy(iam.PolicyStatement(
            actions=['*'],  # scope to S3 crud operations for TF server
            principals=[iam.AccountPrincipal(account_id=self.account),
                        iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
                        iam.ArnPrincipal(task_definition.execution_role.role_arn),
                        iam.AnyPrincipal() # because I'm stuck
                        ],
            # scope to TF server
            resources=['*']  # scope to needed buckets
        ))

        toolkit_domain = 'toolkit.transferfamily.aws.com'
        alb = elbv2.ApplicationLoadBalancer(self, 'TransferToolkitUiLoadBalancer',
                                            vpc=vpc,
                                            internet_facing=False,
                                            #cross_zone_enabled=False,
                                            # read up on this
                                            )

        zone = route53.PrivateHostedZone(self, 'TransferToolkitUiHostedZone',
                                         zone_name=toolkit_domain,
                                         vpc=vpc)
        route53.ARecord(self, "ToolkitUiDomain",
                        zone=zone,
                        target=route53.RecordTarget.from_alias(
                            route53_targets.LoadBalancerTarget(alb)
                        ))

        # todo: to enable HTTPS, you will need a private certificate authority
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_acmpca/CfnCertificateAuthority.html

        # certificate = acm.PrivateCertificate(self, 'TransferToolkitUiCertificate',
        #                                      domain_name=toolkit_domain,
        #                                      certificate_authority=)

        listener = alb.add_listener("LoadBalancerListener",
                                    port=80, #443,
                                    open=True,
                                    #certificates=[certificate],
                                    #protocol=elbv2.ApplicationProtocol.HTTPS),
                                    protocol=elbv2.ApplicationProtocol.HTTP)
        listener.add_targets("TargetGroup", port=80, targets=[service])
        listener.add_targets("IdpLambdaTargetGroup", health_check=elbv2.HealthCheck(enabled=False),
                             priority=10,
                             target_group_name="IdP-API",
                             conditions=[elbv2.ListenerCondition.path_patterns(["/api/idp/*"])],
                             targets=[elbv2_targets.LambdaTarget(idp_function)])
        listener.add_targets("UserLambdaTargetGroup", health_check=elbv2.HealthCheck(enabled=False),
                             priority=5,
                             target_group_name="User-API",
                             conditions=[elbv2.ListenerCondition.path_patterns(["/api/user/*"])],
                             targets=[elbv2_targets.LambdaTarget(user_function)])

        # todo --> add cognito stack with verified permissions to web app, admin and user management groups.
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_verifiedpermissions/README.html
        # https://constructs.dev/packages/@cdklabs/cdk-verified-permissions/v/0.1.5?lang=typescript

