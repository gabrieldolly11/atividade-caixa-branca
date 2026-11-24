#!/usr/bin/env python3
"""Compila separadamente e executa em diretórios temporários isolados; Python 3 + JDK 17+."""
import csv, json, subprocess, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BASE = 'A;10\nB;0\n'
# id, método, caminho legado, CSV inicial, log inicial, comandos, saída esperada, CSV final, log final
cases = [
 ('T01','Q','Q2',BASE,None,['Q:A'],['Q=10'],BASE,None),
 ('T02','Q','Q3',BASE,None,['Q:B'],['Q=0'],BASE,None),
 ('T03','Q','Q3','B;0\n',None,['Q:A'],['EX=NoSuchElementException'],'B;0\n',None),
 ('T04','Q','Q1','',None,['Q:A'],['EX=NoSuchElementException'],'',None),
 ('T05','Q','Q4',None,None,['Q:A'],['EX=UncheckedIOException'],None,None),
 ('T06','Q','Q6',';\n',None,['Q:A'],['EX=UncheckedIOException'],';\n',None),
 ('T07','Q','Q7','A\n',None,['Q:A'],['EX=UncheckedIOException'],'A\n',None),
 ('T08','Q','Q7','A;abc\n',None,['Q:A'],['EX=UncheckedIOException'],'A;abc\n',None),
 ('T09','Q','Q2','A;10\nA;5\n',None,['Q:A'],['EX=UncheckedIOException'],'A;10\nA;5\n',None),
 ('T10','Q','Q2','A;-1\n',None,['Q:A'],['EX=UncheckedIOException'],'A;-1\n',None),
 ('T11','Q','Q3',BASE,None,['Q:<null>'],['EX=IllegalArgumentException'],BASE,None),
 ('T12','R','R1 + Q2',BASE,None,['R:A:5','U','Q:A'],['R=true','U=A','Q=5'],'A;5\nB;0\n','A;5\n'),
 ('T13','R','R1 + Q2',BASE,None,['R:A:10','Q:A'],['R=true','Q=0'],'A;0\nB;0\n','A;10\n'),
 ('T14','R','R2 + Q2',BASE,None,['R:A:11','U'],['R=false','U='],BASE,None),
 ('T15','R','R1 + Q2',BASE,None,['R:A:0','U'],['EX=IllegalArgumentException','U='],BASE,None),
 ('T16','R','R1 + Q2',BASE,None,['R:A:-5','U'],['EX=IllegalArgumentException','U='],BASE,None),
 ('T17','R','R1 + Q2',BASE,None,['R:A:8','R:A:8','Q:A'],['R=true','R=false','Q=2'],'A;2\nB;0\n','A;8\n'),
 ('T18','R','R3 + Q2',BASE,'<DIR>',['R:A:1','U'],['EX=UncheckedIOException','U='],BASE,'<DIR>'),
 ('T19','R','R5 + Q7','A;x\n',None,['R:A:1'],['EX=UncheckedIOException'],'A;x\n',None),
 ('T20','R','R2 + Q3',BASE,None,['R:Z:1'],['R=false'],BASE,None),
 ('T21','R','R1 + Q3',BASE,None,['R:Z:0'],['EX=IllegalArgumentException'],BASE,None),
 ('T22','R','R2 + Q4',None,None,['R:A:1'],['EX=UncheckedIOException'],None,None),
 ('T23','R','R1 + Q2',BASE,'B;2\n',['R:A:1','R:A:2','U','Q:A'],['R=true','R=true','U=A','Q=7'],'A;7\nB;0\n','B;2\nA;1\nA;2\n'),
 ('T24','R','R1 + Q2','BAD:CODE;10\n',None,['R:BAD;CODE:1'],['EX=IllegalArgumentException'],'BAD:CODE;10\n',None),
 ('T25','Q','Q2','A;10;extra\n',None,['Q:A'],['EX=UncheckedIOException'],'A;10;extra\n',None),
]
# T02 passa pelo laço com não coincidência e depois coincidência; T24 isola código inválido com quantidade positiva.
cases[1] = (*cases[1][:2], 'Q3 + Q2', *cases[1][3:])
cases[23] = (*cases[23][:2], 'R2 + Q3', *cases[23][3:])
def setup(p, value):
    if value == '<DIR>': p.mkdir()
    elif value is not None: p.write_text(value, encoding='utf-8')
def state(p):
    if p.is_dir(): return '<DIR>'
    return p.read_text(encoding='utf-8') if p.exists() else None
def fmt(x): return json.dumps(x, ensure_ascii=False, separators=(',', ':'))
def run():
    evidence = ROOT/'evidencias'; evidence.mkdir(exist_ok=True)
    results=[]; log=[]
    version = subprocess.run(['java','-version'], capture_output=True, text=True, check=True)
    log.append(version.stderr.strip() or version.stdout.strip())
    with tempfile.TemporaryDirectory() as temp:
        tmp=Path(temp)
        for v in ('original','revisado'):
            classes=tmp/v; classes.mkdir()
            compile_cmd=['javac','-encoding','UTF-8','-d',str(classes),str(ROOT/v/'EstoqueArquivo.java'),str(ROOT/'testes/Executor.java')]
            subprocess.run(compile_cmd,check=True)
            log.append(f'\nCOMPILAÇÃO {v}: OK (javac -encoding UTF-8 -d <classes> {v}/EstoqueArquivo.java testes/Executor.java)')
            for id,method,path,initial,initiallog,cmd,expected,final,finallog in cases:
                work=tmp/(v+'-'+id); work.mkdir()
                setup(work/'estoque.csv',initial); setup(work/'movimentacoes.txt',initiallog)
                p=subprocess.run(['java','-cp',str(classes),'Executor',*cmd],cwd=work,capture_output=True,text=True,timeout=10)
                observed={'saida':p.stdout.splitlines(),'estoque':state(work/'estoque.csv'),'log':state(work/'movimentacoes.txt'),'exit':p.returncode}
                want={'saida':expected,'estoque':final,'log':finallog,'exit':0}
                status='PASSOU' if observed==want else 'FALHOU'
                pre={'estoque':initial,'log':initiallog,'ultima':''}
                results.append([id,v,method,path if v=='original' else 'Não se aplica ao CFG legado',fmt(cmd),fmt(pre),fmt(want),fmt(observed),status,f'evidencias/execucao.txt#{v}-{id}'])
                log.append(f'\n[{v}-{id}] java -cp <classes> Executor {fmt(cmd)}\npré={fmt(pre)}\nesperado={fmt(want)}\nobservado={fmt(observed)}\nstderr={p.stderr!r}\n{status}')
    for v in ('original','revisado'):
        subset=[r for r in results if r[1]==v]; count=sum(r[8]=='PASSOU' for r in subset)
        log.append(f'\nRESUMO {v}: {count}/{len(subset)} passaram; {len(subset)-count} falharam.')
    (evidence/'execucao.txt').write_text('\n'.join(log)+'\n',encoding='utf-8')
    with (evidence/'matriz.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.writer(f,delimiter=';'); w.writerow(['ID','Versão','Método','Caminho legado','Entrada','Pré-condição','Esperado','Observado','Situação','Evidência']); w.writerows(results)
    print('\n'.join(log[-2:]))
    return 0 if all(r[8]=='PASSOU' for r in results if r[1]=='revisado') else 1
if __name__=='__main__': raise SystemExit(run())
