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
                                            'IDP_TABLE_NAME': 'transferidp_identity_providers' # todo paramaterize
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
        ddb.Table.from_table_name(self, 'userTable',table_name='transferidp_users').grant_read_write_data(user_function)

        alb = elbv2.ApplicationLoadBalancer(self, 'CustomIdpLoadBalancer',
                                            vpc=vpc,
                                            internet_facing=False)
        listener = alb.add_listener("LoadBalancerListener", port=80, open=True)  # change 'open' to false, add SG
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


        # after all functional requirements, secure everything
        # todo --> add cognito with verified permissions to web app, admin and user management groups.
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_elasticloadbalancingv2_actions/README.html
        #  This is the last thing you'll add once everything is working
        # todo, integrate with Cognito, secure the endpoint with TLS