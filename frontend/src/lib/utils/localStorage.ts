import { logger } from '@/lib/logger';

const SECRET_KEY = process.env.NEXT_PUBLIC_LOCAL_STORAGE_SECRET_KEY || 'supersecretkey';

const encrypt = (text: string): string => {
  return btoa(text.split('').map((char, i) =>
    String.fromCharCode(char.charCodeAt(0) ^ SECRET_KEY.charCodeAt(i % SECRET_KEY.length)),
  ).join(''));
};

const decrypt = (cipher: string): string => {
  try {
    const decoded = atob(cipher);
    return decoded.split('').map((char, i) =>
      String.fromCharCode(char.charCodeAt(0) ^ SECRET_KEY.charCodeAt(i % SECRET_KEY.length)),
    ).join('');
  } catch (error) {
    logger.error('Decryption failed:', error);
    return ''; // Return empty string or handle error as appropriate
  }
};

export const localStorageWrapper = {
  setItem: (key: string, value: any): void => {
    try {
      const serializedValue = JSON.stringify(value);
      const encryptedValue = encrypt(serializedValue);
      localStorage.setItem(key, encryptedValue);
    } catch (error) {
      logger.error(`Error setting item ${key} to localStorage:`, error);
      // Handle storage limit exceeded or other errors
    }
  },

  getItem: (key: string): any | null => {
    try {
      const encryptedValue = localStorage.getItem(key);
      if (encryptedValue === null) {
        return null;
      }
      const decryptedValue = decrypt(encryptedValue);
      return JSON.parse(decryptedValue);
    } catch (error) {
      logger.error(`Error getting item ${key} from localStorage:`, error);
      return null;
    }
  },

  removeItem: (key: string): void => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      logger.error(`Error removing item ${key} from localStorage:`, error);
    }
  },

  clear: (): void => {
    try {
      localStorage.clear();
    } catch (error) {
      logger.error('Error clearing localStorage:', error);
    }
  },
};
