import { createStore } from 'vuex';

export const store = createStore({
  state () {
    return {
      config: {},
      menuOpen: true,
    }
  },

  getters: {
    config: state => state.config,
    menuOpen: state => state.menuOpen,
  },

  mutations: {
    setConfig(state, payload) {
      state.config = payload;
      state.config.loaded = true;
    },
    toggleMenu(state) {
      state.menuOpen = !state.menuOpen;
    },
  },
});