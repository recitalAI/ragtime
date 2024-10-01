import { createVuetify } from 'vuetify';
import { fr, en } from 'vuetify/locale';
import '@fortawesome/fontawesome-free/css/all.css';
import { aliases, fa } from 'vuetify/iconsets/fa'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/dist/vuetify.min.css';

const vuetify = createVuetify({
  components,
  directives,
  locale: {
    locale: 'en',
    messages: { en, fr },
  },
  theme: {
    defaultTheme: 'lightTheme',
    themes: {
      lightTheme: {
        dark: false,
        variables: {},
        colors: {
          primary: '#502BFF',
          'primary-lighten1': '#9985FF',
          'primary-lighten2': '#CCC2FF',
          'primary-darken1': '#0000CA',
          'primary-darken2': '#14007A',
          'primary-darken3': '#07002D',
          secondary: '#0F64FF',
          'secondary-lighten1': '#6D91FF',
          'secondary-darken1': '#0000CA',
          'secondary-darken2': '#14007A',
          'complementary-yellow': '#F5B941',
          'complementary-pink': '#9B1464',
          warning: '#F5B941',
          error: '#F11A34',
          'error-lighten': '#F56676',
          top: '#DDEDFE',
          success: '#8FF2B8',
          'success-darken': '#02B54C',
          dark: '#101010',
          'grey': '#777',
          'grey-darken1': '#F4F5F9',
          'grey-darken2': '#C8C8C8',
          'grey-darken3': '#969696',
          'grey-darken4': '#4B4B4B',
          'grey-lighten1': '#D1CFCF',
          'grey-lighten2': '#EAEBEE',
          'white': '#FFF',
        },
      }
    }
  },
  icons: {
    defaultSet: 'fa',
    aliases,
    sets: {
      fa,
    },
  },
});

export default vuetify;
