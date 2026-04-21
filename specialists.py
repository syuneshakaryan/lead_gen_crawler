from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import requests
import re

def extract_info(title, company_name):
    if not title:
        return None, None

    title = title.replace("–", "-")
    parts = title.split("-")
    if len(parts) < 2:
        return None, None

    name = parts[0].strip()
    role_match = re.search(r"(?i)(.*)\s+at\s+" + re.escape(company_name), parts[1])
    position = role_match.group(1).strip() if role_match else parts[1].strip()
    return name, position

def google_search(company, roles, max_results=5):
    query_roles = " OR ".join([f'"{role}"' for role in roles])
    query = f'site:linkedin.com/in "{company}" {query_roles}'
    bing_query = f'site:linkedin.com/in "{company}" {" OR ".join([f\'"{r}"\' for r in roles])}'
    url = f"https://www.bing.com/search?q={requests.utils.quote(bing_query)}"

    print(f"\n[🔍] Searching for: {query}")
    print(f"[🌐] URL: {url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False for debugging
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 Version/16.1 Safari/605.1.15"
            ])
        )

        page = context.new_page()

        # 🧠 Anti-bot bypass: remove navigator.webdriver flag
        page.add_init_script(
            """Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"""
        )

        page.goto(url, timeout=20000)
        time.sleep(random.uniform(5, 8))  # human-like pause

        html = page.content()
        with open("debug_playwright.html", "w", encoding="utf-8") as f:
            f.write(html)
            print("[💾] Saved full HTML to debug_playwright.html")

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for block in soup.select("div.tF2Cxc"):
            title_el = block.select_one("h3")
            link_el = block.select_one("a")
            snippet_el = block.select_one("div.VwiC3b")

            if link_el and "linkedin.com/in" in link_el.get("href", ""):
                name, position = extract_info(title_el.text if title_el else "", company)
                results.append({
                    "name": name,
                    "position": position,
                    "company": company,
                    "url": link_el["href"],
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else ""
                })

        browser.close()
        return results

# Example usage
if __name__ == "__main__":
    company_name = "ahrefs"
    roles = [
        "seo specialist", "outreach specialist", "smm specialist",
        "marketing specialist", "content creator", "webmaster"
    ]

    leads = google_search(company_name, roles)

    print(f"\n[✅] Found {len(leads)} LinkedIn profiles:\n")
    for i, lead in enumerate(leads, 1):
        print(f"[{i}] Name: {lead['name']}")
        print(f"     Position: {lead['position']}")
        print(f"     Company: {lead['company']}")
        print(f"     LinkedIn: {lead['url']}")
        print(f"     Snippet: {lead['snippet']}")
