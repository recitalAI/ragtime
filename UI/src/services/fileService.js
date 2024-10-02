import { http } from '@/plugins/axios';


export async function saveJsonFile(data, filename) {
  try {
    const response = await http.post('save-json', { data, filename });
    return response.data;
  } catch (error) {
    console.error('Error saving JSON file:', error);
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('Error response from server:', error.response.data);
      console.error('Error status:', error.response.status);
      console.error('Error headers:', error.response.headers);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response received:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('Error setting up request:', error.message);
    }
    throw error;
  }
}

export async function updateJsonFile(data, newFilename, oldFilename) {
  try {
    const response = await http.put('update-json', { data, newFilename, oldFilename });
    return response.data;
  } catch (error) {
    console.error('Error updating JSON file:', error);
    throw error;
  }
}


export function loadJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        resolve(data);
      } catch (error) {
        reject(new Error('Invalid JSON file'));
      }
    };
    reader.onerror = (error) => reject(error);
    reader.readAsText(file);
  });
}