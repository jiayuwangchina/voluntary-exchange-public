#!/usr/bin/env python3
"""Build two self-contained anonymous manuscripts and refresh plain cross-references.

The official class excludes xr/xr-hyper. The %<xref:key> comments identify
external reference numbers that this script refreshes from the other PDF's
own LaTeX labels. No external-reference package is used or needed by TeX.
"""
from pathlib import Path
import hashlib,json,re,subprocess,shutil,tempfile,os

DEST=Path(__file__).resolve().parent
STAGE=tempfile.TemporaryDirectory(prefix='econometrica-build-')
ROOT=Path(STAGE.name)
NAMES=['Paper_1_Main_Manuscript','Paper_1_Online_Appendix']
PDF_NAMES=['Anonymous_Main_Manuscript.pdf','Anonymous_Online_Appendix.pdf']
for filename in [n+'.tex' for n in NAMES]+['econsocart.cls','econsocart.cfg','econsoc.bst']:
    shutil.copy2(DEST/filename,ROOT/filename)

def run(name):
    r=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],
                     cwd=ROOT,text=True,capture_output=True)
    if r.returncode:
        print(r.stdout[-6000:]);raise SystemExit(r.returncode)

def labels(name):
    text=(ROOT/(name+'.aux')).read_text()
    own=set(re.findall(r'\\label\{([^}]+)\}',(ROOT/(name+'.tex')).read_text()))
    pairs=re.findall(r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}',text)
    return {k:v for k,v in pairs if k in own}

def refresh(name, other):
    path=ROOT/(name+'.tex');src=path.read_text()
    def plain(m):
        key=m.group(2)
        if key not in other:raise ValueError('Unresolved external reference: '+key)
        return other[key]+'%<xref:'+key+'>\n'
    def equation(m):
        key=m.group(2)
        if key not in other:raise ValueError('Unresolved external equation: '+key)
        return r'\textup{('+other[key]+')}%<xeqref:'+key+'>\n'
    new=re.sub(r'([A-Za-z0-9.]+)%<xref:([^>]+)>\n',plain,src)
    new=re.sub(r'\\textup\{\(([^)]+)\)\}%<xeqref:([^>]+)>\n',equation,new)
    if new!=src:path.write_text(new)
    return new!=src

previous=None
for iteration in range(6):
    for name in NAMES:run(name)
    maps={name:labels(name) for name in NAMES}
    changed=False
    for i,name in enumerate(NAMES):
        changed=refresh(name,maps[NAMES[1-i]]) or changed
    if iteration>=2 and not changed and maps==previous:break
    previous=maps
else:raise RuntimeError('Labels failed to stabilize.')

report={'passes':iteration+1,'documents':{},'class_mode':'official econsocart draft',
        'external_references':'plain text, refreshed by build.py',
        'author_information':'omitted by request'}
for name in NAMES:
    src=(ROOT/(name+'.tex')).read_text();log=(ROOT/(name+'.log')).read_text()
    for token in ['undefined references','undefined citations','multiply defined',
                  'Overfull','LaTeX Error','Fatal error']:
        assert token not in log,(name,token)
    own=set(re.findall(r'\\label\{([^}]+)\}',src))
    assert set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',src))<=own
    assert not re.search(r'\\(?:author|address|ead|affiliation)\s*[\[{]',src)
    assert 'xr-hyper' not in src
    info=subprocess.check_output(['pdfinfo',str(ROOT/(name+'.pdf'))],text=True)
    pages=int(re.search(r'^Pages:\s*(\d+)',info,re.M).group(1))
    assert not re.search(r'^Author:[ \t]*\S',info,re.M)
    warnings=[line.strip() for line in log.splitlines() if 'Warning:' in line]
    report['documents'][name]={'pages':pages,'labels':len(own),
        'external_refs':len(re.findall(r'%<x(?:eq)?ref:',src)),
        'warnings':warnings,
        'source_sha256':hashlib.sha256(src.encode()).hexdigest()}
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
                  (ROOT/(NAMES[0]+'.tex')).read_text(),re.S).group(1)
report['abstract_words']=len(abstract.split())
assert report['abstract_words']<=100
assert report['documents'][NAMES[0]]['pages']<=45
for name,pdfname in zip(NAMES,PDF_NAMES):
    new_source=(ROOT/(name+'.tex')).read_bytes()
    if new_source!=(DEST/(name+'.tex')).read_bytes():
        (DEST/(name+'.tex')).write_bytes(new_source)
    # Publish a complete PDF atomically, separately from automatic TeX previews.
    temporary=DEST/(pdfname+'.part')
    temporary.write_bytes((ROOT/(name+'.pdf')).read_bytes())
    os.replace(temporary,DEST/pdfname)
    report['documents'][name]['pdf']=pdfname
(DEST/'compilation_report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
STAGE.cleanup()
