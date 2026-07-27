<template>
  <v-card class="mt-4">
    <v-card-title>
      Experiment Logs
      <v-spacer></v-spacer>
      <v-switch
        :model-value="autoScroll"
        label="Auto-scroll"
        @update:model-value="$emit('update:autoScroll', $event)"
      ></v-switch>
    </v-card-title>
    <v-card-text>
      <div
        ref="logContainer"
        class="log-container"
        @scroll="handleScroll"
      >
        <p v-if="logs.length === 0">Waiting for logs...</p>
        <pre v-for="(log, index) in logs" :key="index">{{ log }}</pre>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
import { nextTick, ref, watch } from 'vue';

export default {
  name: 'LiveLogPanel',
  props: {
    logs: {
      type: Array,
      required: true,
    },
    autoScroll: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['update:autoScroll'],
  setup(props, { emit }) {
    const logContainer = ref(null);

    // The panel owns its DOM: scroll to the bottom when new log lines land
    // and auto-scroll is on (this used to live in the polling loop).
    watch(() => props.logs.length, () => {
      if (props.autoScroll) {
        nextTick(() => {
          if (logContainer.value) {
            logContainer.value.scrollTop = logContainer.value.scrollHeight;
          }
        });
      }
    });

    // Scrolling away from the bottom pauses auto-scroll; returning re-arms it.
    const handleScroll = () => {
      if (logContainer.value) {
        const { scrollTop, scrollHeight, clientHeight } = logContainer.value;
        emit('update:autoScroll', scrollTop + clientHeight >= scrollHeight - 10);
      }
    };

    return { logContainer, handleScroll };
  },
};
</script>

<style scoped>
.log-container {
  height: 300px;
  overflow-y: auto;
  background-color: #f5f5f5;
  padding: 10px;
  font-family: monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
