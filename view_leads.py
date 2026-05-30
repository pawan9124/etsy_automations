import sqlite3
import pandas as pd
from pathlib import Path

DB_FILE = Path(__file__).parent / "leads.db"

def main():
    if not DB_FILE.exists():
        print("No leads database found yet. Run the server and submit a lead first!")
        return

    conn = sqlite3.connect(DB_FILE)
    
    # Read into a pandas DataFrame for a nice, clean table format
    try:
        df = pd.read_sql_query("SELECT id, name, email, etsy_url, timestamp FROM leads", conn)
        if df.empty:
            print("Database exists, but no leads have been captured yet.")
        else:
            print("\n" + "="*80)
            print("🚀 YOUR CAPTURED LEADS")
            print("="*80)
            print(df.to_string(index=False))
            print("="*80 + "\n")
    except Exception as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
