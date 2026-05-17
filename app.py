from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from detector import analyze_job, scrape_job_from_url, client
from datetime import datetime, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import PyPDF2
import io
import re
import shortuuid

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

IST = timezone(timedelta(hours=5, minutes=30))
class SharedReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(20), unique=True)
    company_name = db.Column(db.String(200))
    verdict = db.Column(db.String(50))
    scam_score = db.Column(db.Integer)
    safe_to_apply = db.Column(db.String(50))
    red_flags = db.Column(db.Text)
    explanation = db.Column(db.Text)
    company_status = db.Column(db.Text)
    created_at = db.Column(db.String, default=lambda: datetime.now(IST).strftime("%d %b %Y"))
class JobAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), default="Unknown")
    verdict = db.Column(db.String(50))
    scam_score = db.Column(db.Integer)
    safe_to_apply = db.Column(db.String(50))
    red_flags = db.Column(db.Text)
    explanation = db.Column(db.Text)
    company_status = db.Column(db.Text)
    analyzed_at = db.Column(db.String, default=lambda: datetime.now(IST).strftime("%d %b %Y"))

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/api/analytics")
def api_analytics():
    jobs = JobAnalysis.query.all()
    total = len(jobs)

    if total == 0:
        return jsonify({"error": "No data yet"})

    # Verdict counts
    verdicts = {"SCAM": 0, "SUSPICIOUS": 0, "LEGITIMATE": 0}
    for j in jobs:
        v = j.verdict.strip().upper()
        if v in verdicts:
            verdicts[v] += 1

    # Score ranges
    score_ranges = {"0-20": 0, "21-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
    for j in jobs:
        s = j.scam_score
        if s <= 20: score_ranges["0-20"] += 1
        elif s <= 40: score_ranges["21-40"] += 1
        elif s <= 60: score_ranges["41-60"] += 1
        elif s <= 80: score_ranges["61-80"] += 1
        else: score_ranges["81-100"] += 1

    # Average score
    avg_score = round(sum(j.scam_score for j in jobs) / total)

    # Most common red flags
    all_flags = []
    for j in jobs:
        if j.red_flags and j.red_flags != "None":
            lines = j.red_flags.split("\n")
            for line in lines:
                line = line.strip()
                if line:
                    all_flags.append(line[:50])

    flag_counts = {}
    for f in all_flags:
        flag_counts[f] = flag_counts.get(f, 0) + 1

    top_flags = sorted(flag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return jsonify({
        "total": total,
        "verdicts": verdicts,
        "score_ranges": score_ranges,
        "avg_score": avg_score,
        "top_flags": [{"flag": f, "count": c} for f, c in top_flags],
        "scam_percentage": round((verdicts["SCAM"] / total * 100))
    })

@app.route("/scrape", methods=["POST"])
def scrape():
    data = request.get_json()
    url = data.get("url", "")
    if not url.strip():
        return jsonify({"error": "Please enter a URL!"})
    job_text = scrape_job_from_url(url)
    if not job_text:
        return jsonify({"error": "Could not extract job text from this URL."})
    return jsonify({"job_text": job_text})

@app.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF uploaded!"})
    file = request.files["pdf"]
    if file.filename == "":
        return jsonify({"error": "No file selected!"})
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF!"})
        return jsonify({"job_text": text[:4000]})
    except Exception as e:
        return jsonify({"error": f"PDF reading failed: {str(e)}"})

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    job_text = data.get("job_text", "")
    if not job_text.strip():
        return jsonify({"error": "Please paste a job posting!"})

    result, company_status = analyze_job(job_text)

    score_match = re.search(r'SCAM_SCORE:\s*(\d+)', result)
    verdict_match = re.search(r'VERDICT:\s*(.+)', result)
    company_match = re.search(r'COMPANY_NAME:\s*(.+)', result)
    flags_match = re.search(r'RED_FLAGS_FOUND:\s*([\s\S]*?)(?=EXPLANATION:)', result)
    explanation_match = re.search(r'EXPLANATION:\s*([\s\S]*?)(?=SAFE_TO_APPLY:)', result)
    safe_match = re.search(r'SAFE_TO_APPLY:\s*(.+)', result)

    job = JobAnalysis(
        company_name=company_match.group(1).strip() if company_match else "Unknown",
        verdict=verdict_match.group(1).strip() if verdict_match else "Unknown",
        scam_score=int(score_match.group(1)) if score_match else 0,
        safe_to_apply=safe_match.group(1).strip() if safe_match else "Unknown",
        red_flags=flags_match.group(1).strip() if flags_match else "None",
        explanation=explanation_match.group(1).strip() if explanation_match else "-",
        company_status=company_status
    )
    db.session.add(job)
    db.session.commit()

    return jsonify({"result": result, "company_status": company_status})

@app.route("/api/history")
def api_history():
    jobs = JobAnalysis.query.order_by(JobAnalysis.id.desc()).all()
    return jsonify([{
        "id": j.id,
        "company_name": j.company_name,
        "verdict": j.verdict,
        "scam_score": j.scam_score,
        "safe_to_apply": j.safe_to_apply,
        "analyzed_at": j.analyzed_at
    } for j in jobs])

@app.route("/api/stats")
def api_stats():
    total = JobAnalysis.query.count()
    scams = JobAnalysis.query.filter_by(verdict="SCAM").count()
    legitimate = JobAnalysis.query.filter_by(verdict="LEGITIMATE").count()
    suspicious = JobAnalysis.query.filter_by(verdict="SUSPICIOUS").count()
    return jsonify({
        "total": total,
        "scams": scams,
        "legitimate": legitimate,
        "suspicious": suspicious,
        "scam_percentage": round((scams / total * 100) if total > 0 else 0)
    })

@app.route("/download-report", methods=["POST"])
def download_report():
    data = request.get_json()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('title', fontSize=20, fontName='Helvetica-Bold',
                                  textColor=colors.HexColor('#cc0000'), spaceAfter=10)
    story.append(Paragraph("Fake Job Detector - Analysis Report", title_style))
    story.append(Spacer(1, 10))

    date_style = ParagraphStyle('date', fontSize=10, textColor=colors.grey)
    story.append(Paragraph(f"Generated on: {datetime.now(IST).strftime('%d %b %Y')}", date_style))
    story.append(Spacer(1, 20))

    verdict = data.get('verdict', 'Unknown')
    score = data.get('score', 0)
    company = data.get('company_name', 'Unknown')
    safe = data.get('safe', 'Unknown')
    flags = data.get('flags', 'None')
    explanation = data.get('explanation', '-')
    company_status = data.get('company_status', '-')

    table_data = [
        ['Field', 'Result'],
        ['Company Name', company],
        ['Verdict', verdict],
        ['Scam Score', f"{score}/100"],
        ['Safe to Apply', safe],
    ]

    table = Table(table_data, colWidths=[200, 280])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#cc0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    section_style = ParagraphStyle('section', fontSize=13, fontName='Helvetica-Bold',
                                    textColor=colors.HexColor('#cc0000'), spaceAfter=6)
    body_style = ParagraphStyle('body', fontSize=10, leading=16, textColor=colors.black)

    story.append(Paragraph("Red Flags Found", section_style))
    story.append(Paragraph(flags.replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("AI Explanation", section_style))
    story.append(Paragraph(explanation, body_style))
    story.append(Spacer(1, 15))

    story.append(Paragraph("Company Verification", section_style))
    story.append(Paragraph(company_status, body_style))
    story.append(Spacer(1, 20))

    footer_style = ParagraphStyle('footer', fontSize=9, textColor=colors.grey)
    story.append(Paragraph("This report was generated by Fake Job Detector — AI powered scam detection tool.", footer_style))

    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"job_report_{datetime.now(IST).strftime('%d%m%Y')}.pdf",
                     mimetype='application/pdf')
@app.route("/match")
def match():
    return render_template("match.html")

@app.route("/api/match", methods=["POST"])
def api_match():
    data = request.get_json()
    resume_text = data.get("resume_text", "")
    job_text = data.get("job_text", "")

    if not resume_text.strip() or not job_text.strip():
        return jsonify({"error": "Please provide both resume and job description!"})

    prompt = f"""
You are an expert career counselor and HR specialist. Analyze the resume against the job description.

Resume:
{resume_text}

Job Description:
{job_text}

Respond in this EXACT format:
MATCH_SCORE: [0-100]
VERDICT: [STRONG MATCH / GOOD MATCH / PARTIAL MATCH / WEAK MATCH]
MATCHING_SKILLS: [list skills from resume that match the job]
MISSING_SKILLS: [list important skills required but missing from resume]
EXPERIENCE_FIT: [YES / PARTIAL / NO]
RECOMMENDATION: [2-3 sentences of honest advice for this candidate]
INTERVIEW_TIPS: [2-3 specific tips for this particular job interview]
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return jsonify({"result": response.text})
@app.route("/api/share", methods=["POST"])
def share_report():
    data = request.get_json()
    slug = shortuuid.ShortUUID().random(length=8)

    report = SharedReport(
        slug=slug,
        company_name=data.get("company_name", "Unknown"),
        verdict=data.get("verdict", "Unknown"),
        scam_score=data.get("score", 0),
        safe_to_apply=data.get("safe", "Unknown"),
        red_flags=data.get("flags", "None"),
        explanation=data.get("explanation", "-"),
        company_status=data.get("company_status", "-")
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({"slug": slug})

@app.route("/report/<slug>")
def view_report(slug):
    report = SharedReport.query.filter_by(slug=slug).first()
    if not report:
        return "<h2 style='font-family:sans-serif;padding:40px;color:#ff4d4d'>Report not found!</h2>", 404
    return render_template("report.html", report=report)
if __name__ == "__main__":
    app.run(debug=True)