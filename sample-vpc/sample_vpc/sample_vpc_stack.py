from wsgiref.simple_server import server_version

from aws_cdk import (
    Tags,
    Stack,
    aws_ec2 as ec2,
    aws_dynamodb as ddb,
    aws_iam as iam
)
from constructs import Construct

# add EFS is using EFS with TF and in same VPC
interface_endpoints = ['ecr.dkr', 'ecr.api', 'xray', 'logs', 'ssm', 'ssmmessages', 'ec2messages', 'secretsmanager', 'elasticloadbalancing','monitoring', 'lambda']

class SampleVpcStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        subnet_type = ec2.SubnetType.PRIVATE_ISOLATED
        self.vpc: ec2.IVpc = ec2.Vpc(self, "CustomIdpVpc", max_azs=3, subnet_configuration=[
            ec2.SubnetConfiguration(subnet_type=subnet_type, name="CustomIdp", cidr_mask=24),
        ])
        self.vpc.add_flow_log("CustomIdpVpcFlowLog")
        vpc_peer = ec2.Peer.ipv4(self.vpc.vpc_cidr_block)
        endpoint_sg = ec2.SecurityGroup(self, "endpoint_sg", security_group_name="InterfaceEndpointSg",
                                        description="allow access VPC Endpoints", vpc=self.vpc,
                                        allow_all_outbound=True)
        Tags.of(endpoint_sg).add("Name", "InterfaceEndpoints")
        endpoint_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(443))
        endpoint_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(80))

        for endpoint in interface_endpoints:
            interface = self.vpc.add_interface_endpoint(
                endpoint,
                service=ec2.InterfaceVpcEndpointAwsService(endpoint, port=443),
                private_dns_enabled=True,
                security_groups=[endpoint_sg])
            # Tags on endpoints aren't supported yet by Cfn, forward-looking attempt here
            Tags.of(interface).add("Name", endpoint, include_resource_types=['AWS::EC2::VPCEndpoint'])

        idp_table = ddb.Table.from_table_name(self, 'idpTable', table_name='transferidp_identity_providers')
        user_table = ddb.Table.from_table_name(self, 'userTable', table_name='transferidp_users')

        ddb_endpoint = self.vpc.add_gateway_endpoint("DynamoDbGatewayEndpoint", service=ec2.GatewayVpcEndpointAwsService.DYNAMODB)
        ddb_endpoint.add_to_policy(iam.PolicyStatement(
            actions=['dynamodb:DeleteItem', 'dynamodb:GetItem', 'dynamodb:UpdateItem', 'dynamodb:PutItem', 'dynamodb:Query', 'dynamodb:Scan'],
            principals=[iam.AccountPrincipal(account_id=self.account)], # could be scoped to ECS task role and Lambda execution roles
            resources=[idp_table.table_arn, user_table.table_arn] # if multi-region add regional ARNs
        ))

        # only needed if TF server in this VPC, apply policy as bucket ACL
        s3_endpoint = self.vpc.add_gateway_endpoint("S3GatewayEndpoint", service=ec2.GatewayVpcEndpointAwsService.S3)
        s3_endpoint.add_to_policy(iam.PolicyStatement(
            actions=['*'], # scope to S3 crud operations for TF server
            principals=[iam.AccountPrincipal(account_id=self.account)], # scope to TF server
            resources=['*'] # scope to needed buckets
        ))


        bastion_sg = ec2.SecurityGroup(self, "bastion_sg", security_group_name="BastionSg",
                                       description="allow access to bastion host", vpc=self.vpc,
                                       allow_all_outbound=True)
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(80))
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(443))
        admin_client = ec2.BastionHostLinux(self, "AdminClient", instance_name="AdminClient", vpc=self.vpc,
                                            require_imdsv2=True,
                                            security_group=bastion_sg,
                                            subnet_selection=ec2.SubnetSelection(
                                                subnet_type=subnet_type))
