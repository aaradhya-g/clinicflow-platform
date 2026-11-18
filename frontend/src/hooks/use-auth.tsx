"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api-client";
import { User, UserRole, AuthResponse } from "@/types";

interface AuthContextType {
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<void>;
  demoLogin: (role: UserRole) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  useEffect(() => {
    // Hydrate user from localStorage
    try {
      const storedUser = localStorage.getItem("clinicflow_user");
      const token = localStorage.getItem("clinicflow_access_token");
      if (storedUser && token) {
        setUser(JSON.parse(storedUser));
      }
    } catch {
      // Ignored
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleAuthSuccess = (data: AuthResponse) => {
    localStorage.setItem("clinicflow_access_token", data.access_token);
    localStorage.setItem("clinicflow_refresh_token", data.refresh_token);
    const userObj: User = {
      id: data.user_id,
      email: data.email,
      full_name: data.full_name,
      role: data.role,
      is_active: true,
    };
    localStorage.setItem("clinicflow_user", JSON.stringify(userObj));
    setUser(userObj);

    // Redirect based on role
    if (data.role === "doctor") {
      router.push("/doctor");
    } else if (data.role === "admin") {
      router.push("/admin");
    } else {
      router.push("/receptionist");
    }
  };

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const { data } = await apiClient.post<AuthResponse>("/auth/login", { email, password });
      handleAuthSuccess(data);
    } finally {
      setIsLoading(false);
    }
  };

  const demoLogin = async (role: UserRole) => {
    setIsLoading(true);
    try {
      const { data } = await apiClient.post<AuthResponse>(`/auth/demo-login/${role}`);
      handleAuthSuccess(data);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("clinicflow_access_token");
    localStorage.removeItem("clinicflow_refresh_token");
    localStorage.removeItem("clinicflow_user");
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || null,
        isAuthenticated: !!user,
        isLoading,
        login,
        demoLogin,
        logout,
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
