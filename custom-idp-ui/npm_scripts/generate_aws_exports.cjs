#!/usr/bin/node

const fs = require('node:fs');
const { env } = require('eslint-plugin-vue/lib/configs/base.js')

const config = {
  aws_project_region: "us-east-1",
  aws_cognito_identity_pool_id: "process.env.AWS_COGNITO_IDENTITY_POOL_ID",
  aws_cognito_region: "process.env.AWS_COGNITO_REGION",
  aws_user_pools_id: "process.env.AWS_USER_POOLS_ID",
  aws_user_pools_web_client_id: "process.env.AWS_USER_POOLS_WEB_CLIENT_ID",
  // aws_project_region: env.AWS_PROJECT_REGION,
  // aws_cognito_identity_pool_id: process.env.AWS_COGNITO_IDENTITY_POOL_ID,
  // aws_cognito_region: process.env.AWS_COGNITO_REGION,
  // aws_user_pools_id: process.env.AWS_USER_POOLS_ID,
  // aws_user_pools_web_client_id: process.env.AWS_USER_POOLS_WEB_CLIENT_ID,
  // oauth: {},
  // aws_cognito_login_providers: process.env.AWS_COGNITO_LOGIN_PROVIDERS,
  // aws_cognito_signup_attributes: process.env.AWS_COGNITO_SIGNUP_ATTRIBUTES,
  // aws_mandatory_sign_in: process.env.AWS_MANDATORY_SIGN_IN,
  // aws_cognito_password_protection_settings: process.env.AWS_COGNITO_PASSWORD_PROTECTION_SETTINGS,
  // aws_cognito_verification_mechanisms: process.env.AWS_COGNITO_VERIFICATION_MECHANISMS
}



let config_string = "/* eslint-disable */\n";
config_string += "export const awsmobile = ";
config_string += JSON.stringify(config, null, 2)

fs.writeFile('./src/assets/aws-exports.js', config_string, err => {
  if (err) {
    console.error(err);
  } else {
    // file written successfully
  }
});