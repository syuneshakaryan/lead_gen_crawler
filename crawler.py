import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import random
from config import DEFAULT_HEADERS

# Create a global session to reuse connections
session = requests.Session()

def get_random_headers():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0",
    ]
    headers = DEFAULT_HEADERS.copy()
    headers["User-Agent"] = random.choice(user_agents)
    return headers

def can_fetch_url(url, user_agent=DEFAULT_HEADERS["User-Agent"]):
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{base}/robots.txt"

    rp = RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        can_fetch = rp.can_fetch(user_agent, url)
        return can_fetch if can_fetch is not None else True
    except Exception as e:
        print(f"[⚠️] Failed to parse robots.txt for {url}: {e}")
        return True

def fetch_html(url):
    if not can_fetch_url(url):
        print(f"[❌] Disallowed by robots.txt: {url}")
        return None
    try:
        headers = get_random_headers()
        # Reduced delay: adjust if needed, using slightly shorter randomized delay to speed up process
        time.sleep(random.uniform(1.0, 2.0))
        res = session.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        return res.text
    except Exception as e:
        print(f"[!] Failed to fetch {url}: {e}")
        return None
    
def extract_internal_links(html, base_url, max_links=150):
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    for a in soup.find_all('a', href=True):
        full = urljoin(base_url, a['href'])
        if urlparse(full).netloc == urlparse(base_url).netloc:
            links.add(full)
        if len(links) >= max_links:
            break
    print(f"[i] Found {len(links)} internal links")
    return links

print(f"[🔍] Can fetch? {can_fetch_url('https://example.com')}")
html = fetch_html('https://example.com')
if html:
    print("[✅] Fetched HTML successfully.")
else:
    print("[❌] Still blocked.")