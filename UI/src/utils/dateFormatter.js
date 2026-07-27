export function formatDate(dateString) {
    if (dateString === null || dateString === undefined || dateString === '') {
      return '\u2014';
    }
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return '\u2014';
    }
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
    if (isNaN(date.getTime())) {
      return new Date().toUTCString();
    }
    return date.toUTCString();
}
