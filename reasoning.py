# reasoning.py
"""
Reasoning generator for Candidate Ranker.
Creates unique, data-backed 1-2 sentence summaries for top-100 candidates.
Reference date: 2026-06-07
"""

from datetime import date

MUST_HAVE = {
    "embedding", "embeddings", "retrieval", "vector", "search", "ranking",
    "sentence-transformers", "pinecone", "weaviate", "qdrant", "milvus",
    "opensearch", "elasticsearch", "faiss", "python", "ndcg", "mrr", "map",
    "a/b test", "evaluation", "transformer", "neural", "lora", "qlora",
    "xgboost", "fine-tuning", "model", "inference", "nlp", "transformers",
    "bert", "rag"
}

SERVICES_COMPANIES = [
    "tcs", "tata consultancy", "wipro", "infosys", "accenture",
    "cognizant", "capgemini", "hcl", "tech mahindra", "mphasis",
    "hexaware", "mindtree", "l&t infotech", "ltimindtree"
]

def generate_reasoning(candidate: dict, score: float, rank: int) -> str:
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career_history = candidate.get("career_history", [])
    
    current_title = profile.get("current_title", "AI/ML Engineer")
    current_company = profile.get("current_company", "").strip()
    yoe = profile.get("years_of_experience", 0.0)
    location = profile.get("location", "India")
    
    # 1. Extract 1-2 key skills
    skills = candidate.get("skills", [])
    relevant_skills = []
    for s in skills:
        name = s.get("name", "")
        if name:
            name_lower = name.lower()
            if any(kw in name_lower for kw in MUST_HAVE):
                relevant_skills.append(name)
                
    if len(relevant_skills) < 2:
        for s in skills:
            name = s.get("name")
            if name and name not in relevant_skills:
                relevant_skills.append(name)
                
    top_skills = [s for s in relevant_skills if s][:2]
    skills_str = " and ".join(top_skills) if top_skills else "ML engineering systems"

    # 2. Extract company history type
    is_services = False
    has_product = False
    for entry in career_history:
        comp = entry.get("company", "").lower()
        if any(sc in comp for sc in SERVICES_COMPANIES):
            is_services = True
        else:
            has_product = True
            
    company_context = "product development" if (has_product and not is_services) else "services background"
    if has_product and is_services:
        company_context = "mixed product and services background"

    # 3. Calculate active days
    last_active_str = signals.get("last_active_date", "2026-06-07")
    try:
        parts = list(map(int, last_active_str.split('-')))
        last_active = date(parts[0], parts[1], parts[2])
    except:
        last_active = date(2026, 6, 7)
    days_since = (date(2026, 6, 7) - last_active).days

    notice = signals.get("notice_period_days", 0)
    if notice is None or notice == 999:
        notice = 30

    # 4. Formulate concerns and missing elements
    pref_cities = ["pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon", "gurugram", "new delhi"]
    loc_lower = location.lower()
    is_in_pref_city = any(city in loc_lower for city in pref_cities)
    
    if not is_in_pref_city:
        concern = f"location in {location} requires alignment"
    elif notice > 60:
        concern = f"notice period is high at {notice} days"
    elif yoe < 5.0:
        concern = f"years of experience is slightly below target ({yoe} yrs)"
    else:
        concern = "behavioral engagement profile is moderate"

    if not top_skills:
        missing = "lacks direct search/retrieval domain skills"
    elif is_services and not has_product:
        missing = "lacks product development background"
    else:
        missing = "lacks senior-level production deployment track record"

    # Deterministic variety based on rank
    rot = rank % 3
    
    if 1 <= rank <= 20:
        # Strong match: highlights strengths and positive logistics
        if current_company:
            comp_phrase = f"currently at {current_company}"
        else:
            comp_phrase = f"with a strong {company_context} tenure"
            
        if rot == 0:
            reason = (
                f"Excellent fit: {current_title} with {yoe} YoE, showing proven expertise in {skills_phrase if 'skills_phrase' in locals() else skills_str}. "
                f"They are {comp_phrase}, active recently ({days_since}d ago), and have a short {notice}-day notice."
            )
        elif rot == 1:
            reason = (
                f"Top pick: Highly qualified {current_title} ({yoe} YoE) with a background in {company_context}. "
                f"They offer deep technical proficiency in {skills_str} and are active on the platform with {notice} days notice."
            )
        else:
            reason = (
                f"Strongly recommended: A senior {current_title} presenting {yoe} years of experience and specialization in {skills_str}. "
                f"They are based in {location} and show strong platform engagement ({days_since} days since active)."
            )
            
    elif 21 <= rank <= 70:
        # Balanced match: mentions strengths and a soft concern
        if rot == 0:
            reason = (
                f"Qualified {current_title} with {yoe} YoE and solid technical depth in {skills_str}. "
                f"Included in the shortlist despite concern regarding {concern} due to strong JD skill match."
            )
        elif rot == 1:
            reason = (
                f"Solid profile: {current_title} ({yoe} YoE) exhibiting relevant experience in {skills_str} within a {company_context}. "
                f"Retained as a good match, though there is a minor concern about {concern}."
            )
        else:
            reason = (
                f"Good match: {current_title} offering {yoe} years of experience and skills in {skills_str}. "
                f"Included in the active pool despite the fact that {concern}."
            )
            
    else: # 71 <= rank <= 100
        # Borderline match: honest about gaps and reasons for inclusion as filler
        if rot == 0:
            reason = (
                f"Borderline pick: {current_title} with {yoe} YoE showing relevant {skills_str} skills. "
                f"Retained for technical depth despite concerns regarding {concern} and the fact that the candidate {missing}."
            )
        elif rot == 1:
            reason = (
                f"Qualified with reservations: {current_title} ({yoe} YoE) offering technical background in {skills_str}. "
                f"Included as a final shortlist filler despite being borderline due to {concern} while they {missing}."
            )
        else:
            reason = (
                f"Borderline candidate: {current_title} with {yoe} years of experience and {company_context} background. "
                f"Retained for baseline technical overlap in {skills_str} despite concerns that they {missing}."
            )

    # Ensure no double spacing or formatting glitches
    reason = " ".join(reason.split()).replace("..", ".").strip()
    return reason
