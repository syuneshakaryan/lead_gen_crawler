import streamlit as st
import concurrent.futures
import csv
import io

from bot import find_by_rules  
from utils import is_valid_email, is_deliverable_email  # Mail validation functions

def process_single_domain(domain: str, idx: int) -> dict:
    domain = domain.strip()
    if not domain.startswith("http"):
        domain = "https://" + domain
    st.write(f"[{idx}] Processing {domain}...")
    
    # Extract emails using bot logic
    emails = find_by_rules(domain)
    # Filter emails: only include those that pass validation.
    valid_emails = [email for email in emails if is_valid_email(email) and is_deliverable_email(email)]
    return {"Domain": domain, "Valid List": valid_emails}

def main():
    st.title("Website Email Extractor")
    st.markdown("Enter a list of websites (one per line) to extract emails.")
    websites_input = st.text_area("Websites", height=200)

    if st.button("Extract Emails"):
        websites = [line.strip() for line in websites_input.splitlines() if line.strip()]
        if not websites:
            st.error("No websites provided!")
            return

        st.info(f"Processing {len(websites)} website(s). Please wait ...")
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(process_single_domain, website, idx + 1): website
                for idx, website in enumerate(websites)
            }
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    st.error(f"Error processing {futures[future]}: {e}")

        # Create an in-memory CSV (each row: Domain, Email)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Domain", "Email"])
        for res in results:
            for email in res.get("Valid List", []):
                writer.writerow([res.get("Domain"), email])
        csv_value = output.getvalue()

        st.download_button(
            label="Download CSV",
            data=csv_value,
            file_name="results.csv",
            mime="text/csv",
        )
        st.success("Processing completed!")

if __name__ == "__main__":
    main()