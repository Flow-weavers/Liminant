const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "agent";
  content: string;
  timestamp: string;
  metadata: {
    tokens_used?: number;
    model?: string;
    attachments?: string[];
  };
}

interface Session {
  id: string;
  created_at: string;
  updated_at: string;
  state: {
    phase: string;
    current_step: number;
    total_steps: number;
  };
  context: {
    working_directory: string;
    language: string;
    preferences: Record<string, unknown>;
  };
  messages: Message[];
  artifacts: unknown[];
  constraints: {
    active: boolean;
    rules: string[];
    knowledge_refs: string[];
  };
}

async function fetchJSON(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  sessions: {
    create: (data?: { working_directory?: string; language?: string }) =>
      fetchJSON("/api/v1/sessions", {
        method: "POST",
        body: JSON.stringify(data ?? {}),
      }),

    list: () => fetchJSON("/api/v1/sessions"),

    get: (id: string) => fetchJSON(`/api/v1/sessions/${id}`),

    delete: (id: string) =>
      fetchJSON(`/api/v1/sessions/${id}`, { method: "DELETE" }),

    getMessages: (id: string) =>
      fetchJSON(`/api/v1/sessions/${id}/messages`),

    sendMessage: (
      id: string,
      content: string,
      role: string = "user"
    ): Promise<{ message: Message; response_content: string; session: Session }> =>
      fetchJSON(`/api/v1/sessions/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({ content, role }),
      }),
  },

  knowledge: {
    list: () => fetchJSON("/api/v1/knowledge"),
    search: (query: string, limit = 10) =>
      fetchJSON(`/api/v1/knowledge/search?query=${encodeURIComponent(query)}&limit=${limit}`),
    create: (data: unknown) =>
      fetchJSON("/api/v1/knowledge", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    get: (id: string) => fetchJSON(`/api/v1/knowledge/${id}`),
    delete: (id: string) =>
      fetchJSON(`/api/v1/knowledge/${id}`, { method: "DELETE" }),
  },

  tools: {
    list: () => fetchJSON("/api/v1/tools"),
    execute: (name: string, params: Record<string, unknown>) =>
      fetchJSON(`/api/v1/tools/${name}/execute`, {
        method: "POST",
        body: JSON.stringify({ params }),
      }),
  },
};

export type { Session, Message };
