/**
 * Simple test to verify Supabase client initialization
 * Run with: npm run test:supabase
 */

/// <reference types="node" />

import { createClient } from '@supabase/supabase-js';

// Load environment variables directly for Node.js test
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase environment variables');
  console.error('   Required: SUPABASE_URL and SUPABASE_ANON_KEY');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseAnonKey);

async function testSupabaseConnection() {
  console.log('🧪 Testing Supabase Client Initialization...\n');

  // Test 1: Client is initialized
  console.log('✓ Test 1: Supabase client created');
  console.log('  Supabase URL:', supabaseUrl);
  console.log('  Client exists:', !!supabase);

  // Test 2: Check current session (should be null or valid session)
  console.log('\n✓ Test 2: Checking current session...');
  try {
    const { data, error } = await supabase.auth.getSession();

    if (error) {
      console.log('  ⚠ Error getting session:', error.message);
    } else {
      console.log('  Session check successful');
      console.log('  Has active session:', !!data.session);
      if (data.session) {
        console.log('  User ID:', data.session.user.id);
      }
    }
  } catch (err) {
    console.log('  ⚠ Exception during session check:', err);
  }

  // Test 3: Check if we can access auth configuration
  console.log('\n✓ Test 3: Auth configuration check');
  console.log('  Auth methods available:', {
    signIn: typeof supabase.auth.signInWithPassword === 'function',
    signUp: typeof supabase.auth.signUp === 'function',
    signOut: typeof supabase.auth.signOut === 'function',
    signInWithOAuth: typeof supabase.auth.signInWithOAuth === 'function',
  });

  console.log('\n✅ All Supabase client tests completed!');
  console.log('\n📝 Next steps:');
  console.log('  1. Test authentication with real credentials');
  console.log('  2. Implement AuthContext and AuthProvider');
  console.log('  3. Create authentication UI components');
}

// Run test
testSupabaseConnection().catch(console.error);
