# check.py
"""
Sanity check script for Redrob Candidate Ranker submission.
Usage: python check.py --submission submission.csv --candidates candidates.jsonl
"""

import argparse
import csv
import gzip
import json
import os
import sys
from datetime import date

# Import constant lists to avoid duplicating
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

TODAY = date(2026, 6, 7)

def load_submission(csv_path):
    sub_data = []
    if not os.path.exists(csv_path):
        print(f"Error: Submission file {csv_path} does not exist.")
        sys.exit(1)
        
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            print("Error: Submission CSV is empty.")
            sys.exit(1)
            
        for row in reader:
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) < 3:
                continue
            cid = row[0].strip()
            rank = int(row[1].strip())
            score = float(row[2].strip())
            sub_data.append((cid, rank, score))
            
    return sub_data

def scan_candidates(candidates_path, candidate_ids_set):
    records = {}
    is_gz = candidates_path.endswith('.gz')
    if is_gz:
        f = gzip.open(candidates_path, 'rt', encoding='utf-8')
    else:
        f = open(candidates_path, 'r', encoding='utf-8')
        
    try:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
                cid = candidate.get("candidate_id")
                if cid in candidate_ids_set:
                    records[cid] = candidate
                    if len(records) == len(candidate_ids_set):
                        break  # Found all 100
            except json.JSONDecodeError:
                pass
    finally:
        f.close()
        
    return records

def get_percentile(sorted_list, pct):
    if not sorted_list:
        return 0.0
    idx = (len(sorted_list) - 1) * pct
    low = int(idx)
    high = low + 1
    if high < len(sorted_list):
        return sorted_list[low] + (sorted_list[high] - sorted_list[low]) * (idx - low)
    return sorted_list[low]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission", default="./submission.csv")
    parser.add_argument("--candidates", default="./candidates.jsonl")
    args = parser.parse_args()
    
    # 1. Load submission ids and ranks
    sub_data = load_submission(args.submission)
    if len(sub_data) != 100:
        print(f"Warning: Expected exactly 100 submission rows, found {len(sub_data)}")
        
    candidate_ids = [row[0] for row in sub_data]
    candidate_ids_set = set(candidate_ids)
    
    # 2. Find and load candidates details
    print(f"Scanning candidate file {args.candidates} for the {len(candidate_ids_set)} IDs...")
    records = scan_candidates(args.candidates, candidate_ids_set)
    print(f"Successfully matched and loaded {len(records)} candidate records.")
    
    # 3. Print Table and check conditions
    print("\n" + "="*120)
    header_format = "{:<5} | {:<12} | {:<8} | {:<30} | {:<5} | {:<20} | {:<12} | {:<12}"
    row_format = "{:<5} | {:<12} | {:<8.6f} | {:<30} | {:<5.1f} | {:<20} | {:<12} | {:<12}"
    print(header_format.format("Rank", "Candidate ID", "Score", "Current Title", "YoE", "Location", "Last Active", "Open to Work"))
    print("-"*120)
    
    warnings = []
    scores = []
    
    for cid, rank, score in sorted(sub_data, key=lambda x: x[1]):
        scores.append(score)
        c = records.get(cid)
        if not c:
            print(header_format.format(rank, cid, score, "NOT FOUND IN JSONL", 0, "", "", ""))
            warnings.append(f"Candidate {cid} at Rank {rank} was not found in candidate source file.")
            continue
            
        profile = c.get("profile", {})
        signals = c.get("redrob_signals", {})
        
        title = profile.get("current_title", "")
        yoe = profile.get("years_of_experience", 0.0)
        loc = profile.get("location", "")
        active = signals.get("last_active_date", "")
        open_work = signals.get("open_to_work_flag", False)
        
        print(row_format.format(
            rank, cid, score, 
            title[:30], yoe, loc[:20], active, str(open_work)
        ))
        
        # Check warnings
        # 1. Any candidate in top 20 whose current_title matches LOW_TITLES list
        if rank <= 20:
            if any(low in title.lower() for low in LOW_TITLES):
                warnings.append(f"[Warning 1] Rank {rank}: Candidate {cid} has a LOW_VALUE title: '{title}'")
                
        # 2. Any candidate in top 20 with years_of_experience < 3
        if rank <= 20:
            if yoe < 3.0:
                warnings.append(f"[Warning 2] Rank {rank}: Candidate {cid} has YoE < 3 ({yoe} years)")
                
        # 3. Any candidate in top 10 whose entire career history is at SERVICES_COMPANIES (services_ratio >= 0.9)
        if rank <= 10:
            career_history = c.get("career_history", [])
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
                warnings.append(f"[Warning 3] Rank {rank}: Candidate {cid} has services_ratio = {services_ratio:.2f} (entire career at services companies)")
                
        # 4. Any candidate in top 10 where days since last_active_date > 90
        if rank <= 10:
            try:
                parts = list(map(int, active.split('-')))
                last_active_date = date(parts[0], parts[1], parts[2])
                days_since = (TODAY - last_active_date).days
                if days_since > 90:
                    warnings.append(f"[Warning 4] Rank {rank}: Candidate {cid} last active {days_since} days ago ({active})")
            except Exception as e:
                warnings.append(f"[Warning 4] Rank {rank}: Candidate {cid} active date parse error '{active}': {e}")
                
        # 5. Any candidate in top 10 where open_to_work_flag == False
        if rank <= 10:
            if not open_work:
                warnings.append(f"[Warning 5] Rank {rank}: Candidate {cid} has open_to_work_flag == False")
                
    print("="*120)
    
    # 4. Print Score Distribution
    sorted_scores = sorted(scores)
    s_min = sorted_scores[0] if sorted_scores else 0.0
    s_max = sorted_scores[-1] if sorted_scores else 0.0
    s_p25 = get_percentile(sorted_scores, 0.25)
    s_median = get_percentile(sorted_scores, 0.50)
    s_p75 = get_percentile(sorted_scores, 0.75)
    
    print("\nScore Distribution (Top 100):")
    print(f"  Min:    {s_min:.6f}")
    print(f"  P25:    {s_p25:.6f}")
    print(f"  Median: {s_median:.6f}")
    print(f"  P75:    {s_p75:.6f}")
    print(f"  Max:    {s_max:.6f}")
    
    # 5. Print Warnings
    print("\nSanity Check Warnings:")
    if warnings:
        for w in warnings:
            print(f"  \033[93m{w}\033[0m")
        print(f"\nTotal warnings: {len(warnings)}")
    else:
        print("  \033[92mAll checks passed! No warnings detected.\033[0m")

if __name__ == "__main__":
    main()
