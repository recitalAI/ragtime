<template>
  <v-card class="loginForm">
    <v-card-title
      class="h3-text text-primary"
      style="margin-left: -16px"
    >
      {{ $t('login.log_in') }}
    </v-card-title>
    <div class="section1">
      <v-form
        id="form-login"
        ref="form"
        v-model="valid"
        class="mt-8"
        @submit.prevent="validate()"
      >
        <div class="label text-field-label">
          {{ $t('forms.email') }}
        </div>
        <v-text-field
          id="email"
          v-model="emailField"
          class="mt-0"
          variant="outlined"
          color="primary"
          density="compact"
          placeholder="ie «johndoe@email.com»"
          :rules="emailRules"
          @keyup.enter="onEnter"
          required
        />
        <div class="label text-field-label">
          {{ $t('forms.password') }}
        </div>
        <v-text-field
          id="password"
          v-model="password"
          class="mt-0"
          placeholder="••••••••"
          variant="outlined"
          color="primary"
          density="compact"
          :rules="passwordRules"
          :type="visible ? 'text' : 'password'"
          :append-icon="visible ? 'fas fa-eye' : 'fas fa-eye-slash'"
          @click:append="() => (visible = !visible)"
          @keyup.enter="onEnter"
          required
        />
      </v-form>
      <div
        v-if="expired"
        class="d-flex warning-box mt-6 px-4 py-2"
      >
        <div>
          <i class="fas fa-info mr-3" />
        </div>
        {{ $t('login.expired_password') }} {{ $t('login.we_will_email') }}
      </div>
      <v-btn
        id="submit-login"
        class="mt-5"
        color="primary"
        type="submit"
        style="padding: 14px !important"
        @click="validate()"
        rounded
        block
      >
        <v-icon
          v-if="loginStarted"
          style="top: -2px; margin-right: 5px;"
          size="16"
          color="white"
        >
          fas fa-spinner fa-pulse
        </v-icon>
        {{ $t('login.log_in') }}
      </v-btn>
      <v-btn
        id="forgot"
        class="mt-3 bottom-gap"
        color="primary"
        variant="text"
        @click="lostPassword()"
      >
        {{ $t('login.forgot_password') }}
      </v-btn>
    </div>
    <HelperLogin class="mt-10" />
  </v-card>
</template>

<script>
import HelperLogin from '@/components/elements/Login/HelperLogin';
import FormRules from '@/utils/FormRules';

export default {
  name: 'LoginForm',

  components: {
    HelperLogin,
  },

  data: () => ({
    valid: true,
    error: '',
    password: '',
    visible: false,
    emailField: '',
    returnUrl: '/',
    expired: false,
    loginStarted: false,
    loginFailureTimeout: null,
    orgSlug: null,
    loginMethods: null,
    orgId: null,
    orgName: null,
  }),

  computed: {
    passwordRules() {
      const error = this.$t('forms.password_required');
      return [v => !!v || error]
    },

    emailRules() {
      const required_error = this.$t('forms.email_required');
      const valid_error = this.$t('forms.email_must_valid');
      return [
        v => !!v || required_error,
        v => FormRules.emailLocal(v) || valid_error,
      ]
    }
  },

  async created() {
    const language = this.validateLanguage(navigator.language.substring(0, 2));
    localStorage.setItem('language', language || 'en');
    this.returnUrl = this.$route.query.returnUrl || '/';
  },

  methods: {
    async loginMethod() {
      // Here you would typically make an API call to authenticate or register the user
      // For now, we'll just simulate a successful login/registration
      localStorage.setItem('user', JSON.stringify({ email: this.emailField }));
      this.$router.push('/');
    },

    validate() {
      const isValid = this.$refs.form.validate();
      if (isValid) {
        this.loginMethod();
      }
    },

    onEnter() {
      this.validate();
    },

    lostPassword() {
      // Implement forgot password functionality
      alert("Forgot password functionality not implemented yet.");
    },

    validateLanguage(language) {
      const acceptedLanguages = ["en", "fr"];
      if (acceptedLanguages.includes(language)) {
        return language
      }
      return
    },
  },
};
</script>

<style lang="scss" scoped>
.loginForm {
  padding: 30px;

  &__field {
    &:not(:first-child) {
      margin-top: 15px;
    }
  }

  &__submit {
    margin-top: 30px;
  }

  &__forgot {
    margin-top: 30px;
    margin-bottom: 1000px;
  }

  & .warning-box {
    color: rgb(var(--v-theme-primary));
    background-color: rgb(var(--v-theme-primary-lighten2));
    border: 1px solid var(--v-primary--base);
    border-radius: 10px;
  }

  .text-field-label {
    margin-bottom: 3px;
  }
}
</style>
