import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { BodyProfile, PrincipalType } from '../types/api';
import { apiClient, devAuthHeaderProvider } from '../api/client';

export interface BodyEngineAuthContextType {
  role: PrincipalType;
  currentPrincipalId: string;
  token: string | null;
  isDev: boolean;
  activeProfile: BodyProfile | null;
  allProfiles: BodyProfile[];
  backendStatus: 'online' | 'offline' | 'checking';
  switchRole: (role: PrincipalType, customId?: string) => void;
  setCustomToken: (token: string | null) => void;
  setActiveProfile: (profile: BodyProfile | null) => void;
  refreshProfiles: () => Promise<void>;
  checkBackendHealth: () => Promise<boolean>;
}

const DEFAULT_DEV_USER_ID = 'c1f7a28e-8e3b-48d9-a791-03f4439c1b3e';
const DEFAULT_DEV_BRAND_ID = 'e4d9b2a1-5f3c-4b8a-9e1d-8f7a6b5c4d3e';

const BodyEngineAuthContext = createContext<BodyEngineAuthContextType | undefined>(undefined);

export const BodyEngineAuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [role, setRole] = useState<PrincipalType>(() => {
    return (localStorage.getItem('wearwise_role') as PrincipalType) || 'user';
  });
  const [userId, setUserId] = useState<string>(() => {
    return localStorage.getItem('wearwise_user_id') || DEFAULT_DEV_USER_ID;
  });
  const [brandId, setBrandId] = useState<string>(() => {
    return localStorage.getItem('wearwise_brand_id') || DEFAULT_DEV_BRAND_ID;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('wearwise_jwt') || null;
  });

  const [activeProfile, setActiveProfileState] = useState<BodyProfile | null>(null);
  const [allProfiles, setAllProfiles] = useState<BodyProfile[]>([]);
  const [backendStatus, setBackendStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  // Listen to potential wearwise_user_id changes in localStorage
  useEffect(() => {
    const handleStorage = () => {
      const storedUserId = localStorage.getItem('wearwise_user_id');
      if (storedUserId && storedUserId !== userId) {
        setUserId(storedUserId);
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [userId]);

  // Synchronize devAuthHeaderProvider with state
  useEffect(() => {
    devAuthHeaderProvider.setToken(token);
    devAuthHeaderProvider.setDevRole(role, role === 'user' ? userId : brandId);
  }, [role, userId, brandId, token]);

  const checkBackendHealth = async (): Promise<boolean> => {
    try {
      const res = await apiClient.checkHealth();
      if (res && (res.status === 'healthy' || res.status === 'ok')) {
        setBackendStatus('online');
        return true;
      }
      setBackendStatus('offline');
      return false;
    } catch {
      setBackendStatus('offline');
      return false;
    }
  };

  const refreshProfiles = async () => {
    if (role !== 'user') return;
    try {
      const profiles = await apiClient.listProfiles();
      setAllProfiles(profiles);
      if (profiles.length > 0) {
        const savedId = localStorage.getItem('wearwise_active_profile_id');
        const matched = profiles.find((p) => p.profile_id === savedId) || profiles[0];
        setActiveProfileState(matched);
        localStorage.setItem('wearwise_active_profile_id', matched.profile_id);
      } else {
        setActiveProfileState(null);
        localStorage.removeItem('wearwise_active_profile_id');
      }
    } catch (err) {
      console.warn('Failed to load user profiles:', err);
    }
  };

  // Initial load
  useEffect(() => {
    checkBackendHealth();
    if (role === 'user') {
      refreshProfiles();
    }
  }, [role, userId, token]);

  const switchRole = (newRole: PrincipalType, customId?: string) => {
    setRole(newRole);
    localStorage.setItem('wearwise_role', newRole);
    if (customId) {
      if (newRole === 'user') {
        setUserId(customId);
        localStorage.setItem('wearwise_user_id', customId);
      } else {
        setBrandId(customId);
        localStorage.setItem('wearwise_brand_id', customId);
      }
    }
  };

  const setCustomToken = (newToken: string | null) => {
    setToken(newToken);
    if (newToken) {
      localStorage.setItem('wearwise_jwt', newToken);
    } else {
      localStorage.removeItem('wearwise_jwt');
    }
  };

  const setActiveProfile = (profile: BodyProfile | null) => {
    setActiveProfileState(profile);
    if (profile) {
      localStorage.setItem('wearwise_active_profile_id', profile.profile_id);
    } else {
      localStorage.removeItem('wearwise_active_profile_id');
    }
  };

  const currentPrincipalId = role === 'user' ? userId : brandId;

  return (
    <BodyEngineAuthContext.Provider
      value={{
        role,
        currentPrincipalId,
        token,
        isDev: true,
        activeProfile,
        allProfiles,
        backendStatus,
        switchRole,
        setCustomToken,
        setActiveProfile,
        refreshProfiles,
        checkBackendHealth,
      }}
    >
      {children}
    </BodyEngineAuthContext.Provider>
  );
};

export const useBodyEngineAuth = (): BodyEngineAuthContextType => {
  const context = useContext(BodyEngineAuthContext);
  if (!context) {
    throw new Error('useBodyEngineAuth must be used within a BodyEngineAuthProvider');
  }
  return context;
};
