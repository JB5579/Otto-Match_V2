"""
Supabase Client Service
Centralized Supabase client for database operations
"""

import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance

    Returns:
        Supabase client configured with environment variables

    Raises:
        ValueError: If required environment variables are not set
    """
    supabase_url = os.getenv('SUPABASE_URL')

    # Check multiple possible env variable names for the key
    supabase_key = (
        os.getenv('SUPABASE_SERVICE_ROLE_KEY') or
        os.getenv('SUPABASE_ANON_KEY') or
        os.getenv('SUPABASE_KEY')
    )

    if not supabase_url:
        raise ValueError('SUPABASE_URL environment variable is required')

    if not supabase_key:
        raise ValueError(
            'Supabase key not found. Set one of: '
            'SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY, or SUPABASE_KEY'
        )

    return create_client(supabase_url, supabase_key)


# Singleton instance (lazy initialization)
_supabase_client: Optional[Client] = None


def get_supabase_client_singleton() -> Client:
    """
    Get singleton Supabase client instance
    Creates the client on first call and reuses it subsequently
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = get_supabase_client()

    return _supabase_client