import _axios from 'axios';
import { store } from '@/plugins/store';

// Default timeout for API calls. Endpoints that trigger LLM calls
// (generation) use LONG_REQUEST instead — they can legitimately take
// minutes for large validation sets.
const DEFAULT_TIMEOUT_MS = 30000;
export const LONG_REQUEST = { timeout: 600000 };

const tmpHttp = _axios.create({
  timeout: DEFAULT_TIMEOUT_MS,
  headers: {
    accept: 'application/json',
    'Content-Type': 'application/json',
  },
});

/**
 * Cancellation on navigation.
 * Every pending request registers an AbortController here; the router calls
 * cancelPendingRequests() on each navigation, so responses for a page the
 * user already left are aborted instead of landing on a dead component.
 */
const pendingControllers = new Set();

export function cancelPendingRequests() {
  pendingControllers.forEach((controller) => controller.abort());
  pendingControllers.clear();
}

export function isCancelled(error) {
  return _axios.isCancel(error);
}

tmpHttp.interceptors.request.use(
  function (config) {
    // baseURL comes from public/data/config.json, loaded into the store at
    // boot (main.js) — resolved per request because config loads async.
    config.baseURL = `${store.getters.config.backend}api/`;
    if (!config.signal) {
      const controller = new AbortController();
      config.signal = controller.signal;
      config._cancelController = controller;
      pendingControllers.add(controller);
    }
    return config;
  },
  function (error) {
    return Promise.reject(error);
  }
);

tmpHttp.interceptors.response.use(
  function (response) {
    if (response.config._cancelController) {
      pendingControllers.delete(response.config._cancelController);
    }
    return response;
  },
  function (error) {
    if (error.config && error.config._cancelController) {
      pendingControllers.delete(error.config._cancelController);
    }
    // Normalized human-readable message, usable directly in snackbars.
    error.isCancelled = _axios.isCancel(error);
    error.userMessage = error.isCancelled
      ? 'Request cancelled'
      : error.response?.data?.error
        || (error.code === 'ECONNABORTED' ? 'The request timed out. Please try again.' : null)
        || error.message
        || 'Network error';
    return Promise.reject(error);
  }
);

export const http = tmpHttp;
