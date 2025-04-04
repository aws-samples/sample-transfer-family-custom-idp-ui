import aws_cdk as core
import aws_cdk.assertions as assertions

from sample_vpc.transfer_toolkit_ui_vpc_stack import TransferToolkitUiVpcStack

# example tests. To run these tests, uncomment this file along with the example
# resource in sample_vpc/sample_vpc_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = TransferToolkitUiVpcStack(app, "sample-vpc")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
