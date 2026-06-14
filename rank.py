# rank.py
"""
Main entry point for candidate ranker.
"""

import argparse
import csv
import gzip
import json
import sys
import time
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

def load_candidates(path: str):
    is_gz = path.endswith('.gz')
    count = 0
    if is_gz:
        f = gzip.open(path, 'rt', encoding='utf-8')
    else:
        f = open(path, 'r', encoding='utf-8')
        
    try:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                candidate = json.loads(line)
                yield candidate
                count += 1
            except json.JSONDecodeError as e:
                print(f"Warning: malformed JSON on line {line_num} skipped: {e}", file=sys.stderr)
    finally:
        f.close()
    print(f"Total candidates loaded: {count}")

class HeapElement:
    def __init__(self, score, candidate_id, candidate_data):
        self.score = score
        self.candidate_id = candidate_id
        self.candidate_data = candidate_data

    def __lt__(self, other):
        # In a min-heap, heapq.heappop will pop the 'smallest' element.
        # We want to pop the 'worst' candidate, so 'worst' must be '<' (less than) 'better'.
        # A candidate with a lower score is worse.
        if self.score != other.score:
            return self.score < other.score
        # If scores are equal, a lexicographically larger candidate_id is worse.
        return self.candidate_id > other.candidate_id

def chunk_generator(candidates_gen, chunk_size=1000):
    chunk = []
    for c in candidates_gen:
        chunk.append(c)
        if len(chunk) == chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

def score_chunk(chunk):
    # Import inside worker for pickling/multiprocessing compatibility in Windows
    from scorer import score_candidate
    return [(c, score_candidate(c)) for c in chunk]

def score_all_parallel(candidates_generator):
    import heapq
    processes = max(1, cpu_count() - 1)
    chunks = chunk_generator(candidates_generator, chunk_size=1000)
    
    heap = []
    all_scores = []
    total_candidates = 0
    honeypot_count = 0
    
    # Estimate total chunks = 100 for the progress bar
    with Pool(processes=processes) as pool:
        for chunk_result in tqdm(
            pool.imap(score_chunk, chunks),
            total=100,
            desc="Scoring (parallel)",
            unit="chunk"
        ):
            for candidate, score in chunk_result:
                total_candidates += 1
                all_scores.append(score)
                if score == 0.0:
                    honeypot_count += 1
                
                element = HeapElement(score, candidate["candidate_id"], candidate)
                if len(heap) < 100:
                    heapq.heappush(heap, element)
                else:
                    if heap[0] < element:
                        heapq.heappushpop(heap, element)
                        
    # Sort the heap descending (best first)
    top100_elements = sorted(heap, reverse=True)
    top100 = [(el.candidate_data, el.score) for el in top100_elements]
    
    return top100, all_scores, total_candidates, honeypot_count

def main():
    import os
    import subprocess
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="./candidates.jsonl")
    parser.add_argument("--out", default="./submission.csv")
    args = parser.parse_args()
    
    start = time.time()
    
    print(f"Scoring candidates from {args.candidates} in stream mode...")
    
    # We will score in parallel and stream
    candidates_gen = load_candidates(args.candidates)
    top100, all_scores, total_candidates, honeypot_count = score_all_parallel(candidates_gen)
    
    print(f"Scored {total_candidates} candidates in {time.time()-start:.1f}s")
    
    # Write CSV
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])
        for rank, (candidate, score) in enumerate(top100, start=1):
            from reasoning import generate_reasoning
            reason = generate_reasoning(candidate, score, rank)
            writer.writerow([candidate["candidate_id"], rank,
                             f"{score:.6f}", reason])
    
    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s")
    print(f"Honeypots detected: {honeypot_count}")
    print(f"Output written to: {args.out}")
    print("\nTop 10:")
    for rank, (c, s) in enumerate(top100[:10], start=1):
        print(f"  {rank}. {c['candidate_id']} | {s:.4f} | "
              f"{c['profile']['current_title']} | "
              f"{c['profile']['years_of_experience']}yrs | "
              f"{c['profile']['location']}")
              
    # Run automatic self-validation
    print("\nRunning check.py automatically for self-validation...")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        check_script = os.path.join(script_dir, "check.py")
        result = subprocess.run(
            [sys.executable, check_script, "--submission", args.out, "--candidates", args.candidates],
            capture_output=True,
            text=True
        )
        print("Self-Validation Results:")
        print(result.stdout.strip())
        if result.stderr:
            print("Validation Errors/Logs:")
            print(result.stderr.strip())
    except Exception as e:
        print(f"Failed to automatically run check.py for self-validation: {e}")

if __name__ == "__main__":
    main()
