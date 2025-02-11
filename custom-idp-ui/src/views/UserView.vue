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
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in user_list" :key="user['user']">
            <td>{{ user.user }}</td>
            <td>{{ user.identity_provider_key }}</td>
            <td>{{ user.config.Role }}</td>
            <td>
              <button v-on:click="editUser(user.user, user.identity_provider_key)">Edit or Copy</button>
              <button v-on:click="deleteUser(user.user, user.identity_provider_key)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <h2>{{ operation }}</h2>
    <div class="user">
      <form
        id="user-form"
        class="form-inline"
        v-on:submit.prevent="createUser()"
        v-if="idp_list.length > 0"
      >
        <InputItem>
          <template #message>{{ errors.user }}</template>
          <template #label><label for="user">Username</label></template>
          <input placeholder="in lowercase" type="text" id="user" v-model="user" v-bind="user_attrs" />
        </InputItem>
        <InputItem>
          <template #message>{{ errors.identity_provider_key }}
          <span v-if="errors.identity_provider_module">
            <br />{{ errors.identity_provider_module }}
          </span>
          </template>
          <template #label
            ><label for="identity_provider_key">Identity Provider Key</label></template
          >
          <select
            id="identity_provider_key"
            name="identity_provider_key"
            v-model="identity_provider_key"
            v-bind="identity_provider_key_attrs"
            v-on:change="setIdpModule">
            <option disabled value="">Choose IDP</option>
            <option v-for="option in idp_list" :value="option.provider" :key="option.provider">
              {{ option.module }}: {{ option.provider }}
            </option>
          </select>
        </InputItem>
        <InputItem>
          <template #message>{{ errors.config_Role }}</template>
          <template #label><label for="role">IAM Role ARN</label></template>
          <input placeholder="arn:aws:iam::<account-id>:role/<role-name>" type="text" id="role" v-model="Role" v-bind="Role_attrs" />
        </InputItem>
        <InputItem v-if="argon2_hash_attrs.visible">
          <template #message>{{ errors.config_argon2_hash }}</template>
          <template #label><label for="argon2_hash">Argon2 Hash</label></template>
          <input placeholder="$argon2i$v=19$m=4096,t=3,p=$argon2i$v=19$m=4096,t=3,p=XX" type="text" id="argon2_hash" v-model="argon2_hash" v-bind="argon2_hash_attrs" />
        </InputItem>
        <h4>Home Directory Type</h4>
        <InputItem>
          <template #message></template>
          <template #label><label for="LOGICAL">LOGICAL</label></template>
          <input
            type="radio"
            id="LOGICAL"
            name="home_directory_type"
            value="LOGICAL"
            v-model="HomeDirectoryType"
            v-bind="HomeDirectoryType_attrs"
          />
        </InputItem>
        <InputItem>
          <template #message></template>
          <template #label><label for="PATH">PATH</label></template>
          <input
            type="radio"
            id="PATH"
            name="home_directory_type"
            value="PATH"
            v-model="HomeDirectoryType"
            v-bind="HomeDirectoryType_attrs"
          />
        </InputItem>
        <InputItem v-if="HomeDirectory_attrs.visible">
          <template #message>{{ errors.config_HomeDirectory }}</template>
          <template #label><label for="home_directory">Home Directory</label></template>
          <input placeholder="S3 or EFS path" type="text" name="role" v-model="HomeDirectory" v-bind="HomeDirectory_attrs" />
        </InputItem>
        <input-item>
          <template #message>{{ errors.ipv4_allow_list }}</template>
          <template #label><label for="ipv4_allow_list">IPv4 Allow List</label></template>
          <textarea
            id="ipv4_allow_list"
            placeholder="CIDR address per line"
            v-model="ipv4_allow_list"
            v-bind="ipv4_allow_list_attrs"
          ></textarea>
        </input-item>

        <h4>Home Directory Details</h4>
        <div v-for="(field, index) in homeFields" :key="field.key">
          <button type="button" @click="homeRemove(index)">Remove Detail</button>
          <input-item>
            <template #label><label :for="'entry' + index">Entry</label></template>
            <input
              type="text"
              :id="'entry' + index"
              v-model.lazy="homeFields[index].value['Entry']"
            />
          </input-item>
          <input-item>
            <template #label><label :for="'target' + index">Target</label></template>
            <input
              type="text"
              :id="'target' + index"
              v-model.lazy="homeFields[index].value['Target']"
            />
          </input-item>
          <input-item>
          <template #label><label :for="'regions' + index">Allowed Regions</label></template>
          <textarea
            :id="'regions' + index"
            placeholder="One region code per line"
            v-model="homeFields[index].value['regions']"
          ></textarea>
        </input-item>
        </div>
        <button type="button" @click="homePush('')">Add Home Directory Detail</button>

        <h4>Posix Profiles</h4>
        <div v-for="(field, index) in posixFields" :key="field.key">
           <input-item>
            <template #label><label :for="'gid' + index">Gid</label></template>
            <input
              type="text"
              :id="'gid' + index"
              v-model.lazy="posixFields[index].value['Gid']"
            />
          </input-item>
          <input-item>
            <template #label><label :for="'uid' + index">Uid</label></template>
            <input
              type="text"
              :id="'uid' + index"
              v-model.lazy="posixFields[index].value['Uid']"
            />
          </input-item>
          <button type="button" @click="posixRemove(index)">Remove Profile</button>
        </div>
        <button type="button" @click="posixPush('')">Add Posix Profile</button>


        <h4>Public Keys</h4>
        <div v-for="(field, index) in keyFields" :key="field.key">
          <input-item>
            <textarea name="public_keys{{index}}" v-model.lazy="keyFields[index].value"></textarea>
            <button type="button" @click="keyRemove(index)">Remove Key</button>
          </input-item>
        </div>
        <button type="button" @click="keyPush('')">Add Key</button>
        <div id="submit">
          <input id="form_submit" type="submit" value="Save" />
          <input id="cancel" type="reset" onclick="window.location.reload()" value="Clear" />
        </div>
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
  label {
    vertical-align: top;
  }
  input[type="text"] {
    width: 25em;
  }
}
</style>

