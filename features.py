# features.py
"""
Feature scorers for Redrob Candidate Ranker.
Reference date: 2026-06-07
"""

import re
from datetime import date

# -----------------------------------------------------------------------------
# Constant Definitions & Precompiled Regex Patterns
# -----------------------------------------------------------------------------

# Core Skills Scorer Keywords (Task 4)
PRODUCTION_PHRASES = [
    re.compile(r"\bdeployed\b", re.IGNORECASE),
    re.compile(r"\bproduction\b", re.IGNORECASE),
    re.compile(r"\bserved\s+\d+[\d,kKmM+]*\s+users\b", re.IGNORECASE),
    re.compile(r"\bat\s+scale\b", re.IGNORECASE),
    re.compile(r"\blatency\b", re.IGNORECASE),
    re.compile(r"\bthroughput\b", re.IGNORECASE),
    re.compile(r"\bmonitoring\b", re.IGNORECASE),
    re.compile(r"\bA/B\s+test(?:ing)?\b", re.IGNORECASE),
    re.compile(r"\brollout\b", re.IGNORECASE),
    re.compile(r"\bpipeline\b", re.IGNORECASE),
]

RETRIEVAL_PHRASES = [
    re.compile(r"\bretrieval\b", re.IGNORECASE),
    re.compile(r"\branking\b", re.IGNORECASE),
    re.compile(r"\bsearch\b", re.IGNORECASE),
    re.compile(r"\brecommendation\b", re.IGNORECASE),
    re.compile(r"\bmatching\b", re.IGNORECASE),
    re.compile(r"\bindex\b", re.IGNORECASE),
    re.compile(r"\brecall\b", re.IGNORECASE),
    re.compile(r"\bprecision\b", re.IGNORECASE),
    re.compile(r"\brelevance\b", re.IGNORECASE),
    re.compile(r"\bre-rank(?:ing)?\b", re.IGNORECASE),
]

ML_ACTION_PHRASES = [
    re.compile(r"\btrained\b", re.IGNORECASE),
    re.compile(r"\bfine-tuned\b", re.IGNORECASE),
    re.compile(r"\binference\b", re.IGNORECASE),
    re.compile(r"\bevaluation\s+pipeline\b", re.IGNORECASE),
    re.compile(r"\bbenchmark\b", re.IGNORECASE),
    re.compile(r"\bfeature\s+pipeline\b", re.IGNORECASE),
    re.compile(r"\bmodel\s+serving\b", re.IGNORECASE),
    re.compile(r"\boffline\s+evaluation\b", re.IGNORECASE),
    re.compile(r"\bonline\s+experiment\b", re.IGNORECASE),
    re.compile(r"\bfeature\s+store\b", re.IGNORECASE),
    re.compile(r"\bmodel\s+registry\b", re.IGNORECASE),
    re.compile(r"\bretraining\b", re.IGNORECASE),
]

# Career Trajectory Scorer Keywords (Task 5)
HIGH_VALUE_TITLES = [
    "ml engineer", "machine learning engineer", "ai engineer",
    "nlp engineer", "search engineer", "ranking engineer",
    "applied scientist", "research engineer", "applied ml",
    "data scientist",      # only if description mentions ML systems
    "senior engineer",     # only if in ML context
    "staff engineer"       # only if in ML context
]

MEDIUM_TITLES = [
    "software engineer", "backend engineer", "data engineer",
    "platform engineer", "systems engineer"
]

LOW_TITLES = [
    "marketing manager", "operations manager", "hr manager",
    "finance manager", "sales manager", "customer support",
    "mechanical engineer", "civil engineer", "graphic designer",
    "content writer", "business analyst", "project manager"
]

SERVICES_COMPANIES = [
    "tcs", "tata consultancy", "wipro", "infosys", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mphasis",
    "hexaware", "mindtree", "l&t infotech", "ltimindtree"
]

# ML context keywords to check for data scientist, senior engineer, staff engineer
ML_SYSTEMS_KEYWORDS = [
    "ml", "machine learning", "ai", "nlp", "deep learning", "neural",
    "embeddings", "retrieval", "ranking", "search", "trained", "fine-tuned",
    "model", "inference", "evaluation", "benchmark", "offline", "online", "feature"
]
ML_SYSTEMS_PATTERN = re.compile(r"\b(" + "|".join(ML_SYSTEMS_KEYWORDS) + r")\b", re.IGNORECASE)

