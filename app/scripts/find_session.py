import json
import os
import glob
import sys

# Change this to your production URL
BASE_URL = "https://exp-cqs.ixa.eus"
# Must match the OUTPUT_DIR defined in experiment_app/state.py
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.abspath(os.path.join(_SCRIPT_DIR, "..", "..", "output"))

def find_session(query):
    # Search for output directory in common locations
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_dirs = [
        os.path.join(script_dir, "..", "output"), # relative to app/scripts/
        "output",                                  # current directory
        "app/output"                               # relative to root
    ]
    
    output_dir = OUTPUT_DIR

    metadata_files = glob.glob(os.path.join(output_dir, "*_metadata.json"))
    
    results = []
    for meta_path in metadata_files:
        try:
            with open(meta_path, "r") as f:
                data = json.load(f)
            
            match = False
            if query == data.get("session_id"):
                match = True
            elif query == data.get("prolific_pid"):
                match = True
            elif query == data.get("prolific_session_id"):
                match = True
            
            if match:
                # Find progress from results file
                session_id = data.get("session_id")
                results_path = os.path.join(output_dir, f"{session_id}_results.jsonl")
                last_index = -1
                if os.path.exists(results_path):
                    with open(results_path, "r") as rf:
                        for line in rf:
                            if line.strip():
                                trial = json.loads(line)
                                idx = trial.get("argument_index")
                                if idx is not None and idx != -1:
                                    last_index = max(last_index, idx)
                
                progress = last_index + 1

                
                results.append({
                    "session_id": session_id,
                    "prolific_pid": data.get("prolific_pid"),
                    "start_time": data.get("start_time"),
                    "progress": progress,
                    "experimental_group": data.get("experimental_group")
                })
        except Exception as e:
            print(f"Error reading {meta_path}: {e}")
            
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/find_session.py <prolific_pid_or_session_id>")
        sys.exit(1)
        
    query = sys.argv[1]
    sessions = find_session(query)
    
    if not sessions:
        print(f"No sessions found for query: {query}")
    else:
        print(f"Found {len(sessions)} session(s):")
        for s in sessions:
            print("-" * 40)
            print(f"Session ID: {s['session_id']}")
            print(f"Prolific PID: {s['prolific_pid']}")
            print(f"Group: {s['experimental_group']}")
            print(f"Progress: {s['progress']} arguments completed")
            print(f"Start Time: {s['start_time']}")
            print(f"Recovery URL: {BASE_URL}?recovery_id={s['session_id']}")
