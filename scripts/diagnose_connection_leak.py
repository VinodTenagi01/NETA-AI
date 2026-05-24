#!/usr/bin/env python3
"""
Connection Leak Diagnostics

Analyzes active database connections to identify leaks and hanging processes.

Usage:
    python scripts/diagnose_connection_leak.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings


def parse_db_url(url):
    """Parse DATABASE_URL to extract connection parameters."""
    url = url.replace("postgresql+asyncpg://", "").replace("postgresql://", "")

    if "@" in url:
        credentials, host_db = url.split("@")
        user, password = credentials.split(":") if ":" in credentials else (credentials, "")
    else:
        user, password = "", ""
        host_db = url

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


def run_psql_query(params, query):
    """Run psql query and return raw output."""
    cmd = [
        "psql",
        "-U", params["user"],
        "-h", params["host"],
        "-p", params["port"],
        "-d", params["dbname"],
        "-c", query,
    ]
    if params.get("password"):
        os.environ["PGPASSWORD"] = params["password"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout, result.returncode == 0
    except Exception as e:
        return str(e), False


def diagnose():
    """Run comprehensive diagnostics."""
    print("="*100)
    print("PostgreSQL CONNECTION LEAK DIAGNOSTICS")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*100)

    params = parse_db_url(settings.DATABASE_URL)
    print(f"\nTarget Database: {params['dbname']} @ {params['host']}:{params['port']}")
    print(f"App User: {params['user']}")

    # 1. Overall status
    print("\n" + "="*100)
    print("1. OVERALL CONNECTION STATUS")
    print("="*100)

    query = f"""
    SELECT
        count(*) as total_connections,
        max(extract(epoch from (now() - query_start))) as longest_running_seconds,
        max(extract(epoch from (now() - state_change))) as longest_idle_seconds
    FROM pg_stat_activity
    WHERE datname = '{params['dbname']}';
    """
    output, ok = run_psql_query(params, query)
    if ok:
        print(output)
    else:
        print(f"❌ Cannot connect to PostgreSQL: {output}")
        return False

    # 2. Connections by user
    print("\n" + "="*100)
    print("2. CONNECTIONS BY USER")
    print("="*100)

    query = f"""
    SELECT
        usename,
        count(*) as connection_count,
        string_agg(DISTINCT application_name, ', ') as apps
    FROM pg_stat_activity
    WHERE datname = '{params['dbname']}'
    GROUP BY usename
    ORDER BY connection_count DESC;
    """
    output, ok = run_psql_query(params, query)
    if ok:
        print(output)

    # 3. Connections by state
    print("\n" + "="*100)
    print("3. CONNECTIONS BY STATE")
    print("="*100)

    query = f"""
    SELECT
        state,
        count(*) as count,
        max(extract(epoch from (now() - state_change))) as idle_seconds
    FROM pg_stat_activity
    WHERE datname = '{params['dbname']}'
    GROUP BY state
    ORDER BY count DESC;
    """
    output, ok = run_psql_query(params, query)
    if ok:
        print(output)

    # 4. Long-running transactions
    print("\n" + "="*100)
    print("4. LONG-RUNNING QUERIES (> 1 minute)")
    print("="*100)

    query = f"""
    SELECT
        pid,
        usename,
        application_name,
        state,
        extract(epoch from (now() - query_start)) as running_seconds,
        substring(query, 1, 100) as query_snippet
    FROM pg_stat_activity
    WHERE datname = '{params['dbname']}'
      AND query_start < now() - INTERVAL '1 minute'
    ORDER BY query_start ASC;
    """
    output, ok = run_psql_query(params, query)
    if ok:
        lines = output.strip().split("\n")
        if len(lines) > 2:  # More than header
            print(output)
        else:
            print("✓ No long-running queries")

    # 5. Idle connections (potential leaks)
    print("\n" + "="*100)
    print("5. IDLE CONNECTIONS (> 5 minutes = POTENTIAL LEAKS)")
    print("="*100)

    query = f"""
    SELECT
        pid,
        usename,
        application_name,
        extract(epoch from (now() - state_change)) as idle_seconds,
        extract(epoch from (now() - query_start)) as since_query_seconds,
        backend_start,
        substring(query, 1, 100) as last_query
    FROM pg_stat_activity
    WHERE datname = '{params['dbname']}'
      AND state = 'idle'
    ORDER BY state_change ASC;
    """
    output, ok = run_psql_query(params, query)
    if ok:
        lines = output.strip().split("\n")
        if len(lines) > 2:
            print(output)
            # Highlight old idle connections
            print("\n⚠️  WARNING: Found idle connections. These may be leaks.")
            print("   To terminate idle connections, run:")
            print("   python scripts/cleanup_db_connections.py --kill-idle")
        else:
            print("✓ No idle connections")

    # 6. Configuration
    print("\n" + "="*100)
    print("6. POSTGRESQL CONFIGURATION")
    print("="*100)

    query = """SHOW max_connections;"""
    output, ok = run_psql_query(params, query)
    if ok:
        print(f"max_connections: {output.strip()}")

    query = """SHOW superuser_reserved_connections;"""
    output, ok = run_psql_query(params, query)
    if ok:
        print(f"superuser_reserved_connections: {output.strip()}")

    # 7. Recommendations
    print("\n" + "="*100)
    print("7. RECOMMENDATIONS")
    print("="*100)

    query = f"SELECT count(*) FROM pg_stat_activity WHERE datname = '{params['dbname']}';"
    output, ok = run_psql_query(params, query)
    if ok:
        count_str = output.strip().split("\n")[-1].strip()
        try:
            count = int(count_str)
            print(f"\nCurrent connection count: {count}")

            if count > 90:
                print("\n🔴 CRITICAL: Connection count is extremely high!")
                print("   1. Stop the FastAPI app immediately")
                print("   2. Kill idle connections:")
                print("      python scripts/cleanup_db_connections.py --kill-idle")
                print("   3. If problem persists, kill ALL connections:")
                print("      python scripts/cleanup_db_connections.py --kill-all")
                print("   4. Restart PostgreSQL if needed")

            elif count > 70:
                print("\n🟠 HIGH: Connection count is concerning")
                print("   1. Kill idle connections:")
                print("      python scripts/cleanup_db_connections.py --kill-idle")

            elif count > 50:
                print("\n🟡 MEDIUM: Connection count is elevated")
                print("   1. Review pool configuration in app/database_design/database.py")
                print("   2. Check for stuck/long-running queries:")
                print("      SELECT * FROM pg_stat_activity WHERE state NOT IN ('idle', 'idle in transaction');")

            else:
                print("\n✅ Connection count is normal")
                print("   Current pool configuration is working properly")

        except ValueError:
            print("Could not parse connection count")

    print("\n" + "="*100)
    print("END OF DIAGNOSTICS")
    print("="*100)

    return True


if __name__ == "__main__":
    try:
        diagnose()
    except KeyboardInterrupt:
        print("\n\nDiagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