# Seniority words for Progression check
SENIORITY_WORDS = ["senior", "lead", "principal", "staff", "head", "director"]

# Experience Scorer ML Keywords (Task 6)
ML_EXPERIENCE_PHRASES = [
    "machine learning", "deep learning", "nlp", "natural language",
    "retrieval", "ranking", "recommendation", "embeddings",
    "neural network", "transformer", "search system"
]
ML_EXP_PATTERN = re.compile(r"\b(" + "|".join(ML_EXPERIENCE_PHRASES) + r")\b", re.IGNORECASE)

# Location (Task 6)
PREFERRED_CITIES = ["pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "new delhi"]
ACCEPTABLE_CITIES = ["bangalore", "bengaluru", "chennai", "kolkata"]

# Education CS Fields (Task 8)
CS_FIELDS = [
    "computer science", "software engineering", "information technology",
    "machine learning", "artificial intelligence", "data science",
    "mathematics", "statistics", "electrical engineering",
    "electronics", "computational"
]

# Reference date (Task 7)
TODAY = date(2026, 6, 7)

# -----------------------------------------------------------------------------
# 1. Core Skills Scorer (Task 4)
# -----------------------------------------------------------------------------
def score_career_substance(candidate: dict) -> float:
    career_history = candidate.get("career_history", [])
    total_entries = len(career_history)
    
    # 1. Production deployment evidence (40%)
    if total_entries > 0:
        matching_entries_prod = 0
        for entry in career_history:
            desc = entry.get("description", "")
            count = sum(1 for p in PRODUCTION_PHRASES if p.search(desc))
            if count >= 2:
                matching_entries_prod += 1
        production_score = min(1.0, (matching_entries_prod / total_entries) * 1.5)
    else:
        production_score = 0.0

    # 2. Retrieval/ranking system evidence (35%)
    if total_entries > 0:
        weighted_count = 0.0
        for idx, entry in enumerate(career_history):
            desc = entry.get("description", "")
            # check if contains retrieval phrase
            has_retrieval = any(p.search(desc) for p in RETRIEVAL_PHRASES)
            if has_retrieval:
                if idx == 0:
                    weight = 2.0
                elif idx == 1:
                    weight = 1.5
                else:
                    weight = 1.0
                weighted_count += weight
        retrieval_score = min(1.0, weighted_count / (total_entries * 2.0))
    else:
        retrieval_score = 0.0

    # 3. ML systems evidence (25%)
    matching_entries_ml = 0
    for entry in career_history:
        desc = entry.get("description", "")
        count = sum(1 for p in ML_ACTION_PHRASES if p.search(desc))
        if count >= 2:
            matching_entries_ml += 1
    ml_score = min(1.0, matching_entries_ml / max(total_entries, 1))

    final = 0.40 * production_score + 0.35 * retrieval_score + 0.25 * ml_score
    return round(final, 6)

# Alias for Task 8 composite scorer import compatibility
score_core_skills = score_career_substance

# -----------------------------------------------------------------------------
# 2. Career Trajectory Scorer (Task 5)
# -----------------------------------------------------------------------------
def evaluate_title_score(title: str, description: str) -> float:
    title_lower = title.lower()
    desc_lower = description.lower()
    
    # Check High Value Titles
    general_hv = ["ml engineer", "machine learning engineer", "ai engineer", "nlp engineer", "search engineer", "ranking engineer", "applied scientist", "research engineer", "applied ml"]
    if any(hv in title_lower for hv in general_hv):
        return 1.0
        
    if "data scientist" in title_lower:
        if ML_SYSTEMS_PATTERN.search(desc_lower):
            return 1.0
            
    is_senior_staff = ("senior engineer" in title_lower) or ("staff engineer" in title_lower) or \
                      (all(w in title_lower for w in ["senior", "engineer"])) or \
                      (all(w in title_lower for w in ["staff", "engineer"]))
    if is_senior_staff:
        if ML_SYSTEMS_PATTERN.search(desc_lower):
            return 1.0
            
    # Check Medium Titles
    if any(med in title_lower for med in MEDIUM_TITLES):
        return 0.5
        
    # Check Low Titles
    if any(low in title_lower for low in LOW_TITLES):
        return 0.0
        
    return 0.0

def score_career_trajectory(candidate: dict) -> float:
    profile = candidate.get("profile", {})
    career_history = candidate.get("career_history", [])
    
    # Find descriptions for titles
    current_title = profile.get("current_title", "")
    current_desc = ""
    # Use current job description if found, otherwise default to first entry
    for entry in career_history:
        if entry.get("is_current"):
            current_desc = entry.get("description", "")
            break
    if not current_desc and career_history:
        current_desc = career_history[0].get("description", "")

    # 1. Title Relevance (35%)
    title_score = 0.0
    # Title 1: current title
    title_score += evaluate_title_score(current_title, current_desc)
    # Title 2: most recent history title
    if len(career_history) >= 1:
        t2 = career_history[0].get("title", "")
        d2 = career_history[0].get("description", "")
        title_score += evaluate_title_score(t2, d2)
    # Title 3: second most recent history title
    if len(career_history) >= 2:
        t3 = career_history[1].get("title", "")
        d3 = career_history[1].get("description", "")
        title_score += evaluate_title_score(t3, d3)
        
    title_component = title_score / 3.0

    # 2. Product vs services (30%)
    services_months = 0
    total_months = 0
    for entry in career_history:
        comp = entry.get("company", "").lower()
        dur = entry.get("duration_months", 0)
        total_months += dur
        if any(sc in comp for sc in SERVICES_COMPANIES):
            services_months += dur
            
    services_ratio = services_months / max(total_months, 1)
    if services_ratio >= 0.9:
        product_score = 0.1
    elif services_ratio >= 0.6:
        product_score = 0.4
    elif services_ratio >= 0.3:
        product_score = 0.7
    else:
        product_score = 1.0

    # 3. Tenure stability (20%)
    if len(career_history) > 0:
        avg_tenure = total_months / len(career_history)
        has_long_tenure = any(entry.get("duration_months", 0) >= 24 for entry in career_history)
    else:
        avg_tenure = 0.0
        has_long_tenure = False
        
    if avg_tenure < 12.0:
        tenure_score = 0.3
    elif avg_tenure < 18.0:
        tenure_score = 0.6
    else:
        tenure_score = 1.0
        
    if has_long_tenure:
        tenure_score = min(1.0, tenure_score + 0.1)

    # 4. Career progression (15%)
    n_entries = len(career_history)
    if n_entries <= 1:
        progression_score = 0.6
    else:
        # Sort ascending by start_date
        sorted_history = sorted(career_history, key=lambda x: x.get("start_date") or "")
        half = n_entries // 2
        early_career = sorted_history[:half]
        late_career = sorted_history[half:]
        
        late_has_seniority = any(any(word in entry.get("title", "").lower() for word in SENIORITY_WORDS) for entry in late_career)
        early_has_seniority = any(any(word in entry.get("title", "").lower() for word in SENIORITY_WORDS) for entry in early_career)
        
        if late_has_seniority and not early_has_seniority:
            progression_score = 1.0
        elif not late_has_seniority and early_has_seniority:
            progression_score = 0.4
        else:
            progression_score = 0.6

    final = 0.35 * title_component + 0.30 * product_score + 0.20 * tenure_score + 0.15 * progression_score
    return round(final, 6)

# -----------------------------------------------------------------------------
# 3. Experience & Location Scorers (Task 6)
# -----------------------------------------------------------------------------
def score_experience(candidate: dict) -> float:
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0.0)
    
    # Base score by band
    if 5.0 <= yoe <= 9.0:
        base = 1.0
    elif (4.0 <= yoe < 5.0) or (9.0 < yoe <= 11.0):
        base = 0.8
    elif (3.0 <= yoe < 4.0) or (11.0 < yoe <= 14.0):
        base = 0.5
    else:
        base = 0.2
        
    # ML experience bonus
    ml_months = 0
    career_history = candidate.get("career_history", [])
    for entry in career_history:
        title = entry.get("title", "").lower()
        desc = entry.get("description", "").lower()
        if ML_EXP_PATTERN.search(title) or ML_EXP_PATTERN.search(desc):
            ml_months += entry.get("duration_months", 0)
            
    ml_years = ml_months / 12.0
    if ml_years >= 4.0:
        multiplier = 1.2
    elif ml_years >= 2.0:
        multiplier = 1.1
    else:
        multiplier = 1.0
        
    return min(1.0, base * multiplier)

