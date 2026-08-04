import { ref, onMounted, onUnmounted } from 'vue';

/**
 * Shared "are we online?" guard used before launching any generation
 * (answer / fact / evaluation). Two layers:
 *
 * 1. ensureOnline() — a fast, zero-cost frontend short-circuit that reads
 *    navigator.onLine. It flips to false when the *browser* has no network at
 *    all (cable unplugged, Wi-Fi off, airplane mode). Cheap, so we call it
 *    before every generation launch to avoid even hitting the server when the
 *    user's machine is plainly offline.
 *
 * 2. handleOfflineError(err) — the authoritative check. The generation calls
 *    leave from the *backend* (the container), whose outbound access is a
 *    different network than the browser's: navigator.onLine can say "online"
 *    while the container cannot reach the providers. The backend therefore
 *    gates every generation endpoint and returns HTTP 503 { code: 'offline' }
 *    when it has no outbound internet. When a launch fails with that, call
 *    handleOfflineError(err) to show the same popup instead of a generic error.
 *
 * Usage:
 *   const { showOfflineDialog, ensureOnline, handleOfflineError } = useConnectivityGuard();
 *   const generateAnswers = async () => {
 *     if (!ensureOnline()) return;                 // cheap frontend check
 *     try { ... }
 *     catch (err) {
 *       if (handleOfflineError(err)) return;       // backend said offline -> popup
 *       // ...otherwise handle the error normally
 *     }
 *   };
 * and bind <OfflineDialog v-model="showOfflineDialog" /> in the template.
 */
export function useConnectivityGuard() {
  // Default to true so we never block when the API is unavailable (e.g. SSR
  // or an old browser): only a definite `false` from the browser blocks.
  const isOnline = ref(typeof navigator !== 'undefined' && navigator.onLine !== undefined
    ? navigator.onLine
    : true);
  const showOfflineDialog = ref(false);

  const update = () => {
    isOnline.value = navigator.onLine;
    // If the connection comes back while the dialog is open, close it.
    if (isOnline.value) showOfflineDialog.value = false;
  };

  onMounted(() => {
    window.addEventListener('online', update);
    window.addEventListener('offline', update);
  });

  onUnmounted(() => {
    window.removeEventListener('online', update);
    window.removeEventListener('offline', update);
  });

  /**
   * Fast frontend check. Returns true when the browser reports a connection.
   * When the browser is offline, opens the blocking dialog and returns false
   * so the caller can abort the launch: `if (!ensureOnline()) return;`
   */
  const ensureOnline = () => {
    // Re-read live rather than trusting the last event, in case no event fired.
    isOnline.value = typeof navigator !== 'undefined' ? navigator.onLine : true;
    if (!isOnline.value) {
      showOfflineDialog.value = true;
      return false;
    }
    return true;
  };

  /**
   * True if an error is the backend's "no outbound internet" 503 response
   * (the container is offline even though the browser is online). Detects it
   * from the HTTP status and the { code: 'offline' } payload the backend
   * sends. Works with axios-style errors (err.response.*).
   */
  const isOfflineError = (err) => {
    const resp = err && err.response;
    if (!resp) return false;
    const data = resp.data || {};
    return resp.status === 503 && data.code === 'offline';
  };

  /**
   * If `err` is the backend offline response, open the popup and return true
   * (caller should stop). Otherwise return false so the caller handles the
   * error normally.
   */
  const handleOfflineError = (err) => {
    if (isOfflineError(err)) {
      showOfflineDialog.value = true;
      return true;
    }
    return false;
  };

  return { isOnline, showOfflineDialog, ensureOnline, isOfflineError, handleOfflineError };
}
