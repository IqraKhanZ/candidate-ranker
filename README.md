# Redrob Candidate Discoverer & Ranker

An offline, high-performance candidate evaluation and ranking system tailored to discover and rank the top 100 best-fit candidates from a pool of 100,000 for a **Senior AI Engineer** role.

---

## 🔗 Project Links

- **Live Deployed App (Railway)**: https://web-production-974dc.up.railway.app
- **PPT Presentation Slide Deck**: [Redrob_Candidate_Ranker_Submission.pptx](./Redrob_Candidate_Ranker_Submission.pptx)
- **Generated Output File**: [submission.csv](./submission.csv) (This file is generated automatically upon running the scoring engine)

---

## 📦 Dataset Source

The 100,000-candidate dataset is **not** hosted directly in this repository due to its large size (~487 MB). 
- To run the code, ensure the candidate pool file `candidates.jsonl` (or the compressed version `candidates.jsonl.gz`) is placed at the root of the project directory or specified correctly via CLI arguments.

---

## ⚡ Quick Start (Local Setup)

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Install the minimal dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the CLI Pipeline
Process the candidate pool streaming, score them in parallel, and export the top 100 to `submission.csv`:
```bash
python rank.py --candidates ../candidates.jsonl --out ./submission.csv
```
*Expected execution time: ~30 seconds for 100K candidates.*

---

## 🛠️ Approach & Methodology

Our solution is engineered around a two-stage rule-based evaluation pipeline, designed to execute efficiently on low-compute (CPU-only, ≤16GB RAM) environments in under 5 minutes.

### 1. Honeypot Screening Filter
To avoid simple keyword-stuffing bots and invalid resume profiles, a short-circuit detector immediately filters out fraudulent applications (assigning a score of `0.0`):
- **Timeline Impossibility**: Flags candidates whose calculated birth year (assuming work started at age 22) implies they were under 16 when they started their first job.
- **Skills Contradiction**: Flags candidates claiming "expert" level proficiency in $\ge 3$ skills with `0 months` of experience.
- **Experience Contradiction**: Flags candidates whose total sum of career history months is less than half of their profile's claimed `years_of_experience`.
- **Profile Completeness Contradiction**: Flags candidates claiming a 100% profile completeness score but having an empty profile summary or zero career history roles.

### 2. Composite Scoring Model
If a candidate passes the honeypot filter, a composite score is computed:
$$\text{Final Score} = \text{JD Match Score} \times \text{Behavioral Modifier}$$

- **JD Match Score (Weighted sum of features)**:
  - **Skills Substance (35%)**: Analyzes description texts in the candidate's career history for action phrases indicating they *built* ML infrastructure (e.g. `trained`, `fine-tuned`, `model serving`, `feature store`) and retrieval systems (e.g. `dense retrieval`, `vector databases`, `NDCG`), weighted by recency.
  - **Career Trajectory (30%)**: Scores title matches (preferring `ML Engineer`, `AI Engineer` over general developer titles), calculates product vs. services ratio (penalizing pure IT services consulting backgrounds), checks tenure stability, and evaluates progression (promotions from junior to senior/staff roles).
  - **Overall Experience (15%)**: Assesses the candidate's total years of experience against the target band (optimal score at 5-9 years) and applies a multiplier for years spent in ML-specific roles.
  - **CS Education (10%)**: Scores the candidate's academic tier and checks for Computer Science / STEM fields of study.
  - **Location Fit (10%)**: Checks if candidate resides in preferred hubs (Pune, Noida, Delhi NCR) or is willing to relocate.
- **Behavioral Modifier**: Multiplies the JD Match Score by an engagement coefficient ($[0.3, 1.0]$) reflecting their platform activity recency, open-to-work flags, recruiter response rates, and Redrob skill assessment scores.

---

## 🧰 Technologies & Tools Used

### Backend Engine (Python)
- **Standard Library Modules**:
  - `re`: Precompiled regular expressions compiled at module level for high-speed string scanning.
  - `multiprocessing`: Spawns a parallel worker pool utilizing CPU cores to split scoring computations.
  - `json` & `gzip`: Parses JSON lines streaming on-the-fly, avoiding high memory overhead.
  - `csv`: Generates the standards-compliant submission schema.
- **External Dependencies**:
  - `python-dateutil`: For robust parsing and calculations on platform activity dates.
  - `tqdm`: To visualize dataset loading and scoring progress in the terminal.

### Frontend Web UI & Export
- **React & Tailwind CSS (via CDN)**: Serves a premium, glassmorphic dark-mode recruiter console with zero setup.
- **jsPDF & AutoTable (via CDN)**: Generates and formats a downloadable, landscape A4 PDF report table on the client side.
