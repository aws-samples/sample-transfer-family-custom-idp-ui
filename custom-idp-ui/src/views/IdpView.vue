<template>
  <div>
    <div class="idp_list" v-if="idp_list.length > 0">
      <h2>Identity Providers</h2>
      <table class="table table-sm table-striped table-hover"  data-bs-spy="scroll">
        <thead>
        <tr>
          <th scope="col">#</th>
          <th scope="col">Provider</th>
          <th scope="col">Module</th>
          <th scope="col">Actions</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="(idp,index) in idp_list" :key="idp['provider']">
          <th scope="row">{{ index }}</th>
          <td>{{ idp.provider }}</td>
          <td>{{ idp.module }}</td>
          <td>
            <button v-on:click="editIdp(idp.provider)" class="btn btn-secondary">Edit or Copy</button>
            <button v-on:click="deleteIdp(idp.provider)" class="btn btn-danger">Delete</button>
          </td>
        </tr>
        </tbody>
      </table>
    </div>
    <div v-else>{{ idp_load_msg }}</div>
    <h2>{{operation}}</h2>
<!--    <p>ToDo: display success messages for deletes and saves</p>-->
    <div class="idp" v-if="!idp_load_msg.includes('Failed')">
      <form id="idp-create" class="form-inline" v-on:submit.prevent="createIdp()">
        <InputItem>
          <template #message>{{ errors.module }}</template>
          <template #label><label for="module">IDP Module Type</label></template>
          <select v-model="module" v-bind="module_attrs" id="module">
            <option disabled value="">Choose IDP</option>
            <option v-for="option in module_options" :value="option.value" :key="option.value">
              {{ option.text }}
            </option>
          </select>
        </InputItem>
        <InputItem>
          <template #message>{{ errors.provider }}</template>
          <template #label><label for="provider">Provider Name</label></template>
          <input id="provider" type="text" v-model="provider" v-bind="provider_attrs" />
        </InputItem>
        <InputItem v-if="cognito_client_id_attrs.visible">
          <template #message>{{ errors.config_cognito_client_id }}</template>
          <template #label><label for="provider">Cognito Client ID</label></template>
          <input
            id="cognito_client_id"
            type="text"
            v-model="cognito_client_id"
            v-bind="cognito_client_id_attrs"
          />
        </InputItem>
        <InputItem v-if="cognito_user_pool_region_attrs.visible">
          <template #message>{{ errors.config_user_pool_region }}</template>
          <template #label
            ><label for="cognito_user_pool_region">Cognito User Pool Region</label></template
          >
          <input
            placeholder="us-east-1"
            id="cognito_user_pool_region"
            type="text"
            v-model="cognito_user_pool_region"
            v-bind="cognito_user_pool_region_attrs"
          />
        </InputItem>
        <InputItem v-if="server_attrs.visible">
          <template #message>{{ errors.config_server }}</template>
          <template #label><label for="server">LDAP Server</label></template>
          <input placeholder="fully qualified domain name" id="server" type="text" v-model="server" v-bind="server_attrs" />
        </InputItem>

        <InputItem v-if="search_base_attrs.visible">
          <template #message>{{ errors.config_search_base }}</template>
          <template #label><label for="search_base">LDAP Search Base</label></template>
          <input id="search_base" type="text" v-model="search_base" v-bind="search_base_attrs" />
        </InputItem>
        <InputItem v-if="port_attrs.visible">
          <template #label><label for="port">LDAP Port</label></template>
          <input id="port" type="text" v-model="port" v-bind="port_attrs" />
          <template #message>{{ errors.config_port }}</template>
        </InputItem>
        <InputItem v-if="mfa_attrs.visible">
          <template #label><label for="mfa">MFA Required</label></template>
          <input id="mfa" type="checkbox" v-model="mfa" v-bind="mfa_attrs" value="true" />
          <template #message>{{ errors['mfa'] }}</template>
        </InputItem>
        <InputItem v-if="mfa_token_length_attrs.visible">
          <template #label><label for="mfa_token_length">MFA Token Length</label></template>
          <input
            id="mfa_token_length"
            type="text"
            v-model="mfa_token_length"
            v-bind="mfa_token_length_attrs"
          />
          <template #message>{{ errors.config_mfa_token_length }}</template>
        </InputItem>
        <InputItem v-if="ssl_attrs.visible">
          <template #label><label for="ssl">TLS Server Connection</label></template>
          <input id="ssl" type="checkbox" v-bind="ssl_attrs" v-model="ssl" value="true" />
          <template #message>{{ errors.ssl }}</template>
        </InputItem>
        <InputItem v-if="ssl_verify_attrs.visible">
          <template #label><label for="ssl_verify">TLS verify certificate DNS</label></template>
          <input
            id="ssl_verify"
            type="checkbox"
            v-bind="ssl_verify_attrs"
            v-model="ssl_verify"
            value="true"
          />
          <template #message>{{ errors.ssl_verify }}</template>
        </InputItem>
        <InputItem v-if="ldap_ssl_ca_secret_arn_attrs.visible">
          <template #label
            ><label for="ldap_ssl_ca_secret_arn"
              >CA Cert Secret ARN (else uses Lambda Cert store)</label
            >
          </template>
          <input
            placeholder="arn:aws:secretsmanager:<region>:<account-id>:<secret-name>"
            id="ldap_ssl_ca_secret_arn"
            type="text"
            v-bind="ldap_ssl_ca_secret_arn_attrs"
            v-model="ldap_ssl_ca_secret_arn"
          />
          <template #message>{{ errors.config_ldap_ssl_ca_secret_arn }}</template>
        </InputItem>
        <InputItem v-if="public_key_support_attrs.visible">
          <template #label><label for="public_key_support">Public Key Support</label></template>
          <input
            id="public_key_support"
            type="checkbox"
            v-bind="public_key_support_attrs"
            v-model="public_key_support"
            value="true"
          />
          <template #message>{{ errors.public_key_support }}</template>
        </InputItem>

        <InputItem v-if="ldap_service_account_secret_arn_attrs.visible">
          <template #label
            ><label for="ldap_service_account_secret_arn"
              >Active Directory or LDAP credentials Secret ARN (else uses Lambda Cert store)</label
            ></template
          >
          <input
            placeholder="arn:aws:secretsmanager:<region>:<account-id>:<secret-name>"
            id="ldap_service_account_secret_arn"
            type="text"
            v-bind="ldap_service_account_secret_arn_attrs"
            v-model="ldap_service_account_secret_arn"
          />
          <template #message>{{ errors.config_service_account_secret_arn }}</template>
        </InputItem>

        <input-item v-if="ldap_allowed_groups_attrs.visible">
          <template #message>{{ errors.ldap_allowed_groups }}</template>
          <template #label><label for="ldap_allowed_groups">LDAP allowed groups</label></template>
          <textarea
            name="ldap_allowed_groups"
            placeholder="One per line in DN Format: CN=Group Name,CN=Users,DC=domain2019,DC=local"
            v-model="ldap_allowed_groups"
            v-bind="ldap_allowed_groups_attrs"
          ></textarea>
        </input-item>

        <InputItem v-if="attributes_gid_attrs.visible">
          <template #label><label for="attributes_gid">PosixProfile Gid</label></template>
          <input
            id="attributes_gid"
            type="text"
            v-bind="attributes_gid_attrs"
            v-model="attributes_gid"
          />
          <template #message>{{ errors.config_attributes_gid }}</template>
        </InputItem>
        <InputItem v-if="attributes_uid_attrs.visible">
          <template #label><label for="attributes_uid">PosixProfile Uid</label></template>
          <input
            id="attributes_uid"
            type="text"
            v-bind="attributes_uid_attrs"
            v-model="attributes_uid"
          />
          <template #message>{{ errors.config_attributes_uid }}</template>
        </InputItem>
        <InputItem v-if="attributes_role_attrs.visible">
          <template #label><label for="attributes_role">Role</label></template>
          <input
            placeholder="arn:aws:iam::<account-id>:role/<role-name>"
            id="attributes_role"
            type="text"
            v-bind="attributes_role_attrs"
            v-model="attributes_role"
          />
          <template #message>{{ errors.config_attributes_role }}</template>
        </InputItem>
        <InputItem v-if="attributes_policy_attrs.visible">
          <template #label><label for="attributes_policy">Policy</label></template>
          <input
            placeholder="ARN or JSON/YAML statement?"
            id="attributes_policy"
            type="text"
            v-bind="attributes_policy_attrs"
            v-model="attributes_policy"
          />
          <template #message>{{ errors.config_attributes_policy }}</template>
        </InputItem>
        <InputItem v-if="ignore_missing_attributes_attrs.visible">
          <template #label
            ><label for="ignore_missing_attributes">Ignore Missing Attributes</label></template
          >
          <input
            id="ignore_missing_attributes"
            type="checkbox"
            v-bind="ignore_missing_attributes_attrs"
            v-model="ignore_missing_attributes"
            value="true"
          />
          <template #message>{{ errors.config_ignore_missing_attributes }}</template>
        </InputItem>
        <InputItem v-if="client_id_attrs.visible">
          <template #label><label for="client_id">Entra ID Client ID</label></template>
          <input id="client_id" type="text" v-bind="client_id_attrs" v-model="client_id" />
          <template #message>{{ errors.config_client_id }}</template>
        </InputItem>
        <InputItem v-if="app_secret_arn_attrs.visible">
          <template #label><label for="app_secret_arn">Entra ID Client Secret ARN</label></template>
          <input
            placeholder="arn:aws:secretsmanager:<region>:<account-id>:<secret-name>"
            id="app_secret_arn"
            type="text"
            v-bind="app_secret_arn_attrs"
            v-model="app_secret_arn"
          />
          <template #message>{{ errors.config_app_secret_arn }}</template>
        </InputItem>
        <InputItem v-if="authority_url_attrs.visible">
          <template #label><label for="authority_url">Entra ID authority URL</label></template>
          <input
            id="authority_url"
            type="text"
            v-bind="authority_url_attrs"
            v-model="authority_url"
          />
          <template #message>{{ errors.config_authority_url }}</template>
        </InputItem>
        <InputItem v-if="okta_domain_attrs.visible">
          <template #message>{{ errors.okta_domain }}</template>
          <template #label><label for="">Okta Domain</label></template>
          <input placeholder="fully qualified domain name" id="" type="text" v-bind="okta_domain_attrs" v-model="okta_domain" />
        </InputItem>
        <InputItem v-if="okta_app_client_id_attrs.visible">
          <template #message>{{ errors.okta_app_client_id }}</template>
          <template #label><label for="">Okta App Client ID</label></template>
          <input id="" type="text" v-bind="okta_app_client_id_attrs" v-model="okta_app_client_id" />
        </InputItem>
        <InputItem v-if="okta_redirect_url_attrs.visible">
          <template #message>{{ errors.okta_redirect_url }}</template>
          <template #label><label for="">Okta Redirect URL</label></template>
          <input placeholder="fully qualified domain name" id="" type="text" v-bind="okta_redirect_url_attrs" v-model="okta_redirect_url" />
        </InputItem>
        <div id="submit">
          <input id="form_submit" type="submit" value="Save" class="btn btn-primary"/>
          <input id="cancel" type="reset" onclick="window.location.reload()" value="Clear" class="btn btn-warning"/>
        </div>
      </form>
    </div>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .idp_list {
    margin-bottom: 1.5em;
    margin-top: 1em;
    height: 250px;
    overflow-y: scroll;
  }

  .idp {
    min-height: 100vh;
    display: flex;
  }
  input[type="text"] {
    width: 25em;
  }
  textarea {
    width: 40em;
  }
  thead th {
    position: sticky;
    top: 0;
  }
  .btn {
    margin-right: .75rem;
  }
}
</style>
<script setup lang="ts">
import InputItem from '../components/InputItem.vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { ref } from 'vue'

