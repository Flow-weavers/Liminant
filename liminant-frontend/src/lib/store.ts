import { create } from "zustand";
import { api, Session, Message } from "./api";

interface AppState {
  sessions: Session[];
  activeSessionId: string | null;
  activeSession: Session | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;

  createSession: (data?: { working_directory?: string; language?: string }) => Promise<string>;
  loadSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setActiveSession: (id: string | null) => void;
  clearError: () => void;
}

export const useStore = create<AppState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  activeSession: null,
  messages: [],
  isLoading: false,
  error: null,

  createSession: async (data) => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.sessions.create(data);
      const session: Session = res.session;
      set((state) => ({
        sessions: [session, ...state.sessions],
        activeSessionId: session.id,
        activeSession: session,
        messages: [],
        isLoading: false,
      }));
      return session.id;
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
      throw e;
    }
  },

  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await api.sessions.list();
      set({ sessions: res.sessions, isLoading: false });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  loadSession: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const session = await api.sessions.get(id);
      const msgRes = await api.sessions.getMessages(id);
      set({
        activeSessionId: id,
        activeSession: session,
        messages: msgRes.messages,
        isLoading: false,
      });
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  deleteSession: async (id: string) => {
    try {
      await api.sessions.delete(id);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== id),
        activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
        activeSession: state.activeSessionId === id ? null : state.activeSession,
      }));
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  sendMessage: async (content: string) => {
    const { activeSessionId } = get();
    if (!activeSessionId) return;

    const userMsg: Message = {
      id: `msg_${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date().toISOString(),
      metadata: {},
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isLoading: true,
      error: null,
    }));

    try {
      const res = await api.sessions.sendMessage(activeSessionId, content);
      set((state) => ({
        messages: [...state.messages, res.message],
        activeSession: res.session,
        isLoading: false,
      }));
    } catch (e) {
      set({ error: (e as Error).message, isLoading: false });
    }
  },

  setActiveSession: (id: string | null) => {
    if (id) {
      get().loadSession(id);
    } else {
      set({ activeSessionId: null, activeSession: null, messages: [] });
    }
  },

  clearError: () => set({ error: null }),
}));
