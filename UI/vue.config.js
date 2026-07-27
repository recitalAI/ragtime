const { defineConfig } = require('@vue/cli-service')
const webpack = require('webpack')

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

  configureWebpack: {
    plugins: [
      // Vue 3 (esm-bundler) expects this compile-time feature flag to be
      // defined by the bundler; Vue CLI already defines __VUE_OPTIONS_API__
      // and __VUE_PROD_DEVTOOLS__, but not this one, so it warns on startup
      // and the related dev-only branch isn't tree-shaken from the production
      // build. Defining just the missing flag avoids redefining the other two.
      // See https://link.vuejs.org/feature-flags.
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
      }),
    ],
    resolve: {
      fallback: {
        fs: false,
        path: false,
        crypto: false
      }
    }
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
});