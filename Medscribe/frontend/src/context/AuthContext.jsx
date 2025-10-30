import React, { createContext, useContext, useMemo, useState } from 'react';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);

  const signIn = async ({ email }) => {
    // Placeholder auth: accept any email and create a simple user object
    const displayName = email?.split('@')[0] || 'User';
    setUser({ email, displayName });
    return { ok: true };
  };

  const signOut = () => setUser(null);

  const value = useMemo(() => ({ user, signIn, signOut }), [user]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}


