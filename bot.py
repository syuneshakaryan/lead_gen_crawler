from crawler import fetch_html, extract_internal_links
from utils import extract_emails, is_contact_like
from urllib.parse import urljoin
import time
import random

def find_contact_pages(base_url):
    html = fetch_html(base_url)
    if not html:
        return []

    links = extract_internal_links(html, base_url)
    contact_like = [url for url in links if is_contact_like(url)]

    # Add fallback guesses
    for path in ["/contact", "/contactus", "/contact-us", "/support"]:
        contact_url = urljoin(base_url, path)
        if contact_url not in contact_like:
            contact_like.append(contact_url)

    return contact_like

def extract_emails_from_urls(urls):
    found = set()
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        print(f"[🔗] Checking: {url}")
        html = fetch_html(url)
        if html:
            emails = extract_emails(html)
            if emails:
                print(f"[📧] Found emails in {url}: {emails}")
            found.update(emails)
        time.sleep(random.uniform(0.5, 2.0))  # small pause between checks
    return list(found)

def find_by_rules(domain):
    contact_pages = find_contact_pages(domain)
    return extract_emails_from_urls(contact_pages)
