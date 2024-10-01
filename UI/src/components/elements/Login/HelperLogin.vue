<template>
  <div class="helper">
    <p class="text-body-2">
      {{ $t('login.need_help') }}
    </p>
    <v-btn
      id="helper"
      color="primary"
      class="primary--text mt-3"
      target="_blank"
      href="mailto:customersuccess@recital.ai"
      variant="text"
    >
      <v-icon class="mt-4">
        fas fa-envelope
      </v-icon>
      <p
        class="text-body-2 font-weight-semi-bold ml-3"
        style="position: relative; top: 8px;"
      >
        {{ $t('login.email_team') }}
      </p>
    </v-btn>
  </div>
</template>

<script>
export default {
  name: 'HelperLogin',
};
</script>

<style lang="scss" scoped>
.helper {
  & * {
    white-space: nowrap;
  }
}
</style>
