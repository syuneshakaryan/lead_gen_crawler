import time
import sqlite3
from urllib.parse import urlparse
import concurrent.futures

import pandas as pd
from bot import find_by_rules
from utils import is_valid_email, is_deliverable_email
from crawler import fetch_html  # used to check base HTML access

def process_single_domain(domain, idx):
    domain = domain.strip()
    if not domain.startswith("http"):
        domain = "https://" + domain

    print(f"[{idx}] Processing {domain}...")
    # First, check if the website is accessible by fetching its base HTML.
    base_html = fetch_html(domain)
    if base_html is None:
        # Blocked access or unreachable – mark as blocked and skip further crawling.
        access_denied = "Yes"
        valid_emails = []
    else:
        access_denied = "No"
        # Extract emails using find_by_rules and then filter valid ones.
        emails = find_by_rules(domain)
        valid_emails = [email for email in emails if is_valid_email(email) and is_deliverable_email(email)]
    return {
        "Domain": domain,
        "Valid List": valid_emails,
        "Access Denied": access_denied
    }

def process_domains(domains):
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_single_domain, d, idx) for idx, d in enumerate(domains, start=1)]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    return results

def insert_into_db(results, db_file="results.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # Create table with the new access_denied column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            website TEXT,
            email TEXT,
            access_denied TEXT
        )
    """)
    rows = []
    for result in results:
        domain = result["Domain"]
        access_denied = result.get("Access Denied", "No")
        # If there are valid emails, insert one row per email.
        if result.get("Valid List"):
            for email in result["Valid List"]:
                rows.append((domain, email, access_denied))
        else:
            # Otherwise, add a row with an empty email field.
            rows.append((domain, "", access_denied))
    if rows:
        cursor.executemany("INSERT INTO emails (website, email, access_denied) VALUES (?, ?, ?)", rows)
    conn.commit()
    conn.close()

def main():
    input_file = "domains.txt"
    output_file = "results.csv"
    db_file = "results.db"

    with open(input_file, "r") as f:
        domains = f.readlines()

    start = time.time()
    results = process_domains(domains)

    # Create an in-memory CSV (each row: Domain, Email, Access Denied)
    flattened_rows = []
    for res in results:
        access_denied = res.get("Access Denied", "No")
        if res.get("Valid List"):
            for email in res["Valid List"]:
                flattened_rows.append({
                    "Domain": res["Domain"],
                    "Email": email,
                    "Access Denied": access_denied
                })
        else:
            flattened_rows.append({
                "Domain": res["Domain"],
                "Email": "",
                "Access Denied": access_denied
            })

    df = pd.DataFrame(flattened_rows)
    df.to_csv(output_file, index=False)

    # Save results to SQLite DB with the access_denied column
    insert_into_db(results, db_file)

    print(f"\n✅ Finished processing {len(domains)} domains.")
    print(f"📁 Results saved to {output_file} and database file {db_file}")
    print(f"⏱ Total time: {round(time.time() - start, 2)} seconds.")

if __name__ == "__main__":
    main()