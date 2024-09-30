<template>
  <div class="logo-container">
    <img :src="require('@/assets/recital_logo.png')" alt="Logo 1" class="logo logo-top-left">
    <div class="logo-bottom-left-container">
      <img :src="require('@/assets/Ragtime-logo.png')" alt="Piano Keys" class="logo logo-bottom-left">
      <div class="ragtime-text">Ragtime</div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogoHeader'
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Monoton&display=swap');

.logo-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1000;
}

.logo {
  position: absolute;
  left: 10px;
}

.logo-top-left {
  top: 20px;
  width: 100px; /* Adjust size as needed */
}

.logo-bottom-left-container {
  position: absolute;
  left: 10px;
  bottom: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 80px; /* Match this to the width of your piano keys image */
}

.logo-bottom-left {
  width: 100%; /* This ensures the image takes the full width of its container */
  height: auto; /* Maintain aspect ratio */
}

.ragtime-text {
  font-family: 'Monoton', cursive;
  font-size: 18px; /* Adjusted for better fit */
  color: #6a0dad; /* Deep purple color */
  text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
  margin-top: 5px;
  margin-left: 10px;
  letter-spacing: 1px;
  text-align: center;
  width: 100%; /* Ensure text takes full width of container */
}
</style>