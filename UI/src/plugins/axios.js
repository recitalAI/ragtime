import _axios from 'axios';
import { store } from '@/plugins/store';

const tmpHttp = _axios.create({
  headers: {
    accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor
 */
tmpHttp.interceptors.request.use(
  async function(config) {
    config.baseURL = `${store.getters.config.backend}api/`;
    return config;
  },
  function(error) {
    return Promise.reject(error);
  }
);

/**
 * Init axios
 * @type {AxiosInstance}
 */
export const http = tmpHttp;
