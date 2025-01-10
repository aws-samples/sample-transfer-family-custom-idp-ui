<template>
  <div>
    <div class="user_list">
      <h2>Existing Users</h2>
      <table>
        <thead>
        <tr>
          <th>Username</th>
          <th>IdP Key</th>
          <th>Module Type</th>
          <th>Actions</th>
        </tr>
        </thead>
        <tbody>
          <tr>
            <td>hardcoded</td>
            <td>publickeys</td>
            <td>Posix</td>
            <td>
              <button>Edit</button>
              <button>Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <h2>{{operation}}</h2>
    <div class="user">
      <form id="user-form" class="form-inline" v-on:submit.prevent="createUser()" v-if="idp_list.length > 0">
        <InputItem>
          <template #message>{{ errors.user }}</template>
          <template #label><label for="user">Username</label></template>
          <input type="text" name="user" v-model="user" v-bind="user_attrs"/>
        </InputItem>
        <InputItem>
          <template #message>{{ errors.identity_provider_key }}</template>
          <template #label><label for="identity_provider_key">Identity Provider Key</label></template>
          <select name="identity_provider_key" v-model="identity_provider_key" v-bind="identity_provider_key_attrs">
            <option v-for="idp in idp_list" :value="idp.provider">{{idp.module}}: {{idp.provider}}</option>
          </select>
        </InputItem>

        <!--
          https://stackoverflow.com/questions/74534399/vue-3-create-dynamic-input
          https://medium.com/@emperorbrains/vue-js-dynamic-forms-best-practices-and-techniques-a633a696283b
          https://codesandbox.io/p/sandbox/vmj3r80nxy?file=%2Fsrc%2FApp.vue%3A77%2C1
        -->
        <InputItem>
          <template #message>{{ errors.role }}</template>
          <template #label><label for="role">IAM Role ARN</label></template>
          <input type="text" name="role" v-model="role" v-bind="role_attrs"/>
        </InputItem>

      </form>
      <div v-else>
        <p>There are no IDPs configured. Please create an IDP then add users.</p>
      </div>
    </div>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .user_list {
    margin-bottom: 1.5em;
    margin-top: 1em;
  }

  .user {
    min-height: 100vh;
    display: flex;
  }
}
</style>

<script setup lang="ts">
import InputItem from '../components/InputItem.vue'
import { useForm } from 'vee-validate'
import * as yup from 'yup'
import { ref } from 'vue'

const record = {
  "user": {
    "S": "jsmith"
  },
  "identity_provider_key": {
    "S": "publickeys"
  },
  "config": {
    "M": {
      "HomeDirectoryDetails": {
        "L": [
          {
            "M": {
              "Entry": {
                "S": "/s3files"
              },
              "Target": {
                "S": "/[bucketname]/prefix/to/files"
              }
            }
          },
          {
            "M": {
              "Entry": {
                "S": "/efs"
              },
              "Target": {
                "S": "/fs-[efs-fs-id]"
              }
            }
          }
        ]
      },
      "HomeDirectoryType": {
        "S": "LOGICAL"
      },
      "PosixProfile": {
        "M": {
          "Gid": {
            "S": "1000"
          },
          "Uid": {
            "S": "1000"
          }
        }
      },
      "PublicKeys": {
        "SS": [
          "ssh-ed25519 [PUBLICKEY]",
          "ssh-rsa [PUBLICKEY]"
        ]
      },
      "Role": {
        "S": "arn:aws:iam::[AWS Account Id]:role/[Role Name]"
      }
    }
  },
  "ipv4_allow_list": {
    "SS": [
      "0.0.0.0/0"
    ]
  }
};
console.log(record);

const operation = ref('Create New User')

// build base level schema for any module type, then add the module specific conditional fields
const schema = yup.object({
  user: yup.string().required().label('Username'),
  identity_provider_key: yup.string().required().label('Identity Provider Key'),
  config_HomeDirectoryDetails_Entry: yup.string().required().label('Home Directory Entry'),
  config_HomeDirectoryDetails_Target: yup.string().required().label('Home Directory Target'),
  ipv4_allow_list: yup.string().required().label('IPv4 Allow List'),
  role: yup.string().required().label('IAM Role ARN')
})

const { values, errors, defineField, handleSubmit } = useForm({
  validationSchema: schema
})

const [user, user_attrs] = defineField('user', {})
const [identity_provider_key, identity_provider_key_attrs] = defineField('identity_provider_key', {})
// HomeDirectoryDetails is a map, and can have multiple entry/target value pairs
// so you have to define the map to hold key/value pairs
const [HomeDirectoryDetails_Entry, HomeDirectoryDetails_Entry_attrs] = defineField('config_HomeDirectoryDetails_Entry', {})
const [HomeDirectoryDetails_Target, HomeDirectoryDetails_Target_attrs] = defineField('config_HomeDirectoryDetails_Target', {})
const [ipv4_allow_list, ipv4_allow_list_attrs] = defineField('ipv4_allow_list', {})
const [role, role_attrs] = defineField('role', {})

const createUser = handleSubmit(values => {
  console.log(values)
  putUser()
})

async function putUser() {
  const user = {
    config: {
      HomeDirectoryDetails: {},
      PosixProfile: {},
      PublicKeys: [],
      Role: ""
    },
    ipv4_allow_list: []
  }
}

const idp_list = ref([])
const load_idp_list = async () => {
  idp_list.value = await getIdps()
}
load_idp_list()


function getIdps() {
  //console.log('getIdp: ' + provider)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/idp/'
  let result = fetch(url, {
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
      console.log('getIdps failure')
    }
  })
  return result
}

</script>