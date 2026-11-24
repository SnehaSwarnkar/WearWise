import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  getStoredUser,
  getMe,
  logout as apiLogout,
  login as apiLogin,
  signup as apiSignup,
  updateProfile as apiUpdateProfile,
  getToken,
  saveUser,
} from '../api/auth';
import { getSessionId } from '../api/client';

export interface StoreUser {
  id: string;
  name: string;
  email: string;
  gender?: string | null;
  bodyType?: string | null;
  kidsGender?: string | null;
  ageGroup?: string | null;
  onboardingDone?: boolean;
}

export interface StoreAuthContextType {
  user: StoreUser | null;
  setUser: React.Dispatch<React.SetStateAction<StoreUser | null>>;
  loading: boolean;
  storeToken: string | null;
  sessionId: string;
  login: (email: string, password: string) => Promise<StoreUser>;
  signup: (name: string, email: string, password: string) => Promise<StoreUser>;
  logout: () => void;
  updateProfile: (updates: Partial<StoreUser>) => Promise<StoreUser>;
  refreshUser: () => Promise<StoreUser | null>;
  mappedBodyEnginePrincipalId: string;
}

const DEFAULT_DEV_USER_ID = 'c1f7a28e-8e3b-48d9-a791-03f4439c1b3e';

export function deriveBodyEnginePrincipalId(storeUserId?: string | null): string {
  if (!storeUserId) return DEFAULT_DEV_USER_ID;
  const sanitized = storeUserId.replace(/[^a-zA-Z0-9]/g, '').padEnd(12, '0').slice(0, 12).toLowerCase();
  return `c1f7a28e-8e3b-48d9-a791-${sanitized}`;
}

const StoreAuthContext = createContext<StoreAuthContextType | undefined>(undefined);

export const StoreAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<StoreUser | null>(() => getStoredUser());
  const [loading, setLoading] = useState<boolean>(true);
  const [storeToken, setStoreToken] = useState<string | null>(() => getToken());
  const sessionId = getSessionId();

  const mappedBodyEnginePrincipalId = deriveBodyEnginePrincipalId(user?.id);

  // Sync mapped principal id to localStorage for Body Engine dev auth boundary
  useEffect(() => {
    if (user?.id) {
      localStorage.setItem('wearwise_user_id', mappedBodyEnginePrincipalId);
    }
  }, [user?.id, mappedBodyEnginePrincipalId]);

  useEffect(() => {
    getMe()
      .then((u) => {
        if (u) {
          setUser(u);
          setStoreToken(getToken());
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string): Promise<StoreUser> => {
    const loggedIn = await apiLogin(email, password);
    setUser(loggedIn);
    setStoreToken(getToken());
    return loggedIn;
  };

  const signup = async (name: string, email: string, password: string): Promise<StoreUser> => {
    const registered = await apiSignup(name, email, password);
    setUser(registered);
    setStoreToken(getToken());
    return registered;
  };

  const logout = () => {
    apiLogout();
    setUser(null);
    setStoreToken(null);
    localStorage.setItem('wearwise_user_id', DEFAULT_DEV_USER_ID);
  };

  const updateProfile = async (updates: Partial<StoreUser>): Promise<StoreUser> => {
    const updated = await apiUpdateProfile(updates);
    setUser(updated);
    saveUser(updated);
    return updated;
  };

  const refreshUser = async (): Promise<StoreUser | null> => {
    const u = await getMe();
    if (u) {
      setUser(u);
      setStoreToken(getToken());
    }
    return u;
  };

  return (
    <StoreAuthContext.Provider
      value={{
        user,
        setUser,
        loading,
        storeToken,
        sessionId,
        login,
        signup,
        logout,
        updateProfile,
        refreshUser,
        mappedBodyEnginePrincipalId,
      }}
    >
      {children}
    </StoreAuthContext.Provider>
  );
};

export const useStoreAuth = (): StoreAuthContextType => {
  const context = useContext(StoreAuthContext);
  if (!context) {
    throw new Error('useStoreAuth must be used within a StoreAuthProvider');
  }
  return context;
};
