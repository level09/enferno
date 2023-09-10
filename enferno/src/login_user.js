import { createApp } from 'vue';
import Index from "./pages/Index.vue";
import './index.css';
import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.min.css'

const vuetify = createVuetify({
    components,
  directives,
    icons: {
        iconfont: 'mdi',
    },
});

const app = createApp(Index);

app.use(vuetify).mount('#app');

