# 🛡️ Fake Job Detector — AI-Powered Scam Detection Tool

A full-stack AI-powered web application that detects fraudulent job postings using Google Gemini AI. Built to help students and job seekers avoid scams while applying for jobs online.

🔗 **Live Demo:** https://fake-job-detector-c94u.onrender.com

---

## 🚀 Features

- 🤖 **AI Scam Detection** — Analyzes 15+ scam indicators using Google Gemini AI
- 📊 **Scam Score** — Gives a 0-100 trust score for every job posting
- 🏢 **Company Verification** — Verifies if the company exists online
- 📄 **PDF Upload** — Upload job postings as PDF files
- 🔗 **URL Scraping** — Fetch job text directly from career pages
- 🌐 **Multilingual Support** — Analyzes jobs in Telugu, Hindi, Tamil, and English
- 📈 **Analytics Dashboard** — Charts showing scam trends and red flag patterns
- 📊 **History Dashboard** — Track all previously analyzed job postings
- 📄 **PDF Report Download** — Download detailed analysis as PDF
- 🔗 **Shareable Reports** — Generate shareable links for any analysis
- 🎯 **Resume vs Job Match** — Upload resume and check match score against job description

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Backend | Python, Flask |
| AI Brain | Google Gemini 2.5 Flash API |
| Database | SQLite + Flask-SQLAlchemy |
| PDF Generation | ReportLab |
| Web Scraping | BeautifulSoup4, Trafilatura |
| Deployment | Render Cloud Platform |
| Version Control | Git, GitHub |

---

## 📸 Pages

- **Home** — Paste text, upload PDF, or fetch from URL
- **History** — View all analyzed job postings with dates
- **Analytics** — Charts showing verdict distribution and red flag frequency
- **Resume Match** — Upload resume PDF and compare against job description
- **Shared Report** — Publicly shareable analysis report page

---

## ⚙️ How to Run Locally

```bash
# Clone the repository
git clone https://github.com/MikkilineniNithish/fake-job-detector.git
cd fake-job-detector

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key
echo GEMINI_API_KEY=your_key_here > .env

# Run the app
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

---

## 🔍 How It Works

1. User pastes a job posting (text, PDF, or URL)
2. Google Gemini AI analyzes it against 15 scam indicators
3. App generates a Scam Score (0-100) with detailed explanation
4. Company name is verified against Wikipedia and web
5. Results saved to database for history and analytics
6. User can download PDF report or share a link

---

## 📊 Scam Indicators Checked

1. Unrealistic salary
2. Vague job description
3. No company name
4. Asks for personal information
5. Asks for money or payment
6. Too good to be true benefits
7. Poor grammar and spelling
8. Urgency pressure
9. No experience required for high pay
10. Generic email (gmail/yahoo)
11. Work from home with huge pay
12. No interview process
13. Vague location
14. Promises of quick money
15. No clear job responsibilities

---

## 👨‍💻 Developer

**Mikkilineni Nithish**
- 📧 mikkilineninithish@gmail.com
- 🔗 [LinkedIn](https://linkedin.com/in/your-profile)
- 🐙 [GitHub](https://github.com/MikkilineniNithish)

---

## 📄 License

This project is open source and available under the MIT License.