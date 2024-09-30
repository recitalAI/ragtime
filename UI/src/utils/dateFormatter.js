export function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
  
export function formatDateForBackend(dateString) {
    const date = new Date(dateString);
    return date.toUTCString();
}