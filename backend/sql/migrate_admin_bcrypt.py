#!/usr/bin/env python3
"""
Migrate admin password hash from SHA256 to bcrypt.

Usage (run inside backend container or locally with DATABASE_URL set):

    python3 sql/migrate_admin_bcrypt.py --email admin@optimus.local --password <new-password>

The script:
  1. Connects to Postgres via DATABASE_URL env var
  2. Generates a bcrypt hash (rounds=12) of the given password
  3. Updates the user record in place
  4. Verifies the update succeeded
"""
import argparse
import os
import sys

try:
    import bcrypt
except ImportError:
    sys.exit("ERROR: bcrypt not installed. Run: pip install bcrypt>=4.1.0")

try:
    import psycopg
except ImportError:
    sys.exit("ERROR: psycopg not installed. Run: pip install psycopg[binary]>=3.2.0")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate user password to bcrypt")
    parser.add_argument("--email", required=True, help="User email to migrate")
    parser.add_argument("--password", required=True, help="New password (will be hashed with bcrypt)")
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        sys.exit("ERROR: DATABASE_URL environment variable is not set")

    new_hash = bcrypt.hashpw(args.password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")

    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute("SELECT id, email FROM users WHERE email = %s", (args.email,))
        row = cur.fetchone()
        if not row:
            sys.exit(f"ERROR: No user found with email '{args.email}'")

        cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, args.email))
        conn.commit()

        # Verify
        cur.execute("SELECT password_hash FROM users WHERE email = %s", (args.email,))
        stored = cur.fetchone()[0]
        assert stored.startswith("$2"), "Hash was not stored as bcrypt"

    print(f"OK: password for '{args.email}' migrated to bcrypt successfully")
    print(f"    Hash prefix: {stored[:20]}...")


if __name__ == "__main__":
    main()
