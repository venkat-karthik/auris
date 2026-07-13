import axios, { InternalAxiosRequestConfig, AxiosResponse } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor: attach JWT and Organization header
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auris_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      const orgId = localStorage.getItem('auris_org_id');
      if (orgId) {
        config.headers['X-Organization-ID'] = orgId;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: handle 401 token expiration
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auris_token');
        localStorage.removeItem('auris_org_id');
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Types & Interfaces ──────────────────────────────────────────────────────────

export interface UserProfile {
  id: number | string;
  email: string;
  full_name: string;
  is_verified?: boolean;
  selected_org_id?: number;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  balance_credits: number;
  api_key?: string;
  created_at?: string;
}

export interface Agent {
  id: number;
  name: string;
  model: string;
  tier: 'economy' | 'standard' | 'premium';
  system_prompt?: string;
  voice_id?: string;
  language?: string;
  is_active: boolean;
  temperature?: number;
  max_duration_seconds?: number;
  workflow_graph?: any;
  created_at?: string;
}

export interface CallRun {
  id: number;
  agent_id: number;
  customer_number: string;
  agent_number: string;
  direction: 'inbound' | 'outbound' | 'web';
  status: 'queued' | 'in-progress' | 'completed' | 'failed' | 'voicemail';
  duration_seconds?: number;
  summary?: string;
  sentiment?: string;
  key_topics?: string[];
  task_completed?: boolean;
  recording_url?: string;
  transcript?: any;
  transcript_path?: string;
  created_at: string;
}

export interface PhoneNumber {
  id: number;
  phone_number: string;
  label?: string;
  is_active: boolean;
  agent_id?: number;
  agent_name?: string;
  created_at: string;
}

export interface AvailableInventoryItem {
  id: number;
  phone_number: string;
  region?: string;
  is_leased: boolean;
  monthly_cost_usd: number;
}

export interface Campaign {
  id: number;
  name: string;
  agent_id: number;
  status: 'draft' | 'running' | 'paused' | 'completed';
  total_contacts: number;
  completed_calls: number;
  successful_calls: number;
  created_at: string;
}

// ── API Methods Mapped 1:1 to 18 Backend Routers ────────────────────────────────

export const AurisAPI = {
  // 1. Auth Router
  auth: {
    login: async (email: string, password: string) => {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);
      const res = await apiClient.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      });
      return res.data;
    },
    register: async (email: string, password: string, fullName: string, orgName: string) => {
      const res = await apiClient.post('/auth/register', {
        email,
        password,
        full_name: fullName,
        org_name: orgName
      });
      return res.data;
    },
    me: async () => {
      const res = await apiClient.get('/auth/me');
      return res.data;
    },
    verify: async (email: string, code: string) => {
      const res = await apiClient.post('/auth/verify', { email, code });
      return res.data;
    }
  },

  // 2. Organizations Router
  orgs: {
    list: async () => {
      const res = await apiClient.get('/organizations');
      return res.data;
    },
    create: async (name: string, slug?: string) => {
      const res = await apiClient.post('/organizations', { name, slug });
      return res.data;
    },
    select: async (orgId: number) => {
      const res = await apiClient.post(`/organizations/${orgId}/select`);
      return res.data;
    },
    getMembers: async (orgId: number) => {
      const res = await apiClient.get(`/organizations/${orgId}/members`);
      return res.data;
    },
    invite: async (email: string, role: string = 'member') => {
      const res = await apiClient.post('/organizations/invite', { email, role });
      return res.data;
    }
  },

  // 3. Voice Agents Router
  agents: {
    list: async () => {
      const res = await apiClient.get('/agents');
      return res.data;
    },
    get: async (id: number) => {
      const res = await apiClient.get(`/agents/${id}`);
      return res.data;
    },
    create: async (data: Partial<Agent>) => {
      const res = await apiClient.post('/agents', data);
      return res.data;
    },
    update: async (id: number, data: Partial<Agent>) => {
      const res = await apiClient.put(`/agents/${id}`, data);
      return res.data;
    },
    delete: async (id: number) => {
      const res = await apiClient.delete(`/agents/${id}`);
      return res.data;
    },
    getStudioGraph: async (id: number) => {
      const res = await apiClient.get(`/agents/${id}/studio`);
      return res.data;
    },
    saveStudioGraph: async (id: number, graphData: any) => {
      const res = await apiClient.post(`/agents/${id}/studio`, graphData);
      return res.data;
    }
  },

  // 4. Calls & WebRTC Router
  calls: {
    list: async (agentId?: number, limit: number = 50) => {
      const params = agentId ? { agent_id: agentId, limit } : { limit };
      const res = await apiClient.get('/calls', { params });
      return res.data;
    },
    get: async (id: number) => {
      const res = await apiClient.get(`/calls/${id}`);
      return res.data;
    },
    dispatch: async (agentId: number, customerNumber: string, customData?: any) => {
      const res = await apiClient.post('/calls/dispatch', {
        agent_id: agentId,
        customer_number: customerNumber,
        custom_data: customData
      });
      return res.data;
    },
    webCall: async (agentId: number, callerNumber: string = 'Browser WebRTC', metadata?: any) => {
      const res = await apiClient.post('/calls/web-call', {
        agent_id: agentId,
        caller_number: callerNumber,
        metadata: metadata || {}
      });
      return res.data;
    },
    end: async (id: number) => {
      const res = await apiClient.post(`/calls/${id}/end`);
      return res.data;
    }
  },

  // 5. Phone Numbers & V2 Local Inventory Router
  phoneNumbers: {
    list: async () => {
      const res = await apiClient.get('/phone-numbers');
      return res.data;
    },
    search: async (areaCode?: string) => {
      const params = areaCode ? { area_code: areaCode } : {};
      const res = await apiClient.get('/phone-numbers/search', { params });
      return res.data;
    },
    buy: async (phoneNumber: string, label?: string) => {
      const res = await apiClient.post('/phone-numbers/buy', {
        phone_number: phoneNumber,
        label: label || 'Main Reception Line'
      });
      return res.data;
    },
    bind: async (numberId: number, agentId: number | null) => {
      const res = await apiClient.put(`/phone-numbers/${numberId}/bind`, { agent_id: agentId });
      return res.data;
    },
    release: async (numberId: number) => {
      const res = await apiClient.delete(`/phone-numbers/${numberId}`);
      return res.data;
    },
    listInventory: async () => {
      const res = await apiClient.get('/phone-numbers/inventory');
      return res.data;
    },
    seedInventory: async (phoneNumbers: string[], region?: string, cost?: number) => {
      const res = await apiClient.post('/phone-numbers/inventory', {
        phone_numbers: phoneNumbers,
        region: region || 'United States',
        monthly_cost_usd: cost || 2.0
      });
      return res.data;
    }
  },

  // 6. Billing & Credits Router
  billing: {
    createOrder: async (amountInr: number) => {
      const res = await apiClient.post('/billing/create-order', { amount_inr: amountInr });
      return res.data;
    },
    verifyPayment: async (paymentData: any) => {
      const res = await apiClient.post('/billing/verify-payment', paymentData);
      return res.data;
    },
    listTransactions: async () => {
      const res = await apiClient.get('/billing/transactions');
      return res.data;
    }
  },

  // 7. Knowledge Base & RAG Router
  knowledge: {
    list: async () => {
      const res = await apiClient.get('/knowledge');
      return res.data;
    },
    uploadFile: async (file: File, agentId?: number) => {
      const formData = new FormData();
      formData.append('file', file);
      if (agentId) formData.append('agent_id', String(agentId));
      const res = await apiClient.post('/knowledge/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return res.data;
    },
    scrapeUrl: async (url: string, agentId?: number) => {
      const res = await apiClient.post('/knowledge/scrape', { url, agent_id: agentId });
      return res.data;
    },
    delete: async (id: number) => {
      const res = await apiClient.delete(`/knowledge/${id}`);
      return res.data;
    }
  },

  // 8. Outbound Dialing Campaigns Router
  campaigns: {
    list: async () => {
      const res = await apiClient.get('/campaigns');
      return res.data;
    },
    create: async (name: string, agentId: number, contacts: any[]) => {
      const res = await apiClient.post('/campaigns', { name, agent_id: agentId, contacts });
      return res.data;
    },
    start: async (id: number) => {
      const res = await apiClient.post(`/campaigns/${id}/start`);
      return res.data;
    },
    pause: async (id: number) => {
      const res = await apiClient.post(`/campaigns/${id}/pause`);
      return res.data;
    }
  },

  // 9. WhatsApp Router
  whatsapp: {
    listTemplates: async () => {
      const res = await apiClient.get('/whatsapp/templates');
      return res.data;
    },
    sendFollowup: async (callRunId: number, templateName: string) => {
      const res = await apiClient.post('/whatsapp/send', { call_run_id: callRunId, template_name: templateName });
      return res.data;
    }
  },

  // 10. Cloned Voices Router
  clonedVoices: {
    list: async () => {
      const res = await apiClient.get('/cloned-voices');
      return res.data;
    },
    create: async (name: string, sampleAudio: File) => {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('sample', sampleAudio);
      const res = await apiClient.post('/cloned-voices', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return res.data;
    }
  },

  // 11. Customer Profiles & Memory Router
  customers: {
    list: async () => {
      const res = await apiClient.get('/customers');
      return res.data;
    },
    get: async (id: number) => {
      const res = await apiClient.get(`/customers/${id}`);
      return res.data;
    }
  },

  // 12. MCP Tool Dispatch Router
  mcp: {
    listTools: async () => {
      const res = await apiClient.get('/mcp/tools');
      return res.data;
    },
    invokeTool: async (toolName: string, args: any) => {
      const res = await apiClient.post('/mcp/invoke', { tool_name: toolName, arguments: args });
      return res.data;
    }
  }
};
