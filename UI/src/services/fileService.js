import { http } from '@/plugins/axios';
import { validateData, FormatError } from './validationHelper';

export async function saveJsonFile(data, filename) {
  // Validate data before saving
  const validatedData = validateData(data);
  const response = await http.post('save-json', { data: validatedData, filename });
  return response.data;
}

export async function updateJsonFile(data, newFilename, oldFilename) {
  // Validate data before updating
  const validatedData = validateData(data);
  const response = await http.put('update-json', { 
    data: validatedData, 
    newFilename, 
    oldFilename 
  });
  return response.data;
}

export function loadJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      let data;
      try {
        data = JSON.parse(e.target.result);
      } catch (parseError) {
        reject(new Error(`"${file.name}" is not valid JSON (${parseError.message}).`));
        return;
      }
      try {
        // Normalize and validate the structure (throws FormatError with
        // the expected-format hint when the structure is not supported)
        resolve(validateData(data));
      } catch (error) {
        if (error instanceof FormatError) {
          reject(new Error(`"${file.name}": ${error.message}`));
        } else {
          reject(new Error(`"${file.name}" could not be read: ${error.message}`));
        }
      }
    };
    reader.onerror = () => reject(new Error(`Could not read the file "${file.name}".`));
    reader.readAsText(file);
  });
}