def score_location(candidate: dict) -> float:
    profile = candidate.get("profile", {})
    country = profile.get("country", "").lower()
    location = profile.get("location", "").lower()
    
    signals = candidate.get("redrob_signals", {})
    relocate = signals.get("willing_to_relocate", False)
    
    if country != "india":
        if relocate:
            return 0.5
        else:
            return 0.1
            
    # country == india
    if any(city in location for city in PREFERRED_CITIES):
        return 1.0
    elif any(city in location for city in ACCEPTABLE_CITIES):
        return 0.85
    elif relocate:
        return 0.7
    else:
        return 0.4

# -----------------------------------------------------------------------------
# 4. Behavioral Signals Scorer (Task 7)
# -----------------------------------------------------------------------------
def score_behavioral(candidate: dict) -> float:
    signals = candidate.get("redrob_signals", {})
    
    # 1. Base activity score
    last_active_str = signals.get("last_active_date", "2026-06-07")
    try:
        parts = list(map(int, last_active_str.split('-')))
        last_active_date = date(parts[0], parts[1], parts[2])
    except (ValueError, IndexError):
        last_active_date = TODAY
        
    days_since = (TODAY - last_active_date).days
    
    if days_since < 30:
        base = 1.00
    elif days_since < 90:
        base = 0.75
    elif days_since < 180:
        base = 0.55
    else:
        base = 0.30

    # 2. Adjustments
    adj = 0.0
    
    if signals.get("open_to_work_flag") is True:
        adj += 0.05
        
    if signals.get("applications_submitted_30d", 0) > 2:
        adj += 0.03
        
    resp_rate = signals.get("recruiter_response_rate", 0.0)
    if resp_rate > 0.70:
        adj += 0.05
    elif resp_rate < 0.20:
        adj -= 0.10
        
    if signals.get("avg_response_time_hours", 999.0) < 12.0:
        adj += 0.02
        
    int_rate = signals.get("interview_completion_rate", 0.0)
    if int_rate >= 0.80:
        adj += 0.04
    elif int_rate < 0.40:
        adj -= 0.08
        
    notice = signals.get("notice_period_days", 999)
    if notice <= 30:
        adj += 0.04
    elif notice <= 60:
        adj += 0.00
    elif notice <= 90:
        adj -= 0.02
    else:
        adj -= 0.06
        
    if signals.get("verified_email") and signals.get("verified_phone"):
        adj += 0.03
        
    # GitHub Activity adjustment
    gh_score = signals.get("github_activity_score", -1.0)
    if gh_score > 50:
        adj += 0.02
    elif gh_score == -1:
        adj += 0.00
        
    # Assessment score adjustment
    assessment_scores = signals.get("skill_assessment_scores", {})
    if assessment_scores:
        avg_assessment = sum(assessment_scores.values()) / len(assessment_scores)
        if avg_assessment >= 70.0:
            adj += 0.04
        elif avg_assessment >= 50.0:
            adj += 0.02
        elif avg_assessment < 40.0:
            adj -= 0.03

    final = base + adj
    return max(0.30, min(1.0, final))

# -----------------------------------------------------------------------------
# 5. Education Scorer (Task 8)
# -----------------------------------------------------------------------------
def score_education(candidate: dict) -> float:
    education = candidate.get("education", [])
    if not education:
        return 0.35
        
    max_score = 0.0
    for entry in education:
        tier = entry.get("tier", "unknown")
        field = entry.get("field_of_study", "").lower()
        is_cs = any(f in field for f in CS_FIELDS)
        
        if tier == "tier_1":
            score = 1.0 if is_cs else 0.7
        elif tier == "tier_2":
            score = 0.85 if is_cs else 0.6
        elif tier == "tier_3":
            score = 0.65 if is_cs else 0.45
        else: # tier_4 or unknown
            score = 0.40
            
        if score > max_score:
            max_score = score
            
    return max_score
