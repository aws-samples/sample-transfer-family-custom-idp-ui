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
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_certificatemanager as acm
)
import aws_cdk as cdk
import os


# setup logs retention

class CustomIdpEcsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # if you are not using the provided vpc, update this to use your vpc name or id.
        vpc = ec2.Vpc.from_lookup(self, 'CustomIdpVpc', vpc_name='SampleVpcStack/CustomIdpVpc')

        cluster = ecs.Cluster(self, "CustomIdpCluster", vpc=vpc, enable_fargate_capacity_providers=True)
        task_definition = ecs.FargateTaskDefinition(self, 'CustomIdpTaskDefinition',
                                                    runtime_platform=ecs.RuntimePlatform(
                                                        operating_system_family=ecs.OperatingSystemFamily.LINUX,
                                                        cpu_architecture=ecs.CpuArchitecture.ARM64
                                                    ),
                                                    memory_limit_mib=1024, cpu=256
                                                    )

        image = ecr_assets.DockerImageAsset(self, 'CustomIdpWebAppImage',
                                            directory=os.path.join(os.path.dirname('../.'), 'custom-idp-ui'))
        image.repository.image_scan_on_push = True

        container = task_definition.add_container('CustomIdpWebApp',
                                                  image=ecs.ContainerImage.from_docker_image_asset(asset=image),
                                                  logging=ecs.LogDrivers.aws_logs(
                                                      stream_prefix='CustomIdpEcsLog',
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
        idp_function = lambda_.Function(self, 'CustomIdpLambda',
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

        user_function = lambda_.Function(self, 'CustomIdpUsersLambda',
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

        ddb.Table.from_table_name(self, 'idpTable', table_name='transferidp_identity_providers').grant_read_write_data(
            idp_function)
        ddb.Table.from_table_name(self, 'userTable', table_name='transferidp_users').grant_read_write_data(
            user_function)

        toolkit_domain = 'toolkit.transferfamily.aws.com'
        alb = elbv2.ApplicationLoadBalancer(self, 'CustomIdpLoadBalancer',
                                            vpc=vpc,
                                            internet_facing=False
                                            )

        zone = route53.PrivateHostedZone(self, 'CustomIdpHostedZone',
                                         zone_name=toolkit_domain,
                                         vpc=vpc)
        route53.ARecord(self, "ToolkitUiDomain",
                        zone=zone,
                        target=route53.RecordTarget.from_alias(
                            route53_targets.LoadBalancerTarget(alb)
                        ))

        # todo: to enable HTTPS, you will need a private certificate authority
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_acmpca/CfnCertificateAuthority.html

        # certificate = acm.PrivateCertificate(self, 'CustomIdpCertificate',
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

        # todo --> add cognito with verified permissions to web app, admin and user management groups.
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_verifiedpermissions/README.html
        # https://constructs.dev/packages/@cdklabs/cdk-verified-permissions/v/0.1.5?lang=typescript

