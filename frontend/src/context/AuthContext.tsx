import React, { ReactNode } from 'react';
import { StoreAuthProvider, useStoreAuth, StoreAuthContextType, StoreUser } from './StoreAuthContext';
import { BodyEngineAuthProvider, useBodyEngineAuth, BodyEngineAuthContextType } from './BodyEngineAuthContext';

export * from './StoreAuthContext';
export * from './BodyEngineAuthContext';

export type UnifiedAuthContextType = StoreAuthContextType & BodyEngineAuthContextType;

/**
 * Combined AuthProvider that mounts both StoreAuthProvider (commerce session and credentials)
 * and BodyEngineAuthProvider (UUID principals, dev headers, and body profiles).
 */
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <StoreAuthProvider>
      <BodyEngineAuthProvider>
        {children}
      </BodyEngineAuthProvider>
    </StoreAuthProvider>
  );
};

/**
 * Universal hook providing both storefront commerce authentication (user, login, signup, logout)
 * and Body Engine principal management (role, activeProfile, switchRole, backendStatus).
 */
export const useAuth = (): UnifiedAuthContextType => {
  const storeAuth = useStoreAuth();
  const bodyEngineAuth = useBodyEngineAuth();

  return {
    ...storeAuth,
    ...bodyEngineAuth,
    // Keep 'loading' alias to store loading state for PrivateRoute guards
    loading: storeAuth.loading,
  };
};
