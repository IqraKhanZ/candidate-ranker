# Redrob Candidate Discoverer & Ranker

An offline, high-performance candidate evaluation and ranking system tailored to discover and rank the top 100 best-fit candidates from a pool of 100,000 for a **Senior AI Engineer** role. 

This repository implements streaming loaders, trap/honeypot filters, multi-core parallel scoring, and features an interactive React web interface with PDF report export.

---

## 📂 Project Structure

```text
redrob-ranker/
├── rank.py               # Main CLI Entry Point (Streaming & Multiprocessing)
├── scorer.py             # Composite Candidate Scoring Logic
├── features.py           # Sub-scorers (Experience, Location, Behavioral, CS Education)
├── honeypot.py           # Trap & Fraudulent Profile Catcher
├── reasoning.py          # Data-Accurate Reasoning Generator
├── server.py             # Flask Web Server (REST API & Web UI static router)
├── index.html            # React Dashboard Frontend (Tailwind + jsPDF CDNs)
├── check.py              # Quality Sanity Check Script
└── requirements.txt      # Minimal Dependencies
```

---

## ⚡ Quick Start (Local Setup)

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Install the minimal dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the CLI Pipeline
Process the 100,000 candidates streaming, score them in parallel, and export the top 100 to `submission.csv`:
```bash
python rank.py --candidates ../candidates.jsonl --out ../submission.csv
```
*Expected execution time: ~30 seconds for 100K candidates.*

### 3. Validate Format compliant (Official Hackathon Script)
Verify your output file complies with all formatting rules (100 rows, score order, tie-breaks):
```bash
python validate_submission.py submission.csv
```

### 4. Run Sanity Checks
Ensure the output quality aligns with hidden constraints (no low-value titles, proper experience ranges, active candidates):
```bash
python check.py --submission ../submission.csv --candidates ../candidates.jsonl
```

---

## 🌐 Web Console & PDF Exporter

To run the interactive SaaS dashboard:
```bash
python server.py
```
Open your browser and navigate to: **[http://localhost:5000/](http://localhost:5000/)**

### Features:
- **Recruiter JD Input**: Paste your Job Description (or use the one-click templates).
- **Three Data Sources**: 
  - **Local Path**: Specify a candidate file on your local machine.
  - **Online Link**: Paste a dataset download URL.
  - **File Upload**: Drag and drop a `.jsonl` or `.jsonl.gz` dataset file.
- **Landscape PDF Export**: Download a print-ready, clean candidates table report (A4 landscape) via `jsPDF`.

---

## ⚙️ Scoring Mechanics

Candidates are evaluated through a two-stage filter:

1. **Honeypot Filter**: Short-circuits invalid profiles to a score of `0.0`. Catches:
   - Timeline anomalies (YoE implies starting work under age 16).
   - Contradictory skills (Expert proficiency with 0 months duration).
   - Experience mismatch (Stated YoE double the sum of career history durations).
   - Profile completeness mismatch (Completeness = 100% with no career history or summary).

2. **Composite Score Formula**:
   $$\text{Final Score} = (0.35 \times \text{Skills} + 0.30 \times \text{Trajectory} + 0.15 \times \text{Experience} + 0.10 \times \text{Location} + 0.10 \times \text{Education}) \times \text{Behavioral Modifier}$$
   - **Skills (Substance)**: Looks for action phrases matching production deployments, ML infrastructure building, and retrieval systems.
   - **Trajectory**: Evaluates title relevance, tenure stability, seniority progression, and penalizes pure service consulting backgrounds.
   - **Behavioral**: Multiplier based on platform activity recency, open-to-work flag, response rate, assessment scores, and verified contact status.

---

## 🚀 Deployment Instructions

### Option 1: Hugging Face Spaces (Recommended for Sandbox link)
1. Create a new space on [Hugging Face Spaces](https://huggingface.co/spaces) and choose the **Docker** SDK template.
2. Create a `Dockerfile` at the root of the project:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . /app
   RUN pip install --no-cache-dir -r requirements.txt
   EXPOSE 7860
   ENV PORT=7860
   CMD ["python", "server.py"]
   ```
3. Update the port binding in `server.py` to use `ENV` variable `PORT` or default to `7860`:
   ```python
   PORT = int(os.environ.get("PORT", 5000))
   ```
4. Push the code to the Hugging Face space repository.

### Option 2: Render / Heroku
Deploy the Flask app directly. Set the start command to `python server.py` and bind port using the environment variable.
