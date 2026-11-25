import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  clearLegacyAuthStorage,
  getMe,
  logout as apiLogout,
  login as apiLogin,
  sellerLogin as apiSellerLogin,
  signup as apiSignup,
  updateProfile as apiUpdateProfile,
} from '../api/auth';
import { getSessionId } from '../api/client';

export type AccountRole = 'shopper' | 'seller' | 'admin';

export interface StoreUser {
  id: string;
  name: string;
  email: string;
  role: AccountRole;
  status?: string;
  is_active?: boolean;
  seller_approved?: boolean;
  brand_id?: string | null;
  store_name?: string | null;
  store_slug?: string | null;
  business_email?: string | null;
  store_description?: string | null;
  brand_tagline?: string | null;
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
  isShopper: boolean;
  isSeller: boolean;
  isAdmin: boolean;
  sessionId: string;
  login: (email: string, password: string) => Promise<StoreUser>;
  sellerLogin: (email: string, password: string) => Promise<StoreUser>;
  signup: (name: string, email: string, password: string) => Promise<StoreUser>;
  logout: () => Promise<void>;
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
  const [user, setUser] = useState<StoreUser | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const sessionId = getSessionId();

  const mappedBodyEnginePrincipalId = deriveBodyEnginePrincipalId(user?.id);
  const isShopper = Boolean(user && user.role === 'shopper' && user.status !== 'suspended');
  const isSeller = Boolean(
    user && user.role === 'seller' && user.seller_approved && user.status === 'active'
  );
  const isAdmin = Boolean(user && user.role === 'admin' && user.status === 'active');

  useEffect(() => {
    clearLegacyAuthStorage();
    getMe()
      .then((u) => {
        setUser(u || null);
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email: string, password: string): Promise<StoreUser> => {
    const loggedIn = await apiLogin(email, password);
    setUser(loggedIn);
    return loggedIn;
  };

  const sellerLogin = async (email: string, password: string): Promise<StoreUser> => {
    const loggedIn = await apiSellerLogin(email, password);
    setUser(loggedIn);
    return loggedIn;
  };

  const signup = async (name: string, email: string, password: string): Promise<StoreUser> => {
    const registered = await apiSignup(name, email, password);
    setUser(registered);
    return registered;
  };

  const logout = async (): Promise<void> => {
    await apiLogout();
    setUser(null);
  };

  const updateProfile = async (updates: Partial<StoreUser>): Promise<StoreUser> => {
    const updated = await apiUpdateProfile(updates);
    setUser(updated);
    return updated;
  };

  const refreshUser = async (): Promise<StoreUser | null> => {
    const u = await getMe();
    setUser(u || null);
    return u;
  };

  return (
    <StoreAuthContext.Provider
      value={{
        user,
        setUser,
        loading,
        isShopper,
        isSeller,
        isAdmin,
        sessionId,
        login,
        sellerLogin,
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
