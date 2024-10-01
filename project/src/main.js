import { createApp } from 'vue'
import App from './App.vue'
import router from './plugins/router';
import vuetify from './plugins/vuetify';
import { i18n } from './plugins/i18n/i18n';
import loadConfig from './plugins/config/loadConfig';
import { store } from './plugins/store';


const app = createApp(App);

app.config.productionTip = false;

loadConfig().then(config => {
  if (config) {
    app.use(i18n);
    app.use(router);
    app.use(store);
    app.use(vuetify);

    app.component('App', App);

    const instance = app.mount('#app');

    store.commit('setConfig', config);

    window.app = instance;
  }
});
