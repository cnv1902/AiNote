import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

export interface User {
  id: string;
  email: string;
  username: string | null;
  is_active: boolean;
  is_verified: boolean;
  avatar_url: string | null;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface ImageMetadata {
  file_id: string;
  camera_make: string | null;
  camera_model: string | null;
  datetime_original: string | null;
  gps_latitude: number | null;
  gps_longitude: number | null;
  width: number | null;
  height: number | null;
  orientation: number | null;
  extra: unknown;
  created_at: string;
}

export interface NoteFile {
  id: string;
  user_id: string;
  note_id: string | null;
  storage_key: string;
  url: string | null;
  filename: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  created_at: string;
  image_metadata: ImageMetadata | null;
}

export interface Note {
  id: string;
  user_id: string;
  title: string | null;
  content: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  files: NoteFile[];
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Auth API
export const authAPI = {
  register: async (email: string, username: string, password: string): Promise<User> => {
    const response = await api.post('/auth/register', { email, username, password });
    return response.data;
  },

  login: async (username: string, password: string): Promise<TokenPair> => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Notes API
export const notesAPI = {
  list: async (): Promise<Note[]> => {
    const response = await api.get('/notes/');
    return response.data;
  },

  create: async (title: string | null, content: string | null): Promise<Note> => {
    const response = await api.post('/notes/', { title, content });
    return response.data;
  },

  uploadImage: async (imageFile: File, title: string | null): Promise<Note> => {
    const formData = new FormData();
    formData.append('image', imageFile);
    if (title) {
      formData.append('title', title);
    }
    
    const response = await api.post('/notes/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  update: async (id: string, title: string | null, content: string | null): Promise<Note> => {
    const response = await api.put(`/notes/${id}`, { title, content });
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/notes/${id}`);
  },
};

export default api;