const idp_list = ref([])
const load_idp_list = async () => {
  idp_list.value = await getIdp('')
}
load_idp_list()

const schema = yup.object({
  module: yup.string().required('Select a Module type'),
  provider: yup.string().required('Provider Name is required').min(5).max(100),
  config_cognito_client_id: yup.string().when('module', {
    is: 'cognito',
    then: (schema) => schema.required('Enter Cognito App Client Id'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_cognito_user_pool_region: yup.string().optional(),
  config_mfa: yup.string().optional(),
  config_mfa_token_length: yup.number().when('config_mfa', {
    is: 'true',
    then: (schema) =>
      schema
        .required('When MFA is required, specify a token length')
        .positive()
        .integer('MFA Tokens length must be an integer')
        .min(6, 'MFA Tokens length must be 6 to 10')
        .max(10, 'MFA Tokens length must be 6 to 10')
        .typeError('MFA Tokens length must be numeric'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_client_id: yup.string().when('module', {
    is: 'entra',
    then: (schema) => schema.required('Enter Entra ID App Client Id'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_app_secret_arn: yup.string().when('module', {
    is: 'entra',
    then: (schema) => schema.required('Enter Entra ID Client Secret ARN'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_authority_url: yup.string().optional().url('Authority URL must be FQDN'),
  config_attributes_gid: yup.string(),
  config_attributes_uid: yup.string(),
  config_attributes_role: yup.string(),
  config_attributes_policy: yup.string(),
  config_ignore_missing_attributes: yup.boolean(),
  config_port: yup
    .number()
    .typeError('Must be a valid port number, typically 389 or 636 if using TLS'),
  config_search_base: yup.string().when('module', {
    is: 'ldap',
    then: (schema) => schema.required('LDAP search base in the format DC=EXAMPLE,DC=COM'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_server: yup.string().when('module', {
    is: 'ldap',
    then: (schema) =>
      schema
        .required('Enter DNS or IP of LDAP server or AD domain')
        .url('Config Server must be FQDN'),
    otherwise: (schema) => schema.notRequired()
  }),
  config_ssl: yup.boolean(),
  config_ssl_verify: yup.boolean(),
  config_ldap_ssl_ca_secret_arn: yup.string().optional(),
  config_ldap_service_account_secret_arn: yup.string().optional(),
  config_ldap_allowed_groups: yup.string().optional(),

  // okta
  okta_domain: yup.string().when('module', {
    is: 'okta',
    then: (schema) =>
      schema.required('Enter DNS or IP of Okta domain').url('Okta domain must be FQDN'),
    otherwise: (schema) => schema.notRequired()
  }),
  okta_app_client_id: yup.string().optional(),
  okta_redirect_url: yup.string().optional().url('Okta Redirect URL must be FQDN'),

  // public key
  public_key_support: yup.boolean().optional()
}) //)

const { values, errors, defineField, handleSubmit } = useForm({
  validationSchema: schema
})

const module_options = ref([
  { text: 'Argon2 (local hash)', value: 'argon2' },
  { text: 'Amazon Cognito', value: 'cognito' },
  { text: 'Microsoft Entra ID', value: 'entra' },
  { text: 'Active Directory and LDAP', value: 'ldap' },
  { text: 'Okta', value: 'okta' },
  { text: 'Public Key', value: 'public_key' }
  //{ text: 'Secrets Manager', value: 'public_key' } -- need clarification, docs say this is ldap
])
const operation = ref('Configure New IDP')
const [module, module_attrs] = defineField('module', {})
const [provider, provider_attrs] = defineField('provider', {})
const [cognito_client_id, cognito_client_id_attrs] = defineField('config_cognito_client_id', {
  props() {
    return { visible: module.value === 'cognito' }
  }
})
const [cognito_user_pool_region, cognito_user_pool_region_attrs] = defineField('config_cognito_user_pool_region', {
    props() {
      return { visible: module.value === 'cognito' }
    }
  })
const [mfa, mfa_attrs] = defineField('config_mfa', {
  props() {
    return { visible: module.value === 'cognito' || module.value === 'okta' }
  }
})
const [mfa_token_length, mfa_token_length_attrs] = defineField('config_mfa_token_length', {
  props() {
    return {
      visible: (module.value === 'cognito' || module.value === 'okta') && mfa.value === true
    }
  }
})
const [server, server_attrs] = defineField('config_server', {
  props() {
    return { visible: module.value === 'ldap' }
  }
})
const [search_base, search_base_attrs] = defineField('config_search_base', {
  props() {
    return { visible: module.value === 'ldap' }
  }
})
const [port, port_attrs] = defineField('config_port', {
  props() {
    return { visible: module.value === 'ldap' }
  }
})
const [ssl, ssl_attrs] = defineField('config_ssl', {
  props() {
    return { visible: module.value === 'ldap' }
  }
})
const [ssl_verify, ssl_verify_attrs] = defineField('config_ssl_verify', {
  props() {
    return { visible: module.value === 'ldap' }
  }
})
ssl.value = true
ssl_verify.value = true
const [ldap_ssl_ca_secret_arn, ldap_ssl_ca_secret_arn_attrs] = defineField('config_ldap_ssl_ca_secret_arn', {
    props() {
      return { visible: module.value === 'ldap' && ssl_verify.value === true }
    }
  })
const [ldap_service_account_secret_arn, ldap_service_account_secret_arn_attrs] = defineField('config_ldap_service_account_secret_arn', {
    props() {
      return { visible: module.value === 'ldap' && public_key_support.value === true }
    }
  })
const [ldap_allowed_groups, ldap_allowed_groups_attrs] = defineField('config_ldap_allowed_groups', {
    props() {
      return { visible: module.value === 'ldap' }
    }
  })
const [attributes_gid, attributes_gid_attrs] = defineField('config_attributes_gid', {
  props() {
    return { visible: module.value === 'ldap' || module.value === 'okta' }
  }
})
const [attributes_uid, attributes_uid_attrs] = defineField('config_attributes_uid', {
  props() {
    return { visible: module.value === 'ldap' || module.value === 'okta' }
  }
})
const [attributes_role, attributes_role_attrs] = defineField('config_attributes_role', {
  props() {
    return { visible: module.value === 'ldap' || module.value === 'okta' }
  }
})
const [attributes_policy, attributes_policy_attrs] = defineField('config_attributes_policy', {
  props() {
    return { visible: module.value === 'ldap' || module.value === 'okta' }
  }
})
const [ignore_missing_attributes, ignore_missing_attributes_attrs] = defineField('config_ignore_missing_attributes', {
    props() {
      return { visible: module.value === 'ldap' || module.value === 'okta' }
    }
  })
const [public_key_support, public_key_support_attrs] = defineField('public_key_support', {
  props() {
    return { visible: module.value === 'public_key' || module.value === 'ldap' }
  }
})
const [client_id, client_id_attrs] = defineField('config_client_id', {
  props() {
    return { visible: module.value === 'entra' }
  }
})
const [app_secret_arn, app_secret_arn_attrs] = defineField('config_app_secret_arn', {
  props() {
    return { visible: module.value === 'entra' }
  }
})
const [authority_url, authority_url_attrs] = defineField('config_authority_url', {
  props() {
    return { visible: module.value === 'entra' }
  }
})
const [okta_domain, okta_domain_attrs] = defineField('okta_domain', {
  props() {
    return { visible: module.value === 'okta' }
  }
})
const [okta_app_client_id, okta_app_client_id_attrs] = defineField('okta_app_client_id', {
  props() {
    return { visible: module.value === 'okta' }
  }
})
const [okta_redirect_url, okta_redirect_url_attrs] = defineField('okta_redirect_url', {
  props() {
    return { visible: module.value === 'okta' }
  }
})

const createIdp = handleSubmit((values) => {
  console.log(values)
  saveIdp()
})

async function saveIdp() {
  const idp = {
    config: {
      attributes: {}
    }
  }

  for (let [key, value] of Object.entries(values)) {
    if (key.startsWith('config_attributes_')) {
      idp.config.attributes[key.replace('config_attributes_', '')] = value
    } else if (key.startsWith('config_')) {
      if (key === 'config_ldap_allowed_groups') {
        idp.config[key.replace('config_', '')] = value.split('\n')
      } else {
        idp.config[key.replace('config_', '')] = value
      }
    } else {
      idp[key] = value
    }
  }

  let json = {}
  try {
    json = await putIdp(idp)
  } catch (e) {
    console.log(e)
  } finally {
    console.log('done')
  }
  window.location.reload() // reload because it's a simple way to reset the form
  //load_idp_list();
}

async function editIdp(provider_name) {
  const idp = await getIdp(provider_name)
  operation.value = 'Edit or Copy IDP: ' + idp.provider
  module.value = idp.module
  provider.value = idp.provider
  cognito_client_id.value = idp.config.cognito_client_id
  cognito_user_pool_region.value = idp.config.cognito_user_pool_region
  mfa.value = idp.config.mfa
  mfa_token_length.value = idp.config.mfa_token_length
  server.value = idp.config.server
  search_base.value = idp.config.search_base
  port.value = idp.config.port
  ssl.value = idp.config.ssl
  ssl_verify.value = idp.config.ssl_verify
  ldap_ssl_ca_secret_arn.value = idp.config.ldap_ssl_ca_secret_arn
  ldap_service_account_secret_arn.value = idp.config.ldap_service_account_secret_arn
  ldap_allowed_groups.value = idp.config.ldap_allowed_groups.join('\n')
  attributes_gid.value  = idp.config.attributes.gid
  attributes_uid.value  = idp.config.attributes.uid
  attributes_role.value = idp.config.attributes.role
  attributes_policy.value = idp.config.attributes.policy
  ignore_missing_attributes.value = idp.config.ignore_missing_attributes
  public_key_support.value = idp.public_key_support
  client_id.value  = idp.config.client_id
  app_secret_arn.value = idp.config.app_secret_arn
  authority_url.value = idp.config.authority_url
  okta_domain.value = idp.okta_domain
  okta_app_client_id.value = idp.okta_app_client_id
  okta_redirect_url.value  = idp.okta_redirect_url
}


async function putIdp(idp) {
  const signal = AbortSignal.timeout(3000)
  // todo: setup local and deployed config files.
  //  Also solve for the cors issue on ALB, or give in and create an API Gateway to handle CORS
  //const url = 'http://internal-Custom-Custo-kOXb11ZUe62Y-1583837551.us-east-1.elb.amazonaws.com/api/idp/'
  const url = 'http://localhost:8080/api/idp/'
  return await fetch(url, {
    signal,
    method: 'PUT',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(idp)
  })
}
const idp_load_msg = ref("Loading IDPs...")

function getIdp(provider) {
  let failed = false
  //console.log('getIdp: ' + provider)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/idp/'
  let result = fetch(url + provider, {
    signal,
    method: 'GET',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      return response.json()
    } else {
      console.log('getIdp ' + provider + ' failure')
    }
  }).catch(error => {
    console.log('Failed to load or connect to IDP datasource', error)
    idp_load_msg.value = "Failed to load or connect to IDP datasource"
    failed = true
  })
  if (failed) {
    return []
  }
  return result
}

function deleteIdp(provider) {
  console.log('deleteIdp: ' + provider)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/idp/'
  let result = fetch(url + provider, {
    signal,
    method: 'DELETE',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      console.log('deleteIdp success')
      return response.json()
    } else {
      console.log('deleteIdp failure')
    }
  }).catch(error => {
    console.log('Failed to delete IDP', error)
  })
  console.log('delete result' + result)
  idp_list.value = idp_list.value.filter((idp) => idp.provider !== provider)
  setTimeout(() => load_idp_list(), 250) // verbosely reload on delay
}
</script>
