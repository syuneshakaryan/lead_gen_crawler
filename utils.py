import dns.resolver
import re

def extract_emails(html):
    return re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", html)

def is_valid_email(email):
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))

def is_deliverable_email(email):
    domain = email.split('@')[-1]
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception as e:
        print(f"[⚠️ MX Check Failed] {email}: {e}")
        return False

def is_contact_like(url):
    keywords = ['contact', 'support', 'help', 'about', 'team']
    return any(k in url.lower() for k in keywords)
