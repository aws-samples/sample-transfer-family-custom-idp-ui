#!/usr/bin/node

const fs = require('node:fs');
const { CloudFormationClient, DescribeStacksCommand } = require("@aws-sdk/client-cloudformation");

//const aws_account = process.env.CDK_DEFAULT_ACCOUNT;
const aws_region = process.env.CDK_DEFAULT_REGION;

const client = new CloudFormationClient({
  region: aws_region
});
const input = {
  StackName: "CustomIdpAuthStack",
  // NextToken: "1",
};
const command = new DescribeStacksCommand(input);

let userPoolClientId = ''
let userPoolId = ''
let apiProxyEndpoint = ''
client.send(command).then(
  (data) => {
    let stack = data.Stacks[0]
    stack.Outputs.forEach((output) => {
      if (output.OutputKey === "UserPoolClientId") {
        userPoolClientId = output.OutputValue
      }
      if (output.OutputKey === "UserPoolId") {
        userPoolId = output.OutputValue
      }
      if (output.OutputKey === "ProxyEndpoint") {
        apiProxyEndpoint = output.OutputValue
      }
    })
    const config = {
      aws_project_region: aws_region,
      //aws_cognito_identity_pool_id: "you don't currently have one",
      aws_cognito_region: aws_region,
      aws_user_pools_id: userPoolId,
      aws_user_pools_web_client_id: userPoolClientId,
      "oauth": {},
    }

    const config_string = JSON.stringify(config, null, 2)

    fs.writeFile('./src/amplifyConfiguration.json', config_string, err => {
      if (err) {
        console.error(err);
      } else {
        console.error("Successfully updated aws-exports.js");
      }
    });

  },
  (error) => {
    console.log("error: " + error);
  }
);







