from wsgiref.simple_server import server_version

from aws_cdk import (
    Tags,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam
)
from constructs import Construct

# add EFS is using EFS with TF and in same VPC
interface_endpoints = ['ecr.dkr', 'ecr.api', 'xray', 'logs', 'ssm', 'ssmmessages', 'ec2messages', 'secretsmanager', 'elasticloadbalancing','monitoring', 'lambda']

class TransferToolkitUiVpcStack(Stack):

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



        bastion_sg = ec2.SecurityGroup(self, "bastion_sg", security_group_name="BastionSg",
                                       description="allow access to bastion host", vpc=self.vpc,
                                       allow_all_outbound=True)
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(80))
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(443))
        admin_client = ec2.BastionHostLinux(self, "TransferToolKitAdminClient", instance_name="AdminClient", vpc=self.vpc,
                                            require_imdsv2=True,
                                            security_group=bastion_sg,
                                            subnet_selection=ec2.SubnetSelection(
                                                subnet_type=subnet_type))
