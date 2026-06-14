# scorer.py
"""
Composite candidate scoring logic.
"""

from honeypot import is_honeypot
from features import (score_core_skills, score_career_trajectory,
                      score_experience, score_location,
                      score_education, score_behavioral)

def score_candidate(candidate: dict) -> float:
    if is_honeypot(candidate):
        return 0.0
    
    s_skills   = score_core_skills(candidate)          # 0.35
    s_career   = score_career_trajectory(candidate)    # 0.30
    s_exp      = score_experience(candidate)           # 0.15
    s_loc      = score_location(candidate)             # 0.15
    s_edu      = score_education(candidate)            # 0.05
    
    jd_score = (0.35 * s_skills +
                0.30 * s_career +
                0.15 * s_exp   +
                0.15 * s_loc   +
                0.05 * s_edu)
    
    behavioral = score_behavioral(candidate)
    
    return round(jd_score * behavioral, 6)