<script setup lang="ts">

import InputItem from '../components/InputItem.vue'
import { useForm, useFieldArray } from 'vee-validate'
import * as yup from 'yup'
import { ref } from 'vue'

const user_list = ref([])
const load_user_list = async () => {
  user_list.value = await getUser('', '')
}
load_user_list()

const operation = ref('Create New User')

const schema = yup
  .object({
    user: yup.string().required().lowercase('Username must be lowercase').label('Username'),
    identity_provider_key: yup.string().required().label('Identity Provider Key'),
    identity_provider_module: yup.string().required().label('Your IdP must be for a valid IdP module'),
    ipv4_allow_list: yup
      .string()
      .matches(
        /^(?:(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\/(?:[0-2]?[0-9]|3[0-2])(?:\r?\n)?)+$/,
        'Must be CIDR addresses seperated by line breaks'
      )
      .optional()
      .label('IPv4 Allow List'),
    config_Role: yup.string().required().label('IAM Role ARN'),
    config_argon2_hash: yup.string().when('identity_provider_module', {
      is: 'argon2',
      then: (schema) => schema.required('Argon2 Hash is required when IdP module is Argon2'),
      otherwise: (schema) => schema.notRequired()
    }),
    config_HomeDirectoryType: yup.mixed().oneOf(['LOGICAL', 'PATH']).required(),
    config_HomeDirectory: yup.string().when('config_HomeDirectoryType', {
      is: 'LOGICAL',
      then: (schema) => schema.required('Home Directory is required when type is LOGICAL'),
      otherwise: (schema) => schema.notRequired()
    }),
    config_PosixProfile_Gid: yup.string().optional(),
    config_PosixProfile_Uid: yup.string().optional(),
    

  })
  .strict(true)

const { values, errors, defineField, handleSubmit } = useForm({
  validationSchema: schema,
  initialValues: {
    user: '',
    identity_provider_key: '',
    identity_provider_module: '',
    ipv4_allow_list: '0.0.0.0/0',
    config_Role: '',
    config_HomeDirectoryType: 'PATH',
    config_HomeDirectory: null,
    config_argon2_hash: null,
    config_HomeDirectoryDetails: [{}],
    config_PosixProfile: [{}],
    config_PublicKeys: [],
  }
})

const [user, user_attrs] = defineField('user', {})
const [identity_provider_key, identity_provider_key_attrs] = defineField(
  'identity_provider_key',
  {}
)
const [identity_provider_module] = defineField('identity_provider_module', {})
const [Role, Role_attrs] = defineField('config_Role', {})
const [argon2_hash, argon2_hash_attrs] = defineField('config_argon2_hash', {
  props() {
    return { visible: identity_provider_module.value === 'argon2' }
  }
})
const [HomeDirectoryType, HomeDirectoryType_attrs] = defineField('config_HomeDirectoryType', {})
HomeDirectoryType.value = 'PATH'
const [HomeDirectory, HomeDirectory_attrs] = defineField('config_HomeDirectory', {
  props() {
    return { visible: HomeDirectoryType.value === 'LOGICAL' }
  }
})

const {fields: homeFields, remove: homeRemove, push: homePush, replace: homeReplace} = useFieldArray('config_HomeDirectoryDetails')
const {fields: posixFields, remove: posixRemove, push: posixPush, replace: posixReplace} = useFieldArray('config_PosixProfile')

const {fields: keyFields, remove: keyRemove, push: keyPush, replace: keyReplace} = useFieldArray('config_PublicKeys')
const [ipv4_allow_list, ipv4_allow_list_attrs] = defineField('ipv4_allow_list', {})

const createUser = handleSubmit((values) => {
  console.log(values)
  saveUser()
})

function setIdpModule(event) {
  identity_provider_module.value = event.target.selectedOptions[0].text.split(":")[0]
  console.log('form mode is for IdP module ' + identity_provider_module.value)
}

async function saveUser() {
  const user = {
    config: {
      HomeDirectoryDetails: [{}],
      PosixProfile: [{}],
      PublicKeys: [],
      Role: ''
    },
    ipv4_allow_list: []
  }

  for (let [key, value] of Object.entries(values)) {
    console.log(key, value)
    if (key.startsWith('config_')) {
      const config_key = key.replace('config_', '')
      user.config[config_key] = value
    } else {
      if (key === 'ipv4_allow_list') {
        user.ipv4_allow_list = value.split('\n')
      } else {
        user[key] = value
      }
    }
  }

  let json = {}
  try {
    json = await putUser(user)
  } catch (error) {
    console.log(error)
  } finally {
    console.log('done')
  }
  window.location.reload()
}

async function putUser(user) {
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/user/'
  return await fetch(url, {
    signal,
    method: 'PUT',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(user)
  })
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

async function editUser(user_name, identity_provider) {
  const user_record = await getUser(user_name, identity_provider)
  operation.value = 'Edit or Copy IDP: ' + user_record.user
  user.value = user_record.user
  identity_provider_key.value = user_record.identity_provider_key
  identity_provider_module.value = idp_list.value.find((idp) => idp.provider === user_record.identity_provider_key).module
  ipv4_allow_list.value = user_record.ipv4_allow_list.join('\n')
  Role.value = user_record.config.Role
  HomeDirectoryType.value = user_record.config.HomeDirectoryType
  HomeDirectory.value = user_record.config.HomeDirectory
  keyReplace(user_record.config.PublicKeys)
  homeReplace(user_record.config.HomeDirectoryDetails)
  posixReplace(user_record.config.PosixProfile)
}

async function getUser(user, identity_provider_key) {
  //console.log('getUser: ' + user)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/user/'
  const querystring = '?provider=' + identity_provider_key
  return fetch(url + user+querystring, {
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
      console.log('getUser ' + user + ' failure')
    }
  })
}

function deleteUser(user, identity_provider_key) {
  console.log('deleteUser: ' + user + ' from IdP ' + identity_provider_key)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/user/'
  const querystring = '?provider=' + identity_provider_key
  let result = fetch(url + user+querystring, {
    signal,
    method: 'DELETE',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      console.log('deleteUser success')
      return response.json()
    } else {
      console.log('deleteUser failure')
    }
  })
  console.log('delete result' + result)
  user_list.value = user_list.value.filter((item) => item.user !== user)
  setTimeout(() => load_user_list(), 250) // verbosely reload on delay
}
</script>
