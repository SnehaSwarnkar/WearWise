import { createContext, useContext, useState, useEffect } from "react";
import { getStoredUser, getMe, logout as apiLogout } from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(getStoredUser());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Revalidate token on mount
    getMe()
      .then((u) => { if (u) setUser(u); })
      .finally(() => setLoading(false));
  }, []);

  const refreshUser = async () => {
    const u = await getMe();
    if (u) setUser(u);
    return u;
  };

  const logout = () => {
    apiLogout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, refreshUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
