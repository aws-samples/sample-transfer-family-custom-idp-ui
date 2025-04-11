<template>
  <div class="row" id="users">
    <div class="col-8"><h2>Existing Users</h2></div>
    <div class="col-1" style="text-align: right"><label>Filter:</label></div>
    <div class="col-2" style="text-align: right">
      <input v-model="filters.name.value" class="filter" />
    </div>
  </div>
  <div class="row">
    <div class="user_list" v-if="user_list.length > 0">
      <VTable :data="user_list" :filters="filters" class="table table-sm table-striped table-hover">
        <template #head>
          <VTh sortKey="user">Username</VTh>
          <VTh sortKey="identity_provider_key">IdP Key</VTh>
          <VTh sortKey="identity_provider_module">Module Type</VTh>
          <VTh sortKey="config.Role">Role</VTh>
          <th>Actions</th>
        </template>
        <template #body="{ rows }">
          <tr v-for="row in rows" :key="row.user">
            <td>{{ row.user }}</td>
            <td>{{ row.identity_provider_key }}</td>
            <td>{{ row.identity_provider_module }}</td>
            <td>{{ row.config.Role }}</td>
            <td>
              <button
                v-on:click="editUser(row.user, row.identity_provider_key)"
                class="btn btn-secondary"
              >
                Edit or Copy
              </button>
              <button
                v-on:click="confirmDelete(row.user, row.identity_provider_key)"
                class="btn btn-danger"
              >
                Delete
              </button>
            </td>
          </tr>
        </template>
      </VTable>
    </div>
    <div v-else>{{ user_load_msg }}</div>
    <div class="modal fade" id="id-of-modal" data-bs-backdrop="static" data-bs-keyboard="false" tabindex="-1" aria-labelledby="staticBackdropLabel" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
            <div class="modal-header">
              <h1 class="modal-title fs-5" id="exampleModalToggleLabel2">Confirm Delete</h1>
            </div>
            <div class="modal-body">
              Are you sure you want to delete <strong>{{ userToDelete }}</strong> from the <strong>{{ userToDeleteIdp}}</strong> Identity Provider? Confirming will immediately remove access for {{ userToDelete }}.
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-warning" @click="closeModal">Cancel</button>
              <button type="button" class="btn btn-danger" @click="deleteUser">Confirm Delete</button>
            </div>
          </div>
      </div>
    </div>
  </div>
  <div class="row user" v-if="idp_list.length > 0">
    <h2>{{ operation }}</h2>
    <!--      <p>ToDo: display success messages for deletes and saves</p>-->
    <form id="user-form" class="form-inline" v-on:submit.prevent="createUser()">
      <InputItem>
        <template #message>{{ errors.user }}</template>
        <template #label><label for="user">Username</label></template>
        <input
          placeholder="in lowercase"
          type="text"
          id="user"
          v-model="user"
          v-bind="user_attrs"
        />
      </InputItem>
      <InputItem>
        <template #message
          >{{ errors.identity_provider_key }}
          <span v-if="errors.identity_provider_module">
            <br />{{ errors.identity_provider_module }}
          </span>
        </template>
        <template #label><label for="identity_provider_key">Identity Provider Key</label></template>
        <select
          id="identity_provider_key"
          name="identity_provider_key"
          v-model="identity_provider_key"
          v-bind="identity_provider_key_attrs"
          v-on:change="setIdpModule"
        >
          <option disabled value="">Choose IDP</option>
          <option v-for="option in idp_list" :value="option.provider" :key="option.provider">
            {{ option.module }}: {{ option.provider }}
          </option>
        </select>
      </InputItem>
      <InputItem>
        <template #message>{{ errors.config_Role }}</template>
        <template #label><label for="role">IAM Role ARN</label></template>
        <input
          placeholder="arn:aws:iam::<account-id>:role/<role-name>"
          type="text"
          id="role"
          v-model="Role"
          v-bind="Role_attrs"
        />
      </InputItem>
      <InputItem v-if="argon2_hash_attrs.visible">
        <template #message>{{ errors.config_argon2_hash }}</template>
        <template #label><label for="argon2_hash">Argon2 Hash</label></template>
        <input
          placeholder="$argon2i$v=19$m=4096,t=3,p=$argon2i$v=19$m=4096,t=3,p=XX"
          type="text"
          id="argon2_hash"
          v-model="argon2_hash"
          v-bind="argon2_hash_attrs"
        />
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
        <input
          placeholder="S3 or EFS path"
          type="text"
          name="role"
          v-model="HomeDirectory"
          v-bind="HomeDirectory_attrs"
        />
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
      <button type="button" @click="homePush('')" class="btn btn-secondary">
        Add Home Directory Detail
      </button>
      <div v-for="(field, index) in homeFields" :key="field.key">
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
          <button type="button" @click="homeRemove(index)" class="btn btn-warning">
            Remove Detail
          </button>
        </input-item>
      </div>

      <h4>Posix Profiles</h4>
      <button type="button" @click="posixPush('')" class="btn btn-secondary">
        Add Posix Profile
      </button>
      <div v-for="(field, index) in posixFields" :key="field.key">
        <input-item>
          <template #label><label :for="'gid' + index">Gid</label></template>
          <input type="text" :id="'gid' + index" v-model.lazy="posixFields[index].value['Gid']" />
        </input-item>
        <input-item>
          <template #label><label :for="'uid' + index">Uid</label></template>
          <input type="text" :id="'uid' + index" v-model.lazy="posixFields[index].value['Uid']" />
          <button type="button" @click="posixRemove(index)" class="btn btn-warning">
            Remove Profile
          </button>
        </input-item>
      </div>

      <h4>Public Keys</h4>
      <button type="button" @click="keyPush('')" class="btn btn-secondary">Add Key</button>
      <div v-for="(field, index) in keyFields" :key="field.key">
        <input-item>
          <textarea name="public_keys{{index}}" v-model.lazy="keyFields[index].value"></textarea>
          <button type="button" @click="keyRemove(index)" class="btn btn-warning">
            Remove Key
          </button>
        </input-item>
      </div>

      <div id="complete">
        <input id="form_submit" type="submit" value="Save" class="btn btn-primary" />
        <input
          id="cancel"
          type="reset"
          onclick="window.location.reload()"
          value="Clear"
          class="btn btn-warning"
        />
      </div>
    </form>
  </div>
  <div class="row" v-else>
    <p>{{ idp_load_msg }}</p>
  </div>
