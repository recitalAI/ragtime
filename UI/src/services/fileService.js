import { http } from '@/plugins/axios';
import { validateData } from './validationHelper';

export async function saveJsonFile(data, filename) {
  try {
    // Validate data before saving
    const validatedData = validateData(data);
    const response = await http.post('save-json', { data: validatedData, filename });
    return response.data;
  } catch (error) {
    console.error('Error saving JSON file:', error);
    if (error.response) {
      console.error('Error response from server:', error.response.data);
      console.error('Error status:', error.response.status);
      console.error('Error headers:', error.response.headers);
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error setting up request:', error.message);
    }
    throw error;
  }
}

export async function updateJsonFile(data, newFilename, oldFilename) {
  try {
    // Validate data before updating
    const validatedData = validateData(data);
    const response = await http.put('update-json', { 
      data: validatedData, 
      newFilename, 
      oldFilename 
    });
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
        // Validate data after loading
        const validatedData = validateData(data);
        resolve(validatedData);
      } catch (error) {
        reject(new Error('Invalid JSON file'));
      }
    };
    reader.onerror = (error) => reject(error);
    reader.readAsText(file);
  });
}