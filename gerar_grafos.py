#!/usr/bin/env python3
"""Gera DOT/PNG e verifica independência dos caminhos por posto sobre GF(2)."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parent
Q={1:'Entrada',2:'quantidade = 0',3:'try: abrir BufferedReader (L13)',4:'readLine() != null? (L15)',5:'split(";") (L16)',6:'colunas[0].equals(codigo)? (L17)',7:'parseInt(colunas[1]) (L18)',8:'break (L19)',9:'catch IOException (L22–24)',10:'return quantidade (L25)',11:'Exceção não capturada',12:'Saída única'}
QE=[(1,2,''),(2,3,''),(3,4,'OK'),(3,9,'IOException'),(4,5,'sim'),(4,10,'não / EOF'),(4,9,'IOException'),(5,6,''),(6,7,'sim'),(6,4,'não'),(6,11,'AIOOBE'),(7,8,'OK'),(7,11,'AIOOBE / NFE'),(8,10,''),(9,10,''),(10,12,''),(11,12,'')]
QP={'Q1':[1,2,3,4,10,12],'Q2':[1,2,3,4,5,6,7,8,10,12],'Q3':[1,2,3,4,5,6,4,10,12],'Q4':[1,2,3,9,10,12],'Q5':[1,2,3,4,9,10,12],'Q6':[1,2,3,4,5,6,11,12],'Q7':[1,2,3,4,5,6,7,11,12]}
R={1:'Entrada',2:'consultarQuantidade(codigo) (L29)',3:'quantidade <= disponivel? (L30)',4:'try: abrir FileWriter (L32)',5:'write(...) (L33)',6:'ultimaMovimentacao = codigo (L34)',7:'return true (L35)',8:'catch IOException (L36–38)',9:'return false (L40)',10:'Exceção propagada da consulta',11:'Saída única'}
RE=[(1,2,''),(2,3,'OK'),(2,10,'AIOOBE / NFE'),(3,4,'sim'),(3,9,'não'),(4,5,'OK'),(4,8,'IOException'),(5,6,'OK'),(5,8,'IOException'),(6,7,''),(7,11,''),(8,9,''),(9,11,''),(10,11,'')]
RP={'R1':[1,2,3,4,5,6,7,11],'R2':[1,2,3,9,11],'R3':[1,2,3,4,8,9,11],'R4':[1,2,3,4,5,8,9,11],'R5':[1,2,10,11]}
def rank(rows):
    pivots={}
    for r in rows:
        while r:
            p=r.bit_length()-1
            if p in pivots:r^=pivots[p]
            else:pivots[p]=r;break
    return len(pivots)
def generate(name,nodes,edges,paths,decisions,exception,ends):
    ed=[(a,b) for a,b,_ in edges]
    masks=[]
    for path in paths.values():
        mask=0
        for a,b in zip(path,path[1:]):mask^=1<<ed.index((a,b))
        masks.append(mask)
    v=len(edges)-len(nodes)+2
    assert rank(masks)==v==len(paths)
    assert {n for a,b in ed for n in (a,b)}==set(nodes)
    lines=['digraph CFG {','graph [rankdir=TB, bgcolor="white", pad=0.25, nodesep=0.4, ranksep=0.45, labelloc=t, fontsize=18, fontname="DejaVu Sans", label="'+name+' | N='+str(len(nodes))+' E='+str(len(edges))+' V(G)='+str(v)+'"];','node [shape=box, style="rounded,filled", fillcolor="#edf3fa", color="#385574", fontname="DejaVu Sans", fontsize=11];','edge [fontname="DejaVu Sans", fontsize=10, color="#385574"];']
    for i, label in nodes.items():
        label=label.replace('"','\\"'); shape='diamond' if i in decisions else 'oval' if i in ends else 'box'
        fill='#fff0de' if i in exception else '#e7f4e9' if i in ends else '#edf3fa'
        lines.append(f'{i} [label="{i}. {label}", shape={shape}, fillcolor="{fill}"];')
    for a,b,l in edges:
        attrs=f'label="{l}"'
        if b in exception:attrs+=', color="#ad4a36", style=dashed'
        lines.append(f'{a} -> {b} [{attrs}];')
    lines.append('}')
    dot=ROOT/(name+'.dot');dot.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    subprocess.run(['dot','-Tpng','-Gdpi=150',str(dot),'-o',str(ROOT/(name+'.png'))],check=True)
    print(f'{name}: N={len(nodes)}, E={len(edges)}, P=1, V={v}, posto GF(2)={rank(masks)}')
if __name__=='__main__':
    generate('consultarQuantidade',Q,QE,QP,{4,6},{9,11},{1,12})
    generate('registrarSaida',R,RE,RP,{3},{8,10},{1,11})