</template>

<style>
@media (min-width: 1024px) {
  .user_list {
    margin-bottom: 1.5em;
    margin-top: 1em;
    height: 250px;
    overflow-y: scroll;
  }
  .filter {
    width: 200px;
    text-align: right;
  }
  .user {
    min-height: 100vh;
    display: flex;
  }
  #users {
    margin-top: 1rem;
  }
  label {
    vertical-align: top;
  }
  input[type='text'] {
    width: 25em;
    display: block;
  }
  thead th {
    position: sticky;
    top: 0;
    background-color: var(--bs-table-bg);
  }
  .btn {
    margin-right: 0.75rem;
  }
  #complete {
    margin-top: 1rem;
    text-align: center;
  }
  h4 {
    margin-top: 0.3rem;
  }
  textarea {
    display: block;
    width: 25em;
  }
  button {
    display: block;
    margin-top: 0.3rem;
  }
}
</style>

<script setup lang="ts">

import InputItem from '../components/InputItem.vue'
import { useForm, useFieldArray } from 'vee-validate'
import * as yup from 'yup'
import { onMounted, ref } from 'vue'
import { Modal } from 'bootstrap'
import { fetchAuthSession } from '@aws-amplify/auth'

onMounted(async => {
  modal.value = new Modal('#id-of-modal', {})
})

const modal = ref(null)
const userToDelete = ref(null)
const userToDeleteIdp = ref(null)

const token = ref(null)
const setToken = async () => {
  const auth =  await fetchAuthSession();
  token.value = auth.tokens.accessToken
}

function confirmDelete(user, identity_provider_key) {
  console.log("user: " + user + " idp: " + identity_provider_key)
  userToDelete.value = user
  userToDeleteIdp.value = identity_provider_key
  modal.value.show();
}

