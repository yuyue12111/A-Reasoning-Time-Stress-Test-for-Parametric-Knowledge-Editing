# -*- coding: utf-8 -*-
"""W-A 主分析修正版(修 fork 版 A2 n=0/G4 n=0 取数 bug;prereg §2 端点)。→ results/wa_main_analysis.json"""
import json, glob, math, random

BAND = (16, 48)
def load(pat):
    rows = [json.loads(l) for f in sorted(glob.glob(pat)) for l in open(f) if l.strip()]
    return [r for r in rows if not r.get("_meta") and not r.get("error") and not r.get("gate")]
def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return None
E, B = load("results/wa/edited_r*of8.jsonl"), load("results/wa/base_r*of8.jsonl")
for rows in (E, B):
    for r in rows:
        r["S_old"] = fnum(r.get("S_old")); r["g3_agree"] = fnum(r.get("g3_agree"))
        r["pos"] = str(r.get("positive")) == "True"; r["amb"] = str(r.get("ambiguous_1sttok")) == "True"
        zp = r.get("z_pre_by_layer")
        r["zpre_max"] = max(zp[BAND[0]:BAND[1]+1]) if isinstance(zp, list) and zp else None
def g3ok(r): return (r["g3_agree"] or 0) >= 0.95
def wilson(k, n):
    if not n: return None
    p, z = k/n, 1.96; d = 1+z*z/n
    c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return [round(c-h,4), round(c+h,4)]
def binom_ge(k, n, p0=1/21):
    from math import comb
    return sum(comb(n,i)*p0**i*(1-p0)**(n-i) for i in range(k,n+1))
def A1(drop_amb):
    g=[r for r in E if r["group"]=="a1" and g3ok(r) and (not drop_amb or not r["amb"])]
    k=sum(r["pos"] for r in g); n=len(g)
    return {"n":n,"pos":k,"rate":round(k/n,3) if n else None,"wilson95":wilson(k,n),"binom_p":round(binom_ge(k,n),4) if n else None}
def mw(a,b):
    if not a or not b: return None
    U=sum((x>y)+0.5*(x==y) for x in a for y in b); auc=U/(len(a)*len(b))
    rng=random.Random(42); pool=a+b; na=len(a); cnt=0
    for _ in range(10000):
        rng.shuffle(pool)
        if sum((x>y)+0.5*(x==y) for x in pool[:na] for y in pool[na:])>=U: cnt+=1
    return {"n":[len(a),len(b)],"auc":round(auc,3),"perm_p_one_sided":round(cnt/10000,4)}
def boot_med(d,B_=10000):
    rng=random.Random(42); n=len(d)
    ms=sorted(sorted(rng.choices(d,k=n))[n//2] for _ in range(B_))
    return [round(ms[int(0.025*B_)],3), round(ms[int(0.975*B_)],3)]
out={"consort":{"edited":len(E),"base":len(B),"g3_fail":sum(1 for r in E if not g3ok(r)),"amb":sum(1 for r in E if r["amb"])}}
out["A1_main_no_amb"]=A1(True); out["A1_sens_with_amb"]=A1(False)
def zp(g): return [r["zpre_max"] for r in E if r["group"]==g and g3ok(r) and not r["amb"] and r["zpre_max"] is not None]
out["A2_MW_rev_gt_held"]=mw(zp("a2rev"),zp("a2held"))
bmap={r["case_id"]:r for r in B}
def a3(gs):
    d=[r["S_old"]-bmap[r["case_id"]]["S_old"] for r in E if r["group"] in gs and g3ok(r)
       and r["case_id"] in bmap and r["S_old"] is not None and bmap[r["case_id"]]["S_old"] is not None]
    if not d: return None
    d.sort(); return {"n":len(d),"median":round(d[len(d)//2],3),"ci95":boot_med(d)}
out["A3_all"]=a3({"a1","a2rev","a2held","calib"})
out["A3_by_group"]={g:a3({g}) for g in ("a1","a2rev","a2held")}
g4=[r for r in B if r["group"]=="a1"]
out["G4_base_a1"]={"n":len(g4),"pos":sum(r["pos"] for r in g4),"rate":round(sum(r["pos"] for r in g4)/len(g4),3) if g4 else None}
g5=[r for r in B if r["group"] in ("a2rev","a2held","calib") and r["zpre_max"] is not None]
out["G5_base_premention_z2"]={"n":len(g5),"det":sum(r["zpre_max"]>=2 for r in g5),"rate":round(sum(r["zpre_max"]>=2 for r in g5)/len(g5),3) if g5 else None}
out["edited_pos"]={g:f"{sum(r['pos'] for r in E if r['group']==g and g3ok(r))}/{sum(1 for r in E if r['group']==g and g3ok(r))}" for g in ("a1","a2rev","a2held","calib")}
out["base_pos"]={g:f"{sum(r['pos'] for r in B if r['group']==g)}/{sum(1 for r in B if r['group']==g)}" for g in ("a1","a2rev","a2held","calib")}
json.dump(out,open("results/wa_main_analysis.json","w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
