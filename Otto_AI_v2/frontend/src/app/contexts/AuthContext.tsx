import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import {
  type Session,
  type SignInWithPasswordCredentials,
  type SignUpCredentials,
  type SignInWithOAuthCredentials,
  supabase,
} from '../lib/supabaseClient';
import type { User } from '@supabase/supabase-js';

// Re-export types for convenience
export type { SignInWithPasswordCredentials, SignUpCredentials };

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signIn: (credentials: SignInWithPasswordCredentials) => Promise<any>;
  signUp: (credentials: SignUpCredentials) => Promise<any>;
  signInWithOAuth: (credentials: SignInWithOAuthCredentials) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  const signIn = useCallback(
    async (credentials: SignInWithPasswordCredentials) => {
      const response = await supabase.auth.signInWithPassword(credentials);
      return response;
    },
    []
  );

  const signUp = useCallback(async (credentials: SignUpCredentials) => {
    const response = await supabase.auth.signUp(credentials);
    return response;
  }, []);

  const signInWithOAuth = useCallback(
    async (credentials: SignInWithOAuthCredentials) => {
      await supabase.auth.signInWithOAuth(credentials);
    },
    []
  );

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
  }, []);

  const value = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signInWithOAuth,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
