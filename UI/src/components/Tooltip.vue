<template>
  <span class="tooltip" ref="tooltipContainer">
    <slot></slot>
    <span class="info-icon" @mouseenter="showTooltip" @mouseleave="hideTooltip" ref="infoIcon">
      <i class="fas fa-info-circle"></i>
    </span>
    <Teleport to="body">
      <span class="tooltip-text" :class="{ 'show': isVisible }" ref="tooltipText">{{ text }}</span>
    </Teleport>
  </span>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue';

export default {
  name: 'CustomTooltip',
  props: {
    text: {
      type: String,
      required: true,
    },
  },
  setup() {  // Removed 'props' parameter
    const isVisible = ref(false);
    const tooltipContainer = ref(null);
    const infoIcon = ref(null);
    const tooltipText = ref(null);

    const showTooltip = () => {
      isVisible.value = true;
      requestAnimationFrame(positionTooltip);
    };

    const hideTooltip = () => {
      isVisible.value = false;
    };

    const positionTooltip = () => {
      if (!infoIcon.value || !tooltipText.value) return;

      const infoIconRect = infoIcon.value.getBoundingClientRect();
      const tooltipRect = tooltipText.value.getBoundingClientRect();

      let left = infoIconRect.left + window.scrollX + (infoIconRect.width - tooltipRect.width) / 2;
      let top = infoIconRect.top + window.scrollY - tooltipRect.height - 10;

      // Ensure the tooltip doesn't go off-screen
      if (left < 0) left = 0;
      if (left + tooltipRect.width > window.innerWidth) left = window.innerWidth - tooltipRect.width;
      if (top < 0) top = infoIconRect.bottom + window.scrollY + 10;

      tooltipText.value.style.left = `${left}px`;
      tooltipText.value.style.top = `${top}px`;
    };

    const handleResize = () => {
      if (isVisible.value) {
        requestAnimationFrame(positionTooltip);
      }
    };

    onMounted(() => {
      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, true);
    });

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleResize, true);
    });

    return {
      isVisible,
      tooltipContainer,
      infoIcon,
      tooltipText,
      showTooltip,
      hideTooltip,
    };
  },
};
</script>

<style scoped>
.tooltip {
  position: relative;
  display: inline-flex;
  cursor: pointer;
}

.info-icon {
  font-size: 1.2em;
  color: rgb(var(--v-theme-primary));
  margin-left: 4px;
}

.tooltip-text {
  visibility: hidden;
  width: 200px;
  background-color: #333;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px;
  position: fixed;
  z-index: 9999;
  opacity: 0;
  transition: opacity 0.3s, visibility 0.3s;
  pointer-events: none;
}

.tooltip-text.show {
  visibility: visible;
  opacity: 1;
}
</style>