#!/usr/bin/env python3
"""
PostgreSQL Connection Cleanup Utility

Diagnoses and terminates idle/stuck database connections.
Run this when you see: "FATAL: sorry, too many clients already"

Usage:
    python scripts/cleanup_db_connections.py [--kill-idle] [--kill-all]

Options:
    --kill-idle : Terminate idle connections (safe)
    --kill-all  : Terminate ALL app connections (warning: will disconnect app!)
"""

import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings

# Extract PostgreSQL connection info from DATABASE_URL
# Format: postgresql+asyncpg://user:password@host:port/dbname
def parse_db_url(url):
    """Parse DATABASE_URL to extract connection parameters."""
    url = url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

    # Split credentials from host
    if "@" in url:
        credentials, host_db = url.split("@")
        user, password = credentials.split(":") if ":" in credentials else (credentials, "")
    else:
        user, password = "", ""
        host_db = url

    # Split host:port from dbname
    if "/" in host_db:
        host_port, dbname = host_db.split("/", 1)
    else:
        host_port = host_db
        dbname = "postgres"

    host = host_port.split(":")[0]
    port = host_port.split(":")[1] if ":" in host_port else "5432"

    return {
        "user": user or "postgres",
        "password": password,
        "host": host or "localhost",
        "port": port,
        "dbname": dbname or "postgres",
    }


def get_psql_command(params):
    """Build psql command with connection parameters."""
    cmd = [
        "psql",
        "-U", params["user"],
        "-h", params["host"],
        "-p", params["port"],
        "-d", params["dbname"],
    ]
    if params.get("password"):
        # Set password via PGPASSWORD environment variable
        os.environ["PGPASSWORD"] = params["password"]
    return cmd


def run_sql_query(params, query):
    """Execute SQL query and return results."""
    cmd = get_psql_command(params) + ["-c", query]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None
        return result.stdout
    except Exception as e:
        print(f"Failed to execute query: {e}")
        return None


def show_connections(params):
    """Display active connections."""
    print("\n" + "="*80)
    print("ACTIVE DATABASE CONNECTIONS")
    print("="*80)

    query = """
    SELECT
        pid,
        usename,
        application_name,
        state,
        query_start,
        state_change,
        substring(query, 1, 80) as query
    FROM pg_stat_activity
    WHERE datname = '%s'
    ORDER BY query_start DESC;
    """ % params["dbname"]

    result = run_sql_query(params, query)
    if result:
        print(result)
    else:
        print("Could not retrieve connection information")
        return False
    return True


def count_connections(params):
    """Count total connections."""
    query = f"SELECT count(*) FROM pg_stat_activity WHERE datname = '{params['dbname']}';"
    result = run_sql_query(params, query)
    if result:
        lines = [l.strip() for l in result.split("\n") if l.strip() and l[0].isdigit()]
        if lines:
            return int(lines[0])
    return -1


def show_connection_summary(params):
    """Show summary of connections by state."""
    print("\n" + "="*80)
    print("CONNECTION SUMMARY")
    print("="*80)

    query = """
    SELECT
        state,
        count(*) as count
    FROM pg_stat_activity
    WHERE datname = '%s'
    GROUP BY state
    ORDER BY count DESC;
    """ % params["dbname"]

    result = run_sql_query(params, query)
    if result:
        print(result)

    # Show max connections setting
    query2 = "SHOW max_connections;"
    result2 = run_sql_query(params, query2)
    if result2:
        print("\nPostgreSQL Configuration:")
        print(result2)


def kill_idle_connections(params):
    """Terminate idle connections safely."""
    print("\n" + "="*80)
    print("TERMINATING IDLE CONNECTIONS")
    print("="*80)

    query = """
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '%s'
      AND state = 'idle'
      AND state_change < NOW() - INTERVAL '5 minutes'
      AND pid != pg_backend_pid();
    """ % params["dbname"]

    result = run_sql_query(params, query)
    if result:
        lines = [l.strip() for l in result.split("\n") if l.strip() and l[0] in "tf"]
        killed = sum(1 for line in lines if "t" in line.lower())
        print(f"\nTerminated {killed} idle connections")
        return killed > 0
    return False


def kill_all_app_connections(params):
    """Terminate ALL connections (dangerous!)."""
    print("\n" + "="*80)
    print("WARNING: TERMINATING ALL CONNECTIONS")
    print("="*80)
    print("This will disconnect any running app instances!")

    response = input("\nAre you sure? Type 'yes' to continue: ")
    if response.lower() != "yes":
        print("Cancelled.")
        return False

    query = """
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname = '%s'
      AND pid != pg_backend_pid();
    """ % params["dbname"]

    result = run_sql_query(params, query)
    if result:
        lines = [l.strip() for l in result.split("\n") if l.strip() and l[0] in "tf"]
        killed = sum(1 for line in lines if "t" in line.lower())
        print(f"\nTerminated {killed} connections")
        return True
    return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PostgreSQL connection cleanup utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current connections
  python scripts/cleanup_db_connections.py

  # Kill idle connections (safe)
  python scripts/cleanup_db_connections.py --kill-idle

  # Kill ALL connections (dangerous - disconnects app!)
  python scripts/cleanup_db_connections.py --kill-all
        """
    )
    parser.add_argument("--kill-idle", action="store_true",
                       help="Terminate idle connections")
    parser.add_argument("--kill-all", action="store_true",
                       help="Terminate ALL connections (disconnects app!)")

    args = parser.parse_args()

    # Parse database URL
    print(f"Connecting to: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'unknown'}")
    params = parse_db_url(settings.DATABASE_URL)

    try:
        # Step 1: Show current status
        print("\nChecking connection status...")
        count = count_connections(params)
        if count >= 0:
            print(f"Current connections: {count}")
            if count > 80:
                print("⚠️  WARNING: Connection count is very high!")

        # Step 2: Show details
        if not show_connections(params):
            print("\n❌ Could not connect to PostgreSQL!")
            print("Make sure PostgreSQL is running and credentials are correct.")
            sys.exit(1)

        show_connection_summary(params)

        # Step 3: Action if requested
        if args.kill_idle:
            killed = kill_idle_connections(params)
            if killed:
                count_after = count_connections(params)
                print(f"Connections after cleanup: {count_after}")

        elif args.kill_all:
            killed = kill_all_app_connections(params)
            if killed:
                count_after = count_connections(params)
                print(f"Connections after cleanup: {count_after}")

        else:
            print("\nTo cleanup idle connections, run:")
            print("  python scripts/cleanup_db_connections.py --kill-idle")

        print("\n" + "="*80)
        print("Done.")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
