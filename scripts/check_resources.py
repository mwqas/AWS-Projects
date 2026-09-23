"""Check syntax and authored Markdown links without importing AWS packages."""
import ast
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
errors = []
python_count = 0
link_count = 0
for path in ROOT.rglob('*.py'):
    if '.git' in path.parts or '.venv' in path.parts:
        continue
    try:
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        python_count += 1
    except (SyntaxError, UnicodeError) as exc:
        errors.append(f'{path.relative_to(ROOT)}: {exc}')

for path in ROOT.rglob('*.md'):
    if any(part in path.parts for part in ('.git', '.venv', 'reference')):
        continue  # Upstream README links belong to its original repository.
    text = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
    for target in re.findall(r'\]\(([^)]+)\)', text):
        target = target.split('#')[0].split(' "')[0].strip('<>')
        if not target or re.match(r'\w+://|mailto:', target):
            continue
        link_count += 1
        if not (path.parent / unquote(target)).exists():
            errors.append(f'{path.relative_to(ROOT)}: missing link {target}')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {python_count} Python files parse; {link_count} local documentation links exist.')
