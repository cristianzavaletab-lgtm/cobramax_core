import os
import re

base = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
issues = []
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.html'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as fh:
                lines = fh.readlines()
            for i, line in enumerate(lines):
                if '<table' in line:
                    # look back up to 8 lines to find 'table-responsive'
                    start = max(0, i-8)
                    context = ''.join(lines[start:i])
                    if 'table-responsive' not in context:
                        issues.append((path, i+1, line.strip()))

if not issues:
    print('No se encontraron tablas sin wrapper .table-responsive')
else:
    print('Tablas sin wrapper detectadas:')
    for p, ln, txt in issues:
        print(f'{p}:{ln}: {txt}')
