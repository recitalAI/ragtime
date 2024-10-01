<template>
  <div class="logout-view" />
</template>

<script>
export default {
  name: 'LogoutView',
  mounted() {
    localStorage.removeItem('user');
     this.$router.push('/login');
  }
}
</script>
