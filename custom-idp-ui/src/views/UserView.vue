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
          <input type="text" name="user" v-model="user" v-bind="user_attrs" />
        </InputItem>
        <InputItem>
          <template #message>{{ errors.identity_provider_key }}</template>
          <template #label
            ><label for="identity_provider_key">Identity Provider Key</label></template
          >
          <select
            name="identity_provider_key"
            v-model="identity_provider_key"
            v-bind="identity_provider_key_attrs"
          >
            <option v-for="idp in idp_list" :value="idp.provider">
              {{ idp.module }}: {{ idp.provider }}
            </option>
          </select>
        </InputItem>
        <InputItem>
          <template #message>{{ errors.config_Role }}</template>
          <template #label><label for="role">IAM Role ARN</label></template>
          <input type="text" name="role" v-model="Role" v-bind="Role_attrs" />
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
          <input type="text" name="role" v-model="HomeDirectory" v-bind="HomeDirectory_attrs" />
        </InputItem>
        <!--
          https://stackoverflow.com/questions/74534399/vue-3-create-dynamic-input
          https://codesandbox.io/p/sandbox/vmj3r80nxy?file=%2Fsrc%2FApp.vue%3A77%2C1
        -->
        <h4>Home Directory Details</h4>
        required
        <h4>Posix Profiles</h4>

        <h4>Public Keys</h4>
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

const operation = ref('Create New User')

// build base level schema for any module type, then add the module specific conditional fields
const schema = yup
  .object({
    user: yup.string().required().lowercase('Username must be lowercase').label('Username'),
    identity_provider_key: yup.string().required().label('Identity Provider Key'),
    ipv4_allow_list: yup.string().required().label('IPv4 Allow List'),
    config_Role: yup.string().required().label('IAM Role ARN'),
    config_HomeDirectoryType: yup.mixed().oneOf(['LOGICAL', 'PATH']).required(),
    config_HomeDirectory: yup.string().when('config_HomeDirectoryType', {
      is: 'LOGICAL',
      then: (schema) => schema.required("Home Directory is required when type is LOGICAL"),
      otherwise: (schema) => schema.notRequired()
    }),
    config_PosixProfile_Gid: yup.number().optional(),
    config_PosixProfile_Uid: yup.number().optional(),
    config_PublicKeys: yup.string().optional(),

    // config_HomeDirectoryDetails_Entry: yup.string().required().label('Home Directory Entry'),
    // config_HomeDirectoryDetails_Target: yup.string().required().label('Home Directory Target'),
    // config_HomeDirectoryDetails_Regions: yup.string().required().label('Home Directory Regions'),
  })
  .strict(true)

const { values, errors, defineField, handleSubmit } = useForm({
  validationSchema: schema
})

const [user, user_attrs] = defineField('user', {})
const [identity_provider_key, identity_provider_key_attrs] = defineField(
  'identity_provider_key',
  {}
)
const [Role, Role_attrs] = defineField('config_Role', {})
const [HomeDirectoryType, HomeDirectoryType_attrs] = defineField('config_HomeDirectoryType', {})
HomeDirectoryType.value = 'PATH'
const [HomeDirectory, HomeDirectory_attrs] = defineField('config_HomeDirectory', {
  props() {
    return { visible: HomeDirectoryType.value === 'LOGICAL' }
  }
})
// HomeDirectoryDetails is a map, and can have multiple entry/target value pairs
// so you have to define the map to hold key/value pairs
const homeDirectoryDetails = ref([])
const [HomeDirectoryDetail_Entry, HomeDirectoryDetail_Entry_attrs] = defineField(
  'config_HomeDirectoryDetail_Entry',
  {}
)
const [HomeDirectoryDetail_Target, HomeDirectoryDetail_Target_attrs] = defineField(
  'config_HomeDirectoryDetail_Target',
  {}
)
const [HomeDirectoryDetail_Region, HomeDirectoryDetail_Region_attrs] = defineField(
  'config_HomeDirectoryDetail_Region',
  {}
)

const [ipv4_allow_list, ipv4_allow_list_attrs] = defineField('ipv4_allow_list', {})

// todo: build UI dynamically, make it adding to a map
function addHomeDirectoryDetails() {
  homeDirectoryDetails.value.push({
    Entry: HomeDirectoryDetail_Entry.value,
    Target: HomeDirectoryDetail_Target.value,
    Region: HomeDirectoryDetail_Region.value
  })
}

addHomeDirectoryDetails()

// todo: you have to have at least 1
function removeHomeDirectoryDetails(index) {
  if (homeDirectoryDetails.value.length > 1) {
    homeDirectoryDetails.value.splice(index, 1)
  }
}

const createUser = handleSubmit((values) => {
  console.log(values)
  putUser()
})

async function putUser() {
  const user = {
    config: {
      HomeDirectoryDetails: {},
      PosixProfile: {},
      PublicKeys: [],
      Role: ''
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
