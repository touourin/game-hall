import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './styles.css'
import { initializeTheme } from './theme'

initializeTheme()
createApp(App).use(createPinia()).mount('#app')