function closeModal() {
  modal.value.hide();
}



const user_list = ref([])
const load_user_list = async () => {
  user_list.value = await getUser('', '')
  console.log(user_list.value)
  if (user_list.value.length == 0) {
    user_load_msg.value = 'No users have been created'
  }
}
load_user_list()

const filters = ref(
  {name: { value: '', keys: ['user', 'identity_provider_key', 'identity_provider_module', 'config.Role'] }}
)

const operation = ref('Create New User')

const schema = yup
  .object({
    user: yup.string().required().lowercase('Username must be lowercase')
      .matches(/^\S+$/, "Username cannot contain spaces").label('Username'),
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
      'Authorization': 'Bearer ' + token.value,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(user)
  }).catch(error => {
    console.log("Failed to update user " + user, error)
    return false
  })
}

const idp_list = ref([])
const load_idp_list = async () => {
  await setToken()
  idp_list.value = await getIdps()
}
const idp_load_msg = ref("Please create an IDP before adding users.")
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
      'Authorization': 'Bearer ' + token.value,
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      return response.json()
    } else {
      console.log('getIdps failure')
    }
  }).catch(error => {
    console.log("Failed to load IDP list", error)
    idp_load_msg.value = "Failed to load IDP list, check your connection to the datasource."
    return []
  })
  return result
}

async function editUser(user_name, identity_provider) {
  const user_record = await getUser(user_name, identity_provider)
  operation.value = 'Edit or Copy IDP: ' + user_record.user
  user.value = user_record.user
  identity_provider_key.value = user_record.identity_provider_key
  identity_provider_module.value = idp_list.value.find((idp) => idp.provider === user_record.identity_provider_key).module
  argon2_hash.value = user_record.config.argon2_hash
  ipv4_allow_list.value = user_record.ipv4_allow_list.join('\n')
  Role.value = user_record.config.Role
  HomeDirectoryType.value = user_record.config.HomeDirectoryType
  HomeDirectory.value = user_record.config.HomeDirectory
  keyReplace(user_record.config.PublicKeys)
  if (user_record.HomeDirectoryDetails) {
    homeReplace(user_record.config.HomeDirectoryDetails)
  }
  if (user_record.config.PosixProfile.length > 0) {
    posixReplace(user_record.config.PosixProfile)
  }
}

const user_load_msg = ref("Loading Users...")
async function getUser(user, identity_provider_key) {
  await setToken()
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/user/'
  const querystring = '?provider=' + identity_provider_key
  return fetch(url + user+querystring, {
    signal,
    method: 'GET',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Authorization': 'Bearer ' + token.value,
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      return response.json()
    } else {
      console.log('getUser ' + user + ' failure')
    }
  }).catch(error => {
    console.log("Failed to load user: " + user + ", provider: " + identity_provider_key, error)
    user_load_msg.value = "Failed to load User list, check your connection to the datasource."
    return []
  })

}

function deleteUser() {
  console.log('deleteUser: ' + userToDelete.value + ' from IdP ' + userToDeleteIdp.value)
  const signal = AbortSignal.timeout(3000)
  const url = 'http://localhost:8080/api/user/'
  const querystring = '?provider=' + userToDeleteIdp.value
  let result = fetch(url + userToDelete.value+querystring, {
    signal,
    method: 'DELETE',
    mode: 'cors',
    cache: 'no-cache',
    headers: {
      'Authorization': 'Bearer ' + token.value,
      'Content-Type': 'application/json'
    }
  }).then((response) => {
    if (response.ok) {
      console.log('deleteUser success')
      return response.json()
    } else {
      console.log('deleteUser failure')
    }
  }).catch(error => {
    console.log("Failed to delete user " + userToDelete.value, error)
    return false
  })
  console.log('delete result' + result)
  userToDelete.value = null;
  userToDeleteIdp.value = null;
  modal.value.hide();
  user_list.value = user_list.value.filter((item) => item.user !== userToDelete.value)
  setTimeout(() => load_user_list(), 250) // verbosely reload on delay
}
</script>
