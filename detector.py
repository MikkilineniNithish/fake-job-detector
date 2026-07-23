import re
import requests
from bs4 import BeautifulSoup


def scrape_job_from_url(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
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

        return clean_text

    except Exception as e:
        print("Scrape Error:", e)
        return None


def verify_company(company_name):
    if company_name.lower() == "not mentioned":
        return "⚠️ Company name not found."

    return f"🔍 Please verify '{company_name}' using the official company website or LinkedIn."


def analyze_job(job_text):

    text = job_text.lower()

    score = 0
    flags = []

    if "payment" in text or "registration fee" in text or "pay ₹" in text:
        score += 30
        flags.append("Asks for money before hiring")

    if "whatsapp" in text:
        score += 15
        flags.append("Uses WhatsApp as primary contact")

    if "@gmail.com" in text or "gmail" in text:
        score += 15
        flags.append("Uses Gmail instead of official company email")

    if "immediate joining" in text:
        score += 10
        flags.append("Immediate joining pressure")

    if "no experience" in text:
        score += 10
        flags.append("No experience required")

    if "work from home" in text:
        score += 5
        flags.append("Work from home offer")

    if "limited seats" in text or "apply immediately" in text:
        score += 10
        flags.append("Urgency pressure")

    salary = re.findall(r"\d+\s*lpa|\₹\d+", text)

    if salary:
        score += 10
        flags.append("Unrealistic salary")

    company = "Not Mentioned"

    match = re.search(r"company[:\-]\s*(.*)", job_text, re.IGNORECASE)

    if match:
        company = match.group(1).strip()

    if score >= 60:
        verdict = "SCAM"
        safe = "NO"

    elif score >= 30:
        verdict = "SUSPICIOUS"
        safe = "PROCEED WITH CAUTION"

    else:
        verdict = "LEGITIMATE"
        safe = "YES"

    result = f"""
LANGUAGE_DETECTED: English

SCAM_SCORE: {score}

VERDICT: {verdict}

COMPANY_NAME: {company}

RED_FLAGS_FOUND:
"""

    if flags:
        for f in flags:
            result += f"\n- {f}"
    else:
        result += "\n- No major red flags detected."

    if verdict == "SCAM":
        explanation = (
            "This job posting contains multiple strong scam indicators such as payment requests, "
            "unrealistic salary claims, urgency, or unofficial contact methods. "
            "Avoid applying until the employer is verified through official sources."
        )

    elif verdict == "SUSPICIOUS":
        explanation = (
            "This job posting contains some warning signs that require careful verification. "
            "Check the company's official website, recruiter details, and hiring process before applying."
        )

    else:
        explanation = (
            "This job posting appears to be legitimate based on the available information. "
            "No major scam indicators were detected, but you should still verify the company through its official careers page."
        )

    result += f"""

EXPLANATION:
{explanation}

SAFE_TO_APPLY: {safe}
"""

    company_status = verify_company(company)

    return result, company_status