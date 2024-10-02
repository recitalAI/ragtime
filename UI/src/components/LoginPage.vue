<template>
  <div class="login-container">
    <h1>{{ isLogin ? 'Login' : 'Register' }}</h1>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="email">Email:</label>
        <input type="email" id="email" v-model="email" required>
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" v-model="password" required>
      </div>
      <div v-if="!isLogin" class="form-group">
        <label for="confirmPassword">Confirm Password:</label>
        <input type="password" id="confirmPassword" v-model="confirmPassword" required>
      </div>
      <button type="submit">{{ isLogin ? 'Login' : 'Register' }}</button>
    </form>
    <div class="additional-options">
      <a href="#" @click.prevent="forgotPassword">Forgot Password?</a>
      <p>
        {{ isLogin ? "Don't have an account?" : "Already have an account?" }}
        <a href="#" @click.prevent="toggleMode">{{ isLogin ? 'Register' : 'Login' }}</a>
      </p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { http } from '@/plugins/axios'; // Import the http instance

export default {
  name: 'LoginPage',
  setup() {
    const router = useRouter();
    const email = ref('');
    const password = ref('');
    const confirmPassword = ref('');
    const isLogin = ref(true);
    const error = ref('');

    const handleSubmit = async () => {
      try {
        const response = await http.post('login', {
          email: email.value,
          password: password.value
        });
        
        if (response.data.access_token) {
          localStorage.setItem('jwt_token', response.data.access_token);
          router.push('/');
        } else {
          console.error('No token in response');
        }
      } catch (error) {
        console.error('Login error:', error.response ? error.response.data : error.message);
      }
    };

    const toggleMode = () => {
      isLogin.value = !isLogin.value;
      email.value = '';
      password.value = '';
      confirmPassword.value = '';
      error.value = '';
    };

    const forgotPassword = () => {
      // Implement forgot password functionality
      alert("Forgot password functionality not implemented yet.");
    };

    return {
      email,
      password,
      confirmPassword,
      isLogin,
      error,
      handleSubmit,
      toggleMode,
      forgotPassword
    };
  }
}
</script>

<style scoped>
.login-container {
  max-width: 400px;
  margin: 50px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
  background-color: #f9f9f9;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}

button:hover {
  background-color: #45a049;
}

.additional-options {
  margin-top: 20px;
  text-align: center;
}

.additional-options a {
  color: #2c3e50;
  text-decoration: none;
}

.additional-options a:hover {
  text-decoration: underline;
}

.error-message {
  color: red;
  margin-top: 10px;
  text-align: center;
}
</style>