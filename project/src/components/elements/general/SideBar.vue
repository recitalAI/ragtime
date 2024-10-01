<template>
  <aside
    class="sidebar-container"
    :style="{width: menuOpen ? '210px' : '60px'}"
  >
    <div class="fade-in stretch d-flex flex-column justify-space-between sidebar-content">
      <div
        class="recital-logo top-gap bottom-gap-lg"
        :class="{ 'recital-logo-small': !menuOpen }"
        @click="$router.push('/');"
      />
      <nav
        style="margin-left: 20px; font-size: 15px; flex-grow: 1;"
        :style="{'padding-top': menuOpen ? '50px' : '61px' }"
      >
        <div
          v-for="item in menuItems"
          :key="item.text"
          class="clickable menu-item mb-4"
          style="white-space: nowrap;"
          :class="{ 'menu-item-current': $route.path === item.route }"
          @click="$router.push(item.route)"
        >
          <v-icon
            v-if="menuOpen"
            size="18"
            start
          >
            {{ item.icon }}
          </v-icon>
          <v-tooltip
            v-else
            location="right"
          >
            <template #activator="{ props }">
              <div v-bind="props">
                <v-icon
                  size="18"
                  start
                >
                  {{ item.icon }}
                </v-icon>
              </div>
            </template>
            {{ item.text }}
          </v-tooltip>
          <span
            v-if="menuOpen"
            class="fade-in"
          >
            {{ item.text }}
          </span>
        </div>
        <hr
          v-if="menuOpen"
          class="mt-8 mb-8 fade-in"
          style="width: 30px"
          :style="{'margin-left': menuOpen ? '0' : '20px' }"
        >
        <div :style="{'padding-top': menuOpen ? '0px' : '50px' }">
          <div
            v-for="item in lowerMenuItems"
            :key="item.text"
            class="clickable menu-item mb-4"
            style="white-space: nowrap;"
            :class="{ 'menu-item-current': $route.path === item.route }"
            @click="$router.push(item.route)"
          >
            <v-icon
              v-if="menuOpen"
              size="18"
              start
            >
              {{ item.icon }}
            </v-icon>
            <v-tooltip
              v-else
              location="right"
            >
              <template #activator="{ props }">
                <div v-bind="props">
                  <v-icon
                    size="18"
                    start
                  >
                    {{ item.icon }}
                  </v-icon>
                </div>
              </template>
              {{ item.text }}
            </v-tooltip>
            <span
              v-if="menuOpen"
              class="fade-in"
            >
              {{ item.text }}
            </span>
          </div>
        </div>
      </nav>
      <div
        class="d-flex flex-column footer-section"
        :style="{'padding-bottom': menuOpen ? '20px' : '37px' }"
      >
        <a
          href="https://github.com/recitalAI/ragtime-package"
          target="_blank"
        >
          <div
            class="clickable mb-4 menu-item"
            style="white-space: nowrap;"
          >
            <v-icon
              v-if="menuOpen"
              size="18"
              start
            >
              fa-brands fa-github
            </v-icon>
            <v-tooltip
              v-else
              location="right"
            >
              <template #activator="{ props }">
                <div v-bind="props">
                  <v-icon
                    size="18"
                    start
                  >
                    fa-brands fa-github
                  </v-icon>
                </div>
              </template>
              RAGtime on GitHub
            </v-tooltip>
            <span
              v-if="menuOpen"
              class="fade-in"
            >
              RAGtime on GitHub
            </span>
          </div>
        </a> 
        <small
          v-if="menuOpen"
          class="fade-in"
        >
          Made with <v-icon>fas fa-heart</v-icon> by reciTAL
        </small>
      </div>
    </div>
    <div
      class="sidebar-button clickable"
      @click="$store.commit('toggleMenu')"
    >
      <v-icon
        v-if="menuOpen"
        style="margin-top: -10%; margin-left: -2px"
        size="16"
      >
        fas fa-chevron-left
      </v-icon>
      <v-icon
        v-else
        style="margin-top: -10%; margin-left: 0px"
        size="16"
      >
        fas fa-chevron-right
      </v-icon>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'SideBar',

  data() {
    return {
      menuItems: [
        { icon: 'fas fa-dashboard', text: 'Dashboard', route: '/' },
        { icon: 'fas fa-flask', text: 'Start experiment', route: '/experiment-setup' },
        { icon: 'fas fa-list-check', text: 'Create validation set', route: '/create-validation-set' },
      ],
      lowerMenuItems: [
        { icon: 'fas fa-user', text: 'Profile settings', route: '/settings' },
        { icon: 'fas fa-sign-out-alt', text: 'Logout', route: '/logout' },
      ],
    };
  },

  computed: {
    menuOpen() {
      return this.$store.getters.menuOpen;
    },
  },
};
</script>

<style lang="scss" scoped>
.sidebar-container {
  position: fixed;
  top: 0px;
  left: 0px;
  bottom: 0px;
  background-color: rgb(var(--v-theme-primary-darken3));
  z-index: 999;
  transition: width 300ms;

  .sidebar-content {
    right: unset;
    color: white;
  }
}

.sidebar-button {
  text-align: center;
  position: absolute;
  right: -12px;
  color: rgb(var(--v-theme-primary-darken3)) !important;
  top: 65px;
  background-color: rgb(var(--v-theme-primary-lighten2));
  width: 24px;
  height: 24px;
  border-radius: 50%;
  visibility: hidden;
  opacity: 0;
  transition: visibility 0.3s, opacity 0.3s;
}

.sidebar-container:hover .sidebar-button {
  visibility: visible;
  opacity: 1,
}

.recital-logo {
  margin-left: 8px;
  margin-top: 26px;
  height: 50px;
  width: 175px;
  background-size: contain;
  background-image: url('~@/images/logo_white_bg.svg');
  cursor: pointer;

  &-small {
    background-size: cover;
    width: 39px;
    height: 39px;
  }
}

.menu-item {
  color: white;
}

.menu-item:hover, .menu-item-current{
  color: rgb(var(--v-theme-primary-lighten2));
}

.footer-section {
  color: #ffffff88;
  font-size: 14px;
  padding-right: 10px;
  padding-left: 20px;
  transition: opacity 0.2s;
}
</style>