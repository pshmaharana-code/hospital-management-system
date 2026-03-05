import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router' // <--- Importing our new map!

const app = createApp(App)

app.use(createPinia()) // Activates the global state vault
app.use(router)        // Activates the router so <RouterView> works!

app.mount('#app')