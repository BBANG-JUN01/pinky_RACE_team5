"""모든 오프라인 모듈 데모, Python 구문, 패키지 XML을 검사한다."""
from pathlib import Path
import ast, importlib, json, sys, xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
for package in (root/'src').glob('pinky_gp_*'): sys.path.insert(0,str(package))
count=0
for p in sorted((root/'src').glob('pinky_gp_*/pinky_gp_*/*.py')):
    tree=ast.parse(p.read_text())
    if not any(isinstance(n,ast.FunctionDef) and n.name=='demo' for n in tree.body):continue
    m=importlib.import_module(f'{p.parent.name}.{p.stem}')
    json.dumps(m.demo(),allow_nan=False)
    print(f'PASS {p.parent.name}.{p.stem}')
    count+=1
for p in root.rglob('*.py'):
    if '__pycache__' not in p.parts:ast.parse(p.read_text())
for p in (root/'src').glob('*/package.xml'):ET.parse(p)
print(f'{count} demos passed; Python AST and package XML parsed.')
