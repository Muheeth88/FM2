import subprocess
import os

try:
    output = subprocess.check_output(['python', 'backend/verify_step9.py'], stderr=subprocess.STDOUT)
    print(output.decode('utf-8'))
except subprocess.CalledProcessError as e:
    print(e.output.decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
