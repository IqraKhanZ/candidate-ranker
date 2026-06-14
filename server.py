# server.py
"""
Flask API server for Redrob Candidate Discoverer.
Serves the React frontend and handles JSON / Multipart scoring requests.
"""

import json
import os
import sys
import time
import tempfile
import urllib.request
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

# Allow uploads up to 500MB (for candidate datasets)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024
PORT = int(os.environ.get('PORT', 5000))

@app.route('/')
def index():
    # Serve index.html from same directory
    return send_from_directory('.', 'index.html')

@app.route('/api/rank', methods=['POST'])
def api_rank():
    temp_file_path = None
    try:
        # Determine if content is JSON or multipart/form-data
        if request.is_json:
            data = request.json
            job_description = data.get('job_description', '')
            source_type = data.get('source_type', 'local')
            dataset_path = data.get('dataset_path', '')
            dataset_url = data.get('dataset_url', '')
            file_to_process = None
        else:
            job_description = request.form.get('job_description', '')
            source_type = request.form.get('source_type', 'local')
            dataset_path = request.form.get('dataset_path', '')
            dataset_url = request.form.get('dataset_url', '')
            file_to_process = request.files.get('file')

        # 1. Handle Candidate Dataset Source
        if source_type == 'upload':
            if not file_to_process or not file_to_process.filename:
                return jsonify({"error": "No file selected for upload."}), 400
            
            # Save uploaded file to a temporary file
            suffix = '.jsonl.gz' if file_to_process.filename.endswith('.gz') else '.jsonl'
            fd, temp_file_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            file_to_process.save(temp_file_path)
            candidate_file = temp_file_path
            print(f"Uploaded file saved temporarily at: {candidate_file}")
            
        elif source_type == 'url':
            if not dataset_url:
                return jsonify({"error": "No dataset URL provided."}), 400
            
            # Download file from URL to a temporary file
            suffix = '.jsonl.gz' if dataset_url.split('?')[0].endswith('.gz') else '.jsonl'
            fd, temp_file_path = tempfile.mkstemp(suffix=suffix)
            os.close(fd)
            
            print(f"Downloading dataset from: {dataset_url}")
            try:
                req = urllib.request.Request(
                    dataset_url, 
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                )
                with urllib.request.urlopen(req) as response:
                    with open(temp_file_path, 'wb') as out_file:
                        chunk_size = 1024 * 1024  # 1MB chunks
                        while True:
                            chunk = response.read(chunk_size)
                            if not chunk:
                                break
                            out_file.write(chunk)
                candidate_file = temp_file_path
                print(f"URL dataset downloaded successfully to: {candidate_file}")
            except Exception as e:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                return jsonify({"error": f"Failed to download dataset from URL: {str(e)}"}), 400
                
        else: # local path
            if not dataset_path:
                return jsonify({"error": "No local dataset file path provided."}), 400
            
            candidate_file = dataset_path
            if not os.path.isabs(candidate_file):
                # Try relative to parent directory of server.py (Candidate Ranker root)
                parent_dir = os.path.dirname(os.path.dirname(__file__))
                candidate_file = os.path.abspath(os.path.join(parent_dir, dataset_path))
                if not os.path.exists(candidate_file):
                    candidate_file = os.path.abspath(dataset_path)

            if not os.path.exists(candidate_file):
                return jsonify({"error": f"Candidate database file not found at: '{dataset_path}'"}), 400

        # 2. Run the scoring loop
        start_time = time.time()
        
        # Import ranker core modules
        from rank import load_candidates, score_all_parallel
        candidates_gen = load_candidates(candidate_file)
        
        # Perform scoring in parallel (streaming mode)
        top100, all_scores, total_candidates, honeypots = score_all_parallel(candidates_gen)
        
        # Clean up downloaded/uploaded temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Temporary file cleaned up: {temp_file_path}")
            except Exception as e:
                print(f"Error removing temp file {temp_file_path}: {e}")
                
        # Generate JSON response candidate list
        output_candidates = []
        from reasoning import generate_reasoning
        for rank_idx, (c, score) in enumerate(top100, start=1):
            reason = generate_reasoning(c, score, rank_idx)
            output_candidates.append({
                "rank": rank_idx,
                "candidate_id": c.get("candidate_id"),
                "score": score,
                "current_title": c.get("profile", {}).get("current_title", ""),
                "years_of_experience": c.get("profile", {}).get("years_of_experience", 0.0),
                "location": c.get("profile", {}).get("location", ""),
                "reasoning": reason,
                "skills": c.get("skills", []),
                "career_history": c.get("career_history", []),
                "education": c.get("education", []),
                "redrob_signals": c.get("redrob_signals", {}),
                "profile": c.get("profile", {})
            })
            
        # Calculate score distribution stats
        sorted_scores = sorted(all_scores)
        
        def get_percentile(sorted_list, pct):
            if not sorted_list:
                return 0.0
            idx = (len(sorted_list) - 1) * pct
            low = int(idx)
            high = low + 1
            if high < len(sorted_list):
                return sorted_list[low] + (sorted_list[high] - sorted_list[low]) * (idx - low)
            return sorted_list[low]
            
        elapsed_time = round(time.time() - start_time, 1)
        print(f"Ranking complete. Scored {total_candidates} records in {elapsed_time}s.")
        
        response_body = {
            "candidates": output_candidates,
            "metrics": {
                "total_candidates": total_candidates,
                "honeypots": honeypots,
                "elapsed_time": elapsed_time,
                "distribution": {
                    "min": sorted_scores[0] if sorted_scores else 0.0,
                    "p25": get_percentile(sorted_scores, 0.25),
                    "median": get_percentile(sorted_scores, 0.50),
                    "p75": get_percentile(sorted_scores, 0.75),
                    "max": sorted_scores[-1] if sorted_scores else 0.0
                }
            }
        }
        return jsonify(response_body)

    except Exception as e:
        # Clean up temp file in case of error
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except:
                pass
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server-side error: {str(e)}"}), 500

if __name__ == '__main__':
    print(f"\n==================================================")
    print(f"Redrob Discoverer Server running locally at:")
    print(f"  --> http://localhost:{PORT}/")
    print(f"Press Ctrl+C to terminate.")
    print(f"==================================================\n")
    app.run(host='0.0.0.0', port=PORT)
