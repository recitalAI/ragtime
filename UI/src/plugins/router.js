import { createRouter, createWebHistory } from 'vue-router';
import HomePage from '@/components/views/HomePage.vue';
import CreateValidationSet from '@/components/CreateValidationSet.vue';
import ModifyValidationSet from '@/components/ModifyValidationSet.vue';
import ExperimentSetup from '@/components/ExperimentSetup.vue';
import ExperimentResults from '@/components/ExperimentResults.vue';
import QuestionEvaluation from '@/components/QuestionEvaluation.vue';
import LoginPage from '@/components/views/LoginView.vue';
import LogoutView from '@/components/views/LogoutView.vue';
import UserSettings from '@/components/UserSettings.vue';

const routes = [
  {
    path: '/',
    name: 'HomePage',
    component: HomePage,
    meta: { requiresAuth: true }
  },
  {
    path: '/create-validation-set',
    name: 'CreateValidationSet',
    component: CreateValidationSet,
    meta: { requiresAuth: true }
  },
  {
    path: '/modify-validation-set',
    name: 'ModifyValidationSet',
    component: ModifyValidationSet,
    meta: { requiresAuth: true }
  },
  {
    path: '/experiment-setup',
    name: 'ExperimentSetup',
    component: ExperimentSetup,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/experiment-results',
    name: 'ExperimentResults',
    component: ExperimentResults,
    props: (route) => ({ path: route.query.path }),
    meta: { requiresAuth: true }
  },
  {
    path: '/question-evaluation/:index',
    name: 'QuestionEvaluation',
    component: QuestionEvaluation,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'LoginPage',
    component: LoginPage
  },
  {
    path: '/settings',
    name: 'UserSettings',
    component: UserSettings,
    meta: { requiresAuth: true }
  },
  {
    path: '/logout',
    name: 'LogoutView',
    component: LogoutView,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
});

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('user');
  
  if (to.matched.some(record => record.meta.requiresAuth) && !isAuthenticated) {
    next('/login');
  } else if (to.path === '/login' && isAuthenticated) {
    next('/');
  } else {
    next();
  }
});

export default router;