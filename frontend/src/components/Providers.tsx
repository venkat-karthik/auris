"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
import { Toaster } from "sonner";
import { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";

// Define TypeScript interfaces for Auth
interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_superuser: boolean;
  selected_org_id: number | null;
}

interface AuthContextType {
  user: User | null;
  orgId: number | null;
  token: string | null;
  loading: boolean;
  login: (token: string, userId: number, orgId: number | null) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

import { getApiUrl } from "@/lib/api";

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const API_URL = getApiUrl();

  const refreshUser = React.useCallback(async (authToken?: string) => {
    const activeToken = authToken || token || localStorage.getItem("auris_token");
    if (!activeToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${activeToken}`,
        },
      });

      if (res.ok) {
        const userData = await res.json();
        setUser(userData);
        setToken(activeToken);
        localStorage.setItem("auris_token", activeToken);
      } else {
        // Token expired or invalid
        logout();
      }
    } catch (err) {
      console.error("Auth verify error:", err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  // Protect client-side routing
  useEffect(() => {
    if (loading) return;
    const publicPages = ["/auth/login", "/auth/signup"];
    const isPublicPage = publicPages.some(page => pathname.startsWith(page));

    if (!user && !isPublicPage) {
      router.push("/auth/login");
    } else if (user && isPublicPage) {
      router.push("/dashboard");
    }
  }, [user, pathname, loading, router]);

  const login = (newToken: string, userId: number, newOrgId: number | null) => {
    setToken(newToken);
    localStorage.setItem("auris_token", newToken);
    refreshUser(newToken);
    router.push("/dashboard");
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem("auris_token");
    router.push("/auth/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        orgId: user?.selected_org_id || null,
        token,
        loading,
        login,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider attribute="class" defaultTheme="system" enableSystem>
      <AuthProvider>
        {children}
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </NextThemesProvider>
  );
}
