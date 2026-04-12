import { create } from "zustand";
import api from "@/services/api";
import type { User } from "@/types/api";

interface UserUpdateData {
  first_name?: string;
  last_name?: string;
  phone?: string;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string, recaptchaToken?: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    role: string;
    first_name: string;
    last_name: string;
    company_name?: string;
  }, recaptchaToken?: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateUser: (data: UserUpdateData) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email, password, recaptchaToken?) => {
    const headers: Record<string, string> = {};
    if (recaptchaToken) headers["X-Recaptcha-Token"] = recaptchaToken;

    const { data } = await api.post("/auth/login", { email, password }, { headers });
    localStorage.setItem("access_token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);

    const userRes = await api.get("/auth/me");
    set({ user: userRes.data, isAuthenticated: true, isLoading: false });
  },

  register: async (formData, recaptchaToken?) => {
    const headers: Record<string, string> = {};
    if (recaptchaToken) headers["X-Recaptcha-Token"] = recaptchaToken;

    await api.post("/auth/register", formData, { headers });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false, isLoading: false });
  },

  fetchUser: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      const { data } = await api.get("/auth/me");
      set({ user: data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  updateUser: async (userData) => {
    const { data } = await api.patch("/auth/me", userData);
    set({ user: data });
  },
}));
