from typing import Optional
import supabase.client
from app.core.config import settings

_supabase_client: Optional[supabase.client.Client] = None

def get_supabase_client() -> supabase.client.Client:
    """
    Initialize and return a Supabase client configured with the application settings.
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
    return _supabase_client
