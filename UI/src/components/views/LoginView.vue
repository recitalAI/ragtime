<template>
  <div class="login h-full">
    <v-container fill-height>
      <v-row
        justify="space-between"
        justify-xl="space-around"
      >
        <v-col
          md="6"
          align="center"
        >
          <LoginLeftMessage />
        </v-col>
        <v-col md="6">
          <LoginForm />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import LoginLeftMessage from '@/components/elements/Login/LoginLeftMessage.vue';
import LoginForm from '@/components/elements/Login/LoginForm.vue';

export default {
  name: 'LoginPage',

  components: {
    LoginForm,
    LoginLeftMessage,
  },
};
</script>

<style lang="scss" scoped>
.login {
  background-image: url('@/assets/login-bg.jpg');
  background-size: cover;
  margin-left: auto;
  display: flex;
  align-items: center;
  padding: 20px 0;
  width: 100%;
}

.h-full {
  height: 100vh;
}

.two-factor {
  position: relative;

  &__help {
    margin-top: 60px;
    position: absolute;
    top: 0;
    left: 100%;
    margin-left: 60px;
  }
}
</style>
