import os
import re
import requests
from bs4 import BeautifulSoup
from google import genai

# Initialize the Gemini client using the environment variable from Render
# Make sure GEMINI_API_KEY is set in your Render Environment Variables!
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def scrape_job_from_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
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
        return "⚠️ Company name not found. Cannot verify online."
    return f"🔍 Please verify '{company_name}' using the official company website or LinkedIn."


def analyze_job(job_text):
    prompt = f"""
    You are an expert fraud detection system for job postings.
    Analyze the following job posting against 15 known scam indicators:
    1. Unrealistic salary
    2. Vague job description
    3. No company name
    4. Asks for personal information
    5. Asks for money
    6. Too good to be true benefits
    7. Poor grammar
    8. Urgency pressure
    9. No experience needed for high pay
    10. Generic email (gmail/yahoo)
    11. Work from home with huge pay
    12. No interview process
    13. Vague location
    14. Promises of quick money
    15. No clear responsibilities

    Job Posting:
    {job_text}

    Respond in this EXACT format:
    SCAM_SCORE: [0-100]
    VERDICT: [SCAM / SUSPICIOUS / LEGITIMATE]
    COMPANY_NAME: [Extract company name or say "Not Mentioned"]
    RED_FLAGS_FOUND: [List each red flag on a new line, or write "None"]
    EXPLANATION: [2-3 sentences explaining the score and verdict]
    SAFE_TO_APPLY: [NO / PROCEED WITH CAUTION / YES]
    """

    try:
        # Using the updated model name here
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt
        )
        result = response.text
        
        # Extract company name to generate company_status
        company_match = re.search(r'COMPANY_NAME:\s*(.+)', result)
        company = company_match.group(1).strip() if company_match else "Not Mentioned"
        company_status = verify_company(company)
        
        return result, company_status
        
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return f"Error analyzing job: {str(e)}", "Error verifying company"
