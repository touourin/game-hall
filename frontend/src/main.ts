import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles.css'
import { initializeTheme } from './theme'
import { router } from './router'

initializeTheme()
createApp(App).use(createPinia()).use(router).mount('#app')
