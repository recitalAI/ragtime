<template>
  <div id="app">
    <router-view
      :key="$route.fullPath"
      class="router-view"
      :class="{
        'open-router': showSidebar && !menuOpen,
        'closed-router': showSidebar && menuOpen,
        'full-router': !showSidebar,
      }"
    />
    <SideBar v-if="showSidebar" />
  </div>
</template>

<script>
import SideBar from '@/components/elements/general/SideBar';

export default {
  name: 'App',

  components: {
    SideBar,
  },

  computed: {
    showSidebar() {
      return this.$route.meta.requiresAuth;
    },

    menuOpen() {
      return this.$store.getters.menuOpen;
    },
  },
}
</script>

<style lang="scss">
@import './assets/scss/main';

#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  background-color: #f4f5f9 !important;
  min-height: 100vh;
}

.router-view {
  height: fit-content;
  transition: width 300ms, margin-left 300ms;
}

.open-router {
  width: calc(100vw - 60px);
  margin-left: 60px !important;
}

.closed-router {
  width: calc(100vw - 210px);
  margin-left: 210px;
}

.full-router {
  width: 100vw;
  margin-left: 0;
}

.ellipsis {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
</style>