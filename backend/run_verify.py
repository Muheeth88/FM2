import subprocess
import os

def run():
    target_log = "d:/Workspace/FM2/backend/verify_log.txt"
    if os.path.exists(target_log):
        os.remove(target_log)
    
    cmd = ["python", "d:/Workspace/FM2/backend/verify_phase3.py"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="d:/Workspace/FM2/backend", encoding='utf8')
    
    with open(target_log, "w", encoding='utf8') as f:
        f.write("--- STDOUT ---\n")
        f.write(result.stdout)
        f.write("\n--- STDERR ---\n")
        f.write(result.stderr)
    
    print(f"Log written to {target_log}")

if __name__ == "__main__":
    run()
