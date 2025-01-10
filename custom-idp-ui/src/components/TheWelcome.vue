<script setup>
import WelcomeItem from './WelcomeItem.vue'
import DocumentationIcon from './icons/IconDocumentation.vue'
import ToolingIcon from './icons/IconTooling.vue'
import EcosystemIcon from './icons/IconEcosystem.vue'
import CommunityIcon from './icons/IconCommunity.vue'
</script>

<template>
  <WelcomeItem>
    <template #icon>
      <DocumentationIcon />
    </template>
    <template #heading>Documentation</template>

    The
    <a href="https://docs.aws.amazon.com/transfer/latest/userguide/custom-idp-toolkit.html" target="_blank" rel="noopener">official documentation</a>
    for the Toolkit solution covers supported IdPs including Active Directory and LDAP, Argon2, Amazon Cognito, Entra ID, Okta, Public, and AWS Secrets Manager.
  </WelcomeItem>

  <WelcomeItem>
    <template #icon>
      <ToolingIcon />
    </template>
    <template #heading>Tooling</template>

    This solution provides a UI for administering both the toolkit IdP configurations as well as users for the IdP when supported.
  </WelcomeItem>

  <WelcomeItem>
    <template #icon>
      <EcosystemIcon />
    </template>
    <template #heading>Ecosystem</template>

    This open source solution is built with Vue.js and runs on AWS infrastructure including
    <a href="https://aws.amazon.com/ecs/" target="_blank">AWS ECS</a>,
    <a href="https://aws.amazon.com/lambda/" target="_blank">AWS Lambda</a>, and
    <a href="https://aws.amazon.com/dynamodb/" target="_blank">Amazon DynamoDB</a>.
    The solution supports running in a private isolated
    <a href="https://aws.amazon.com/vpc/" target="_blank">Amazon VPC</a>
    to keep your data secure and protect your network.
    <br />
    The portal is built with Vue 3, using VeeValidate and the Yup client-side validation framework.
    You can customize this solution to meet your needs.
  </WelcomeItem>

  <WelcomeItem>
    <template #icon>
      <CommunityIcon />
    </template>
    <template #heading>Community</template>

    You can engage with the Toolkit for AWS Transfer Family by interacting the project maintainers on
    <a href="https://github.com/aws-samples/toolkit-for-aws-transfer-family/tree/main" target="_blank" rel="noopener">GitHub</a>.

    Reference the AWS Blog post <a href="https://aws.amazon.com/blogs/storage/simplify-active-directory-authentication-with-a-custom-identity-provider-for-aws-transfer-family/">
    Simplify Active Directory authentication with a custom identity provider for AWS Transfer Family</a> to learn more about supported IdPs and
    COMING SOON blog post to learn about the Admin UI.
  </WelcomeItem>
</template>
