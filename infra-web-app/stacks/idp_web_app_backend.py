from cdk_nag import NagSuppressions
from constructs import Construct, IConstruct
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
    aws_route53_targets as route53_targets,
    aws_s3 as s3
)
import aws_cdk as cdk
import os
import jsii

@jsii.implements(cdk.IAspect)
class HotfixCapacityProviderDependencies:
    # NOT working, still seeing "The specified capacity provider is in use and cannot be removed"
    # Add a dependency from the capacity provider association to the cluster
    # and from each service to the capacity provider association
    # https://github.com/aws/aws-cdk/issues/19275
    def visit(self, node: IConstruct) -> None:
        if type(node) is ecs.Ec2Service:
            children = node.cluster.node.find_all()
            for child in children:
                if type(child) is ecs.CfnClusterCapacityProviderAssociations:
                    child.node.add_dependency(node.cluster)
                    node.node.add_dependency(child)



class IdpWebAppBackend(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 user_pool_client_id: str,
                 jwks_proxy_endpoint: str,
                 vpc_name: str,
                 users_table: str = 'transferidp_users',
                 idp_table: str = 'transferidp_identity_providers',
                 alb_domain: str = 'toolkit.transferfamily.aws.com',
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc.from_lookup(self, 'ToolkitUiVpc', vpc_name=vpc_name)

        cluster = ecs.Cluster(self, "ToolkitWebAppCluster", vpc=vpc, enable_fargate_capacity_providers=True, container_insights=True)
        task_definition = ecs.FargateTaskDefinition(self, 'ToolkitWebAppTaskDefinition',
                                                    runtime_platform=ecs.RuntimePlatform(
                                                        operating_system_family=ecs.OperatingSystemFamily.LINUX,
                                                        cpu_architecture=ecs.CpuArchitecture.ARM64
                                                    ),
                                                    memory_limit_mib=1024, cpu=256
                                                    )

        image = ecr_assets.DockerImageAsset(self, 'ToolkitWebAppUIImage',
                                            directory=os.path.join(os.path.dirname('../.'), 'ui-web-app'))
        image.repository.image_scan_on_push = True

        container = task_definition.add_container('ToolkitWebAppUI',
                                                  image=ecs.ContainerImage.from_docker_image_asset(asset=image),
                                                  logging=ecs.LogDrivers.aws_logs(
                                                      stream_prefix='ToolkitWebAppEcsLog',
                                                      mode=ecs.AwsLogDriverMode.NON_BLOCKING,
                                                      max_buffer_size=cdk.Size.mebibytes(25)
                                                  ))
        container.add_port_mappings(ecs.PortMapping(container_port=80))

        service = ecs.FargateService(self, "Service",
                                     cluster=cluster,
                                     task_definition=task_definition,
                                     desired_count=1,
                                     min_healthy_percent=50,
                                     capacity_provider_strategies=[
                                         ecs.CapacityProviderStrategy(
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
                                     ))

        cdk.Aspects.of(self).add(HotfixCapacityProviderDependencies())

        runtime = lambda_.Runtime.PYTHON_3_13

        # Todo: enable application signals -> https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch-Application-Signals-Enable-Lambda.html

        jwt_layer = lambda_.LayerVersion(self, id='python_jwt_layer',
                                            code=lambda_.Code.from_asset("./lambda_layers/python_jwt_layer/python_jwt.zip"),
                                            compatible_runtimes=[runtime],
                                            description="python jwt validation layer",
                                            layer_version_name="python_jwt_layer"
                                        )

        idp_function = lambda_.Function(self, 'ToolkitWebAppLambda',
                                        runtime=runtime,
                                        handler='manage_idps.handler',
                                        code=lambda_.Code.from_asset(
                                            os.path.join(os.path.dirname("./functions/"))),
                                        vpc=vpc,
                                        environment={
                                            'POWERTOOLS_METRICS_NAMESPACE': 'TransferFamilyToolkit',
                                            'POWERTOOLS_SERVICE_NAME': "ToolkitIdpAdmin",
                                            "LOG_LEVEL": "DEBUG",
                                            'IDP_TABLE_NAME': idp_table,
                                            "COGNITO_USER_POOL_CLIENT_ID": user_pool_client_id,
                                            "JWKS_PROXY_ENDPOINT": jwks_proxy_endpoint
                                        },
                                        tracing=lambda_.Tracing.ACTIVE,
                                        log_retention=cdk.aws_logs.RetentionDays.FIVE_DAYS,
                                        timeout=cdk.Duration.seconds(3),
                                        layers=[jwt_layer])

        user_function = lambda_.Function(self, 'ToolkitWebAppUsersLambda',
                                         runtime=runtime,
                                         handler='manage_users.handler',
                                         code=lambda_.Code.from_asset(
                                             os.path.join(os.path.dirname("./functions/"))),
                                         vpc=vpc,
                                         environment={
                                            'POWERTOOLS_METRICS_NAMESPACE': 'TransferFamilyToolkit',
                                            'POWERTOOLS_SERVICE_NAME': "ToolkitIdpAdmin",
                                            "LOG_LEVEL": "DEBUG",
                                            'USER_TABLE_NAME': users_table,
                                            "COGNITO_USER_POOL_CLIENT_ID": user_pool_client_id,
                                            "JWKS_PROXY_ENDPOINT": jwks_proxy_endpoint
                                         },
                                         tracing=lambda_.Tracing.ACTIVE,
                                         log_retention=cdk.aws_logs.RetentionDays.FIVE_DAYS,
                                         timeout=cdk.Duration.seconds(3),
                                         layers=[jwt_layer])

        powertools_layer = lambda_.LayerVersion.from_layer_version_arn(self, id='lambdapowertools',
                                                                       layer_version_arn=f"arn:aws:lambda:{cdk.Stack.of(self).region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:12")

        idp_function.add_layers(powertools_layer)
        user_function.add_layers(powertools_layer)

        idp_table = ddb.Table.from_table_name(self, 'idpTable', table_name=idp_table)
        idp_table.grant_read_write_data(idp_function)
        user_table = ddb.Table.from_table_name(self, 'userTable', table_name=users_table)
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

        logs_bucket = s3.Bucket(self, 'LogsBucket',
                                                 bucket_name="toolkit-web-app-logs",
                                                 block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
                                                 encryption=s3.BucketEncryption.S3_MANAGED,
                                                 enforce_ssl=True,
                                                 removal_policy=cdk.RemovalPolicy.RETAIN
                                                 )

        alb_sg = ec2.SecurityGroup(self, "alb_sg", security_group_name="ToolkitWebAppApiSg",
                                        description="ToolkitWebApp access to ALB, vpc=self.vpc",
                                        vpc=vpc,
                                        allow_all_outbound=True)
        vpc_peer = ec2.Peer.ipv4(vpc.vpc_cidr_block)
        alb_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(80))
        alb_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(443))
        alb = elbv2.ApplicationLoadBalancer(self, 'ToolkitWebAppLoadBalancer',
                                            vpc=vpc,
                                            internet_facing=False,
                                            security_group=alb_sg,
                                            http2_enabled=True
                                            )
        alb.log_access_logs(logs_bucket, "alb")

        zone = route53.PrivateHostedZone(self, 'ToolkitWebAppHostedZone',
                                         zone_name=alb_domain,
                                         vpc=vpc)
        route53.ARecord(self, "ToolkitUiDomain",
                        zone=zone,
                        target=route53.RecordTarget.from_alias(
                            route53_targets.LoadBalancerTarget(alb)
                        ))

        # todo: to enable HTTPS, you will need a private certificate authority
        # https://docs.aws.amazon.com/cdk/api/v2/python/aws_cdk.aws_acmpca/CfnCertificateAuthority.html

        # certificate = acm.PrivateCertificate(self, 'ToolkitWebAppCertificate',
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

        NagSuppressions.add_resource_suppressions(task_definition,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-IAM5",
                                                          "reason": "Allow all resources for ecr:GetAuthorizationToken",
                                                          "appliesTo": ["Action::ecr:GetAuthorizationToken", "Resource::*"]
                                                      },
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_resource_suppressions(idp_function.role,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-IAM5",
                                                          "reason": "Allow all VPC and basic managed policies",
                                                          "appliesTo": [f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaBasicExecutionRole",
                                                                        f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaVPCAccessExecutionRole",
                                                                        "Resource::*"]
                                                      },
                                                      {
                                                          "id": "AwsSolutions-IAM4",
                                                          "reason": "Allow all VPC and basic managed policies",
                                                          "appliesTo": [f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaBasicExecutionRole",
                                                                        f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaVPCAccessExecutionRole",]
                                                      },
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_resource_suppressions(user_function.role,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-IAM5",
                                                          "reason": "Allow all VPC and basic managed policies",
                                                          "appliesTo": [f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaBasicExecutionRole",
                                                                        f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaVPCAccessExecutionRole",
                                                                        "Resource::*"]
                                                      },
                                                      {
                                                          "id": "AwsSolutions-IAM4",
                                                          "reason": "Allow all VPC and basic managed policies",
                                                          "appliesTo": [f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaBasicExecutionRole",
                                                                        f"Policy::arn:{self.region}:iam::aws:policy/AWSLambdaVPCAccessExecutionRole",]
                                                      },
                                                  ],
                                                  apply_to_children=True)

        NagSuppressions.add_resource_suppressions(logs_bucket,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-S1",
                                                          "reason": "Logs bucket"
                                                      },
                                                  ])

        NagSuppressions.add_stack_suppressions(self,[
                                                      {
                                                          "id": "AwsSolutions-IAM5",
                                                          "reason": "AWSLambdaBasicExecutionRole and AWSLambdaVPCAccessExecutionRole are sufficient"
                                                      },
                                                      {
                                                          "id": "AwsSolutions-IAM4",
                                                          "reason": "AWSLambdaBasicExecutionRole and AWSLambdaVPCAccessExecutionRole are sufficient",
                                                      },
                                                  ])

        NagSuppressions.add_resource_suppressions(alb_sg,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-EC23",
                                                          "reason": "VPC CIDR range and allowed ports defined, not picked up by nag"
                                                      },
                                                  ])

