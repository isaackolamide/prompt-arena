import supabase.client
from app.core.config import settings

def get_supabase_client() -> supabase.client.Client:
    """
    Initialize and return a Supabase client configured with the application settings.
    """
    return supabase.create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
