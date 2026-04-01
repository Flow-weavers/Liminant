import { create } from "zustand";
import { api, API_BASE, Session, Message } from "./api";

interface ReasoningEntry {
  phase: string;
  intent: string;
  kb_entries: { id: string; title: string; type: string }[];
  applied_constraints: { id: string; title: string; type: string }[];
  tools_used: { name: string; args: Record<string, unknown>; result: unknown }[];
  pipeline_stage: number;
  pipeline_complete: boolean;
}

interface PreflightState {
  visible: boolean;
  user_input: string;
  pending_content: string;
  intent: string;
  intent_label: string;
  requirements: string[];
  kb_entries: { id: string; title: string; type: string; content_preview: string; relevance_score: number }[];
  anchors: { id: string; path: string; type: string; label: string }[];
  confidence: number;
  dismissed: boolean;
  loading: boolean;
}

interface ApiState {
  _es: EventSource | undefined;
}

interface AppState extends ApiState {
  sessions: Session[];
  activeSessionId: string | null;
  activeSession: Session | null;
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  reasoningLog: ReasoningEntry[];
  preflight: PreflightState;
  connectStream: (sessionId: string) => void;
  disconnectStream: () => void;

  createSession: (data?: { working_directory?: string; language?: string }) => Promise<string>;
  loadSessions: () => Promise<void>;
  loadSession: (id: string) => Promise<void>;
  deleteSession: (id: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
  setActiveSession: (id: string | null) => void;
  clearError: () => void;
  clearReasoningLog: () => void;
  runPreflight: (user_input: string) => Promise<void>;
  confirmPreflight: () => Promise<void>;
  dismissPreflight: () => void;
  updateConstraints: (data: {
    active?: boolean;
    add_rules?: string[];
    remove_rules?: string[];
    add_knowledge_refs?: string[];
    remove_knowledge_refs?: string[];
  }) => Promise<void>;
  loadArtifacts: (sessionId: string) => Promise<unknown[]>;
}

export const useStore = create<AppState>((set, get) => ({
  _es: undefined,
  sessions: [],
  activeSessionId: null,
  activeSession: null,
  messages: [],
  isLoading: false,
  error: null,
  reasoningLog: [],
  preflight: {
    visible: false,
    user_input: "",
    pending_content: "",
    intent: "general",
    intent_label: "General",
    requirements: [],
    kb_entries: [],
    anchors: [],
    confidence: 0.5,
    dismissed: false,
    loading: false,
  },

  connectStream: (sessionId: string) => {
    const { disconnectStream } = get();
    disconnectStream();

    const url = `${API_BASE}/api/v1/sessions/${sessionId}/stream`;
    const es = new EventSource(url);

    es.addEventListener("pipeline", (e) => {
      try {
        const data = JSON.parse(e.data);
        const entry: ReasoningEntry = {
          phase: data.phase,
          intent: data.data?.intent || "",
          kb_entries: (data.data?.kb_entries || []) as ReasoningEntry["kb_entries"],
          applied_constraints: (data.data?.applied_constraints || []) as ReasoningEntry["applied_constraints"],
          tools_used: (data.data?.tools_used || []) as ReasoningEntry["tools_used"],
          pipeline_stage: data.stage || 0,
          pipeline_complete: data.phase === "done",
        };

        set((state) => ({
          reasoningLog: [...state.reasoningLog, entry],
        }));
      } catch {}
    });

    es.addEventListener("tool_executed", (e) => {
      try {
        const data = JSON.parse(e.data);
        const toolEntry: ReasoningEntry = {
          phase: "tool_executed",
          intent: "",
          kb_entries: [],
          applied_constraints: [],
          tools_used: [{
            name: data.data?.tool_name || "unknown",
            args: (data.data?.args || {}) as Record<string, unknown>,
            result: data.data?.result,
          }],
          pipeline_stage: data.stage || 3,
          pipeline_complete: false,
        };
        set((state) => ({
          reasoningLog: [...state.reasoningLog, toolEntry],
        }));
      } catch {}
    });

    set({ _es: es });
  },

  disconnectStream: () => {
    const { _es } = get() as { _es?: EventSource };
    if (_es) {
      _es.close();
      set({ _es: undefined });
    }
  },

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
      const reasoning = res.reasoning as ReasoningEntry | undefined;
      if (reasoning) {
        set((state) => ({
          reasoningLog: [...state.reasoningLog, reasoning],
        }));
      }
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
  clearReasoningLog: () => set({ reasoningLog: [] }),

  runPreflight: async (user_input: string) => {
    const { activeSessionId } = get();
    if (!activeSessionId) return;
    set((state) => ({
      preflight: {
        ...state.preflight,
        visible: true,
        loading: true,
        user_input,
        pending_content: user_input,
        dismissed: false,
      },
    }));
    try {
      const result = await api.preflight.analyze(user_input, activeSessionId);
      set((state) => ({
        preflight: {
          ...state.preflight,
          loading: false,
          intent: result.intent,
          intent_label: result.intent_label,
          requirements: result.requirements,
          kb_entries: result.kb_entries,
          anchors: result.anchors,
          confidence: result.confidence,
        },
      }));
    } catch {
      set((state) => ({
        preflight: {
          ...state.preflight,
          loading: false,
          intent: "general",
          intent_label: "General",
        },
      }));
    }
  },

  confirmPreflight: async () => {
    const { preflight, sendMessage } = get();
    set((state) => ({
      preflight: { ...state.preflight, visible: false, dismissed: true },
    }));
    await sendMessage(preflight.pending_content);
  },

  dismissPreflight: () => {
    set((state) => ({
      preflight: { ...state.preflight, visible: false, dismissed: true },
    }));
  },

  updateConstraints: async (data) => {
    const { activeSessionId } = get();
    if (!activeSessionId) return;
    try {
      const updated = await api.sessions.updateConstraints(activeSessionId, data);
      set((state) => ({
        activeSession: state.activeSession
          ? { ...state.activeSession, constraints: updated.constraints }
          : null,
      }));
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  loadArtifacts: async (sessionId: string) => {
    const res = await api.sessions.getArtifacts(sessionId);
    return res.artifacts;
  },
}));
