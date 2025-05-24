-- This is the schema for the license_keys table in Supabase
-- Copy and paste this into the Supabase SQL editor

-- Create the license_keys table
CREATE TABLE IF NOT EXISTS license_keys (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  key TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  email TEXT NOT NULL,
  order_id TEXT NOT NULL,
  product_id TEXT NOT NULL,
  product_name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT TRUE
);

-- Create an index on the key field for faster lookups
CREATE INDEX IF NOT EXISTS license_keys_key_idx ON license_keys(key);

-- Create an index on the email field for faster lookups
CREATE INDEX IF NOT EXISTS license_keys_email_idx ON license_keys(email);
