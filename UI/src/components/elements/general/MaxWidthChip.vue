<template>
  <v-chip
    class="max-width-chip mb-2 mr-2"
    style="padding-left: 12px;"
    variant="outlined"
    :class="{ 'small-chip': small }"
    :style="{
      'max-width': showFull ? '' : `${maxWidth}px !important`,
      'background-color': `${color}60 !important`,
      'border-color': `${color} !important`,
      'opacity': loaded ? 1 : 0,
      'padding-right': closeable ? '30px' : '12px',
    }"
    @mouseenter="$emit('hover')"
  >
    <div
      ref="itemName"
      style="opacity: 0"
    >
      <span
        v-for="(text, k) in textArray"
        :key="k"
      >
        {{ text }}
      </span>
    </div>
    <v-tooltip
      v-if="tooLong"
      color="#423F4F"
      right
    >
      <template #activator="{ props }">
        <div
          class="stretch d-flex align-center"
          v-bind="props"
        >
          <div
            class="chip-value ellipsis"
            :style="{
              'max-width': showFull ? '' : `${maxWidth}px !important`,
            }"
          >
            <span
              v-for="(text, k) in textArray"
              :key="k"
            >
              {{ text }}
            </span>
          </div>
        </div>
      </template>
      <span
        v-for="(text, k) in textArray"
        :key="k"
        style="color: white"
      >
        {{ text }}
      </span>
    </v-tooltip>
    <div
      v-else
      class="stretch d-flex align-center"
    >
      <div class="chip-value">
        <span
          v-for="(text, k) in textArray"
          :key="k"
        >
          {{ text }}
        </span>
      </div>
    </div>
    <v-icon
      v-if="closeable"
      class="close-icon"
      color="black"
      size="14"
      @click="$emit('closeClick')"
    >
      fas fa-times
    </v-icon>
  </v-chip>
</template>

<script>
export default {
  name: 'MaxWidthChip',

  data() {
    return ({
      loaded: false,
      tooSmall: false,
    });
  },

  computed: {
    tooLong() {
      this.loaded;
      const itemName = this.$refs.itemName;
      return !this.showFull && (
        itemName && itemName.offsetWidth >= this.maxWidth - 24 ||
        this.tooSmall
      );
    },
  },

  mounted() {
    this.loaded = true;
  },

  props: {
    color: {
      type: String,
      default: '#502BFF',
    },

    textArray: {
      type: Array,
      required: true,
    },

    closeable: {
      type: Boolean,
      default: false,
    },

    showFull: {
      type: Boolean,
      default: false,
    },

    small: {
      type: Boolean,
      default: false,
    },

    maxWidth: {
      type: Number,
      default: 180,
    },
  },

  emits: ['hover', 'closeClick'],
}
</script>

<style lang="scss" scoped>
.max-width-chip {
  text-transform: none !important;
  color: rgba(0, 0, 0, 0);
  overflow: hidden !important;
  white-space: nowrap !important;
  text-overflow: ellipsis !important;

  .chip-value {
    min-width: 100px;
    color: black;
    padding-left: 12px;
    padding-right: 20px;
  }

  .close-icon {
    position: absolute;
    right: 7px;
    top: 7px;
  }
}

.small-chip {
  font-size: 0.7rem !important;
  height: 25px !important;
}
</style>
