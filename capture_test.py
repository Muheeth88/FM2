import subprocess
import os

try:
    output = subprocess.check_output(['python', 'backend/verify_step9.py'], stderr=subprocess.STDOUT)
    with open('test_summary_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(output.decode('utf-8'))
except subprocess.CalledProcessError as e:
    with open('test_summary_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(e.output.decode('utf-8'))
except Exception as e:
    with open('test_summary_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(str(e))
