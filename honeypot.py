# honeypot.py
"""
Honeypot detection logic for Redrob Candidate Ranker.
Reference date: 2026-06-07
"""

def is_honeypot(candidate: dict) -> bool:
    # 1. Timeline impossibility
    profile = candidate.get("profile", {})
    yoe = profile.get("years_of_experience", 0.0)
    
    # estimated_birth_year = current_year - years_of_experience - 22
    # Reference current_year = 2026
    estimated_birth_year = 2026 - yoe - 22
    
    career_history = candidate.get("career_history", [])
    for entry in career_history:
        start_date = entry.get("start_date")
        if start_date:
            try:
                start_year = int(start_date.split('-')[0])
                if start_year < estimated_birth_year + 16:
                    return True
            except (ValueError, IndexError):
                pass

    # 2. Skills contradiction
    skills = candidate.get("skills", [])
    contradictory_skills_count = 0
    for skill in skills:
        prof = skill.get("proficiency")
        dur = skill.get("duration_months")
        if prof == "expert" and dur == 0:
            contradictory_skills_count += 1
            if contradictory_skills_count >= 3:
                return True

    # 3. Experience contradiction
    total_months = 0
    for entry in career_history:
        total_months += entry.get("duration_months", 0)
    total_career_years = total_months / 12.0
    if total_career_years < yoe * 0.5:
        return True

    # 4. Completeness contradiction
    signals = candidate.get("redrob_signals", {})
    completeness = signals.get("profile_completeness_score", 0.0)
    summary = profile.get("summary", "")
    
    if completeness == 100.0:
        if not summary or not summary.strip() or len(career_history) == 0:
            return True

    return False
