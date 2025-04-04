import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import SmartTable from 'vuejs-smart-table'

import '@docsearch/css';
const app = createApp(App)


app.use(createPinia())
app.use(router)
app.use(SmartTable)

app.mount('#app')
