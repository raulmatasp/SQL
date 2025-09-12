import axios from 'axios';

const API_BASE_URL = 'http://localhost:8002/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Add auth token interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('hugdata_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('hugdata_token');
      localStorage.removeItem('hugdata_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Types
export interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  user_id: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
  data_sources?: DataSource[];
  queries?: Query[];
}

export interface DataSource {
  id: string;
  project_id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'bigquery' | 'snowflake' | 'sqlite';
  connection_config: Record<string, any>;
  status: 'active' | 'inactive';
  last_connected_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Query {
  id: string;
  project_id: string;
  user_id: string;
  natural_language: string;
  generated_sql: string;
  results: any[];
  status: 'success' | 'error';
  execution_time_ms: number;
  created_at: string;
  updated_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  password_confirmation: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

// API Services
export const authService = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },

  register: async (userData: RegisterData): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout');
    localStorage.removeItem('hugdata_token');
    localStorage.removeItem('hugdata_user');
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await api.get('/auth/user');
    return response.data;
  },
};

export const projectService = {
  getAll: async (): Promise<Project[]> => {
    const response = await api.get('/projects');
    return response.data.data;
  },

  getById: async (id: string): Promise<Project> => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  create: async (projectData: Omit<Project, 'id' | 'user_id' | 'created_at' | 'updated_at'>): Promise<Project> => {
    const response = await api.post('/projects', projectData);
    return response.data;
  },

  update: async (id: string, projectData: Partial<Project>): Promise<Project> => {
    const response = await api.put(`/projects/${id}`, projectData);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },
};

export const dataSourceService = {
  getAll: async (projectId: string): Promise<DataSource[]> => {
    const response = await api.get(`/projects/${projectId}/data-sources`);
    return response.data.data;
  },

  getById: async (id: string): Promise<DataSource> => {
    const response = await api.get(`/data-sources/${id}`);
    return response.data;
  },

  create: async (projectId: string, dataSourceData: Omit<DataSource, 'id' | 'project_id' | 'status' | 'created_at' | 'updated_at'>): Promise<DataSource> => {
    const response = await api.post(`/projects/${projectId}/data-sources`, dataSourceData);
    return response.data;
  },

  update: async (id: string, dataSourceData: Partial<DataSource>): Promise<DataSource> => {
    const response = await api.put(`/data-sources/${id}`, dataSourceData);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/data-sources/${id}`);
  },

  testConnection: async (id: string): Promise<{ success: boolean; message: string; connected_at?: string }> => {
    const response = await api.post(`/data-sources/${id}/test`);
    return response.data;
  },

  getSchema: async (id: string): Promise<any> => {
    const response = await api.get(`/data-sources/${id}/schema`);
    return response.data;
  },
};

export interface NaturalLanguageQueryRequest {
  query: string;
  project_id: string;
  data_source_id: string;
}

export interface NaturalLanguageQueryResponse {
  query_id: string;
  sql: string;
  explanation: string;
  results: any[];
  execution_time_ms: number;
  confidence: number;
}

export const queryService = {
  processNaturalLanguage: async (queryData: NaturalLanguageQueryRequest): Promise<NaturalLanguageQueryResponse> => {
    const response = await api.post('/queries/natural-language', queryData);
    return response.data;
  },

  executeSql: async (sql: string, dataSourceId: string): Promise<any> => {
    const response = await api.post('/queries/sql', {
      sql,
      data_source_id: dataSourceId,
    });
    return response.data;
  },

  getHistory: async (): Promise<Query[]> => {
    const response = await api.get('/queries/history');
    return response.data.data;
  },

  getById: async (id: string): Promise<Query> => {
    const response = await api.get(`/queries/${id}`);
    return response.data;
  },
};

export const aiService = {
  generateSql: async (query: string, schema: any, context: any = {}): Promise<any> => {
    const response = await api.post('/ai/generate-sql', {
      query,
      schema,
      context,
    });
    return response.data;
  },

  explainQuery: async (sql: string, schema: any): Promise<any> => {
    const response = await api.post('/ai/explain-query', {
      sql,
      schema,
    });
    return response.data;
  },

  suggestCharts: async (dataSample: any[], queryIntent: string): Promise<any> => {
    const response = await api.post('/ai/suggest-charts', {
      data_sample: dataSample,
      query_intent: queryIntent,
    });
    return response.data;
  },
};