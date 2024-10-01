const { defineConfig } = require('@vue/cli-service')

const globalSassFiles = [
  '@/assets/scss/02-utilities/_variables.scss',
  '@/assets/scss/02-utilities/_functions.scss',
  '@/assets/scss/02-utilities/_mixins.scss',
];

module.exports = defineConfig({
  css: {
    loaderOptions: {
      sass: {
        additionalData: globalSassFiles.map(src => `@import "${src}";`).join('\n'),
      },
    },
  },

  chainWebpack: config => {
    ['vue-modules', 'vue', 'normal-modules', 'normal'].forEach(match => {
      config.module
        .rule('sass')
        .oneOf(match)
        .use('sass-loader')
        .tap(opt => {
          return Object.assign(opt, {
            additionalData: globalSassFiles
              .map(src => `@import "${src}"`)
              .join('\n'),
          });
        });
    });
  },
  transpileDependencies: ['vuetify'],
  pluginOptions: {
    i18n: {
      locale: 'en',
      fallbackLocale: 'en',
      localeDir: 'locales',
      enableInSFC: true,
    },
  },
})
