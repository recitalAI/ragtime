<template>
  <div class="home-page-container">
    <main class="main-content page-padding py-7">
      <div
        class="mb-4 d-flex"
        style="justify-content: space-between"
      >
        <h2 class="h2-text mb-4">
          Experiment Dashboard
        </h2>
        <div class="action-buttons">
          <v-btn
            class="mr-3"
            color="primary"
            variant="outlined"
            @click="startExperiment"
            rounded
          >
            <v-icon
              size="17"
              start
            >
              fas fa-flask
            </v-icon>
            Start experiment
          </v-btn>
          <v-btn
            color="primary"
            variant="outlined"
            @click="createValidationSet"
            rounded
          >
            <v-icon
              size="17"
              start
            >
              fas fa-list-check
            </v-icon>
            Create validation set
          </v-btn>
        </div>
      </div>

      <ValidationSetTable />
      <ExperimentTable class="mt-6" />
    </main>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import { formatDate } from '@/utils/dateFormatter';
import ExperimentTable from '@/components/elements/Home/ExperimentTable.vue';
import ValidationSetTable from '@/components/elements/Home/ValidationSetTable';

export default {
  name: 'HomePage',

  components: {
    ExperimentTable,
    ValidationSetTable,
  },

  setup() {
    const router = useRouter();
    const startExperiment = () => {
      router.push('/experiment-setup');
    };

    const createValidationSet = () => {
      router.push('/create-validation-set');
    };

    return {
      startExperiment,
      createValidationSet,
      formatDate,
    };
  }
};
</script>

<style scoped>
.home-page-container {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 250px;
  background-color: #666c63;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.logo {
  margin-bottom: 40px;
}

.logo img {
  width: 100px;
  height: auto;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-grow: 1;
  justify-content: center;
  width: 100%;
}

.sidebar-btn {
  background-color: transparent;
  border: none;
  color: white;
  padding: 15px 20px;
  margin-bottom: 20px;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.3s;
  width: 80%;
  border-radius: 5px;
  font-size: 16px;
  white-space: nowrap;
}

.sidebar-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.bottom-section {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.logout-btn {
  background-color: #e74c3c;
  border: none;
  color: white;
  padding: 10px 20px;
  margin-bottom: 20px;
  text-align: center;
  cursor: pointer;
  transition: background-color 0.3s;
  width: 80%;
  border-radius: 5px;
  font-size: 16px;
}

.logout-btn:hover {
  background-color: #c0392b;
}

.ragtime-logo {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ragtime-logo img {
  width: 80px;
  height: auto;
  margin-bottom: 10px;
}

.ragtime-text {
  font-family: 'Arial', sans-serif;
  font-size: 18px;
  color: #9b59b6;
  font-weight: bold;
}

.main-content {
  flex-grow: 1;
  overflow-y: auto;
}


.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.btn {
  padding: 10px 20px;
  margin-right: 10px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
}

.saved-files-table, .experiments-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.saved-files-table th,
.saved-files-table td,
.experiments-table th,
.experiments-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.saved-files-table th,
.experiments-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.additional-information {
  margin-top: 40px;
}

.error-message {
  color: red;
  font-weight: bold;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  line-height: 1.5;
  border-radius: 0.2rem;
}

.btn-danger {
  color: #fff;
  background-color: #dc3545;
  border-color: #dc3545;
}

.btn-danger:hover {
  color: #fff;
  background-color: #c82333;
  border-color: #bd2130;
}
</style>