from aws_cdk import (
    Tags,
    Stack,
    aws_ec2 as ec2,
)
from cdk_nag import NagSuppressions
from constructs import Construct

# if using EFS, add to interface_endpoints
interface_endpoints = ['ecr.dkr', 'ecr.api', 'xray', 'logs', 'ssm', 'ssmmessages', 'ec2messages', 'secretsmanager',
                       'elasticloadbalancing', 'monitoring', 'lambda']
endpoint_actions = {'ec2messages':'ec2messages:*'}


class IdpWebAppVpc(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        subnet_type = ec2.SubnetType.PRIVATE_ISOLATED
        self.vpc: ec2.IVpc = ec2.Vpc(self, "ToolkitWebAppVpc", max_azs=3, subnet_configuration=[
            ec2.SubnetConfiguration(subnet_type=subnet_type, name="ToolkitUi", cidr_mask=24),
        ])
        self.vpc.add_flow_log("ToolkitWebAppIdpVpcFlowLog")
        vpc_peer = ec2.Peer.ipv4(self.vpc.vpc_cidr_block)
        endpoint_sg = ec2.SecurityGroup(self, "endpoint_sg", security_group_name="ToolkitWebAppEndpointSg",
                                        description="ToolkitWebApp access to VPC Endpoints", vpc=self.vpc,
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

        bastion_sg = ec2.SecurityGroup(self, "bastion_sg", security_group_name="ToolkitWebAppAdminClientSg",
                                       description="allow access to bastion host", vpc=self.vpc,
                                       allow_all_outbound=True)
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(80))
        bastion_sg.add_ingress_rule(vpc_peer, ec2.Port.tcp(443))
        admin_client = ec2.BastionHostLinux(self, "ToolkitWebAppAdminClient", instance_name="ToolkitWebAppAdminClient",
                                            vpc=self.vpc,
                                            require_imdsv2=True,
                                            security_group=bastion_sg,
                                            block_devices=[ec2.BlockDevice(
                                                device_name="/dev/sdh",
                                                volume=ec2.BlockDeviceVolume.ebs(10,
                                                                                 encrypted=True
                                                                                 )
                                            )],
                                            subnet_selection=ec2.SubnetSelection(
                                                subnet_type=subnet_type))

        NagSuppressions.add_resource_suppressions(endpoint_sg,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-EC23",
                                                          "reason": "EC23 can't read CIDR from intrinsic function ec2.Peer.ipv4()"
                                                      },
                                                  ])
        NagSuppressions.add_resource_suppressions(bastion_sg,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-EC23",
                                                          "reason": "EC23 can't read CIDR from intrinsic function ec2.Peer.ipv4()"
                                                      },
                                                  ])
        NagSuppressions.add_resource_suppressions(admin_client.instance,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-EC28",
                                                          "reason": "no ASG since admin_client is expected to be replaced with VPN or DX"
                                                      },
                                                  {
                                                          "id": "AwsSolutions-EC29",
                                                          "reason": "no ASK since admin_client is expected to be replaced with VPN or DX"
                                                      },
                                                  ])
        NagSuppressions.add_resource_suppressions(admin_client.instance,
                                                  [
                                                      {
                                                          "id": "AwsSolutions-IAM5",
                                                          "reason": "Default policy for BastionHostLinux",
                                                          "appliesTo": [
                                                              "Action::ec2messages:*", "Action::ssmmessages:*",
                                                              "Resource::*"
                                                          ]
                                                      },
                                                  ],
                                                  apply_to_children=True)
