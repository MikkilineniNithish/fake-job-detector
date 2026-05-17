from google import genai
import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def scrape_job_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        if len(clean_text) > 500:
            return clean_text[:4000]
        return None
    except Exception as e:
        print(f"Scrape error: {e}")
        return None


def verify_company(company_name):
    if not company_name or company_name.lower() in ["unknown", "not mentioned", "none", ""]:
        return "⚠️ No company name found in the job posting"
    try:
        search_name = company_name.strip().split()[0]
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_name}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            extract = data.get("extract", "")
            if extract and len(extract) > 50:
                return f"✅ Company found: {extract[:250]}..."

        search_url = f"https://www.google.com/search?q={company_name.replace(' ', '+')}+company+official+site"
        search_response = requests.get(search_url, headers={
            "User-Agent": "Mozilla/5.0"
        }, timeout=5)
        if search_response.status_code == 200:
            return f"🔍 '{company_name}' — Found online references. Verify at their official website before applying."

        return f"⚠️ Could not verify '{company_name}' — research before applying"
    except Exception as e:
        print(f"Verify error: {e}")
        return f"⚠️ Could not verify '{company_name}' — research before applying"


def analyze_job(job_text):
    prompt = f"""
You are an expert job scam detector. Analyze the following job posting and detect if it's a scam or legitimate.

IMPORTANT: The job posting may be in any language including Telugu, Hindi, Tamil, English or others.
First detect the language, then analyze it fully. Always respond in ENGLISH only.

Check for these 15 red flags:
1. Unrealistic salary (too high for the role)
2. Vague job description
3. No company name or fake company name
4. Asks for personal information upfront
5. Asks for money or payment
6. Too good to be true benefits
7. Poor grammar and spelling
8. Urgency pressure ("apply immediately!")
9. No experience required for high paying job
10. Generic email (gmail/yahoo instead of company email)
11. Work from home with huge pay and no skills needed
12. No interview process mentioned
13. Vague location or "worldwide"
14. Promises of quick money
15. No clear job responsibilities

Job Posting:
{job_text}

Respond in this EXACT format:
LANGUAGE_DETECTED: [language name]
SCAM_SCORE: [0-100]
VERDICT: [SCAM / SUSPICIOUS / LEGITIMATE]
COMPANY_NAME: [extract company name or write "Not Mentioned"]
RED_FLAGS_FOUND: [list the red flags you found]
EXPLANATION: [2-3 sentences explaining your verdict]
SAFE_TO_APPLY: [YES / NO / PROCEED WITH CAUTION]
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    result_text = response.text
    company_match = re.search(r'COMPANY_NAME:\s*(.+)', result_text)
    company_name = company_match.group(1).strip() if company_match else "Unknown"
    company_status = verify_company(company_name)

    return result_text, company_status