import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")


def get_table_name(slug: str) -> str:
    """Convert a business slug into a Supabase table name."""
    return "bookings_" + slug.replace("-", "_")


def provision_booking_table(slug: str) -> None:
    """
    Creates the bookings table for a business in Supabase if it doesn't exist.
    Uses a raw SQL call via Supabase's rpc endpoint.
    Requires a 'create_booking_table' function to be set up in Supabase:

    CREATE OR REPLACE FUNCTION create_booking_table(table_name text)
    RETURNS void LANGUAGE plpgsql AS $$
    BEGIN
      EXECUTE format('CREATE TABLE IF NOT EXISTS %I (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        service text NOT NULL,
        booking_date date NOT NULL,
        booking_time time NOT NULL,
        customer_name text NOT NULL,
        customer_phone text NOT NULL,
        customer_line_id text,
        status text DEFAULT ''pending'',
        created_at timestamptz DEFAULT now()
      )', table_name);
    END; $$;
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        print(f"  [skip] Supabase not configured — skipping table provision for {slug}")
        return

    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    table_name = get_table_name(slug)
    try:
        client.rpc("create_booking_table", {"table_name": table_name}).execute()
        print(f"  Supabase table provisioned: {table_name}")
    except Exception as e:
        print(f"  [warn] Supabase provision failed for {slug}: {e}")
