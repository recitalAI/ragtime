import { createI18n } from 'vue-i18n';
import en from '@/plugins/i18n/locales/en.json';
import fr from '@/plugins/i18n/locales/fr.json';

export const i18n = createI18n({
  locale: localStorage.getItem('language') || 'en',
  fallbackLocale: localStorage.getItem('language') || 'en',
  messages: { fr, en },
});
