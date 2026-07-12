'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AurisAPI, UserProfile, Organization } from '@/lib/api';

interface AuthContextType {
  user: UserProfile | null;
  organizations: Organization[];
  activeOrg: Organization | null;
  isLoading: boolean;
  login: (token: string, orgId?: number) => Promise<void>;
  logout: () => void;
  selectOrganization: (org: Organization) => void;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// No default mock user or organization to ensure database connection exclusively.

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [activeOrg, setActiveOrg] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshProfile = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('auris_token') : null;
      if (!token) {
        setUser(null);
        setOrganizations([]);
        setActiveOrg(null);
        setIsLoading(false);
        return;
      }

      const userData = await AurisAPI.auth.me();
      setUser(userData);

      const orgsData = await AurisAPI.orgs.list();
      setOrganizations(orgsData);

      const savedOrgId = typeof window !== 'undefined' ? localStorage.getItem('auris_org_id') : null;
      const currentOrg = orgsData.find((o: Organization) => String(o.id) === savedOrgId) || orgsData[0] || null;
      setActiveOrg(currentOrg);
      if (typeof window !== 'undefined' && currentOrg) {
        localStorage.setItem('auris_org_id', String(currentOrg.id));
      }
    } catch (err) {
      console.warn('Backend connection unavailable or token expired:', err);
      setUser(null);
      setOrganizations([]);
      setActiveOrg(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshProfile();
  }, []);

  const login = async (token: string, orgId?: number) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('auris_token', token);
      if (orgId) {
        localStorage.setItem('auris_org_id', String(orgId));
      }
    }
    await refreshProfile();
  };

  const logout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auris_token');
      localStorage.removeItem('auris_org_id');
      window.location.href = '/login';
    }
    setUser(null);
    setOrganizations([]);
    setActiveOrg(null);
  };

  const selectOrganization = (org: Organization) => {
    setActiveOrg(org);
    if (typeof window !== 'undefined') {
      localStorage.setItem('auris_org_id', String(org.id));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organizations,
        activeOrg,
        isLoading,
        login,
        logout,
        selectOrganization,
        refreshProfile
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
