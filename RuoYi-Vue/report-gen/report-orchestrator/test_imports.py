#!/usr/bin/env python3

try:
    import docx
    print('python-docx: OK')
except ImportError as e:
    print('python-docx: FAILED -', e)

try:
    import weasyprint
    print('weasyprint: OK')
except ImportError as e:
    print('weasyprint: FAILED -', e)

print('\nChecking pip list:')
import subprocess
result = subprocess.run(['pip', 'list'], capture_output=True, text=True)
lines = result.stdout.split('\n')
for line in lines:
    if 'docx' in line.lower() or 'weasy' in line.lower():
        print(line)