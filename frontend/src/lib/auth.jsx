import { createContext, useContext, useEffect, useState } from "react";
import {
  api,
  clearSession,
  getStoredUser,
  getToken,
  setSession,
} from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());

  useEffect(() => {
    if (getToken() && !user) setUser(getStoredUser());
  }, [user]);

  async function login(email, password) {
    const data = await api.login(email, password);
    setSession(data.accessToken, data.user);
    setUser(data.user);
    return data.user;
  }

  async function logout() {
    try {
      await api.logout();
    } catch {
      /* ignore */
    }
    clearSession();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
