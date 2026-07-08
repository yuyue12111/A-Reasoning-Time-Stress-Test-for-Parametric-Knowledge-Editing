# -*- coding: utf-8 -*-
"""硬伤4 正解:从本地 wa base 分片重算 prereg-冻结的 **max-stat** G5,对比实跑的 z≥2 版。

背景:实跑 wa_main_analyze.py 的 G5 用固定 z≥2 阈值(zpre_max≥2,窄窗 [m-20,m-5)),偏离冻结
prereg 的 distractor max-stat(o_old 的带×窗 max-z 超全部 20 个 distractor,p=1/21)。git 考古无法证
z≥2 早于开盲 → 曾只能标 post-hoc。但 wa_probe.py 存了 `positive` 字段=S_old>max(20 个 S_d)=
**正是 max-stat 判据**,在 a2rev/a2held 组算于 el_idx(=首现前的 eligible 前窗,line 335-342)。
故可用本地数据重算冻结口径 G5=base 组 positive 率。

  python src/wa_g5_maxstat.py            # 打印 + 出 results/wa_g5_maxstat.json

口径注:①两版同 band [16,48]、同 base a2rev/a2held/calib 群体,apples-to-apples。②max-stat 窗=el_idx
(整个 eligible 前窗),非 prereg 字面的窄 [m-20,m-1](后者的 distractor z 未存,不可算)——但 max-stat
判据本身=prereg 冻结口径,窗差如实注。纯 stdlib。
"""
import json, os, glob

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAND = (16, 48)
GROUPS = ("a2rev", "a2held", "calib")   # 有前窗(有 mention)的 premention 组;G5 群体


def load(pat):
    rows = []
    for f in sorted(glob.glob(pat)):
        for l in open(f):
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("_meta") or r.get("error") or r.get("gate"):
                continue
            rows.append(r)
    return rows


def main():
    B = load(os.path.join(_ROOT, "results", "wa", "base_r*of8.jsonl"))
    pop = [r for r in B if r.get("group") in GROUPS]

    def zpre_max(r):
        zp = r.get("z_pre_by_layer")
        return max(zp[BAND[0]:BAND[1] + 1]) if isinstance(zp, list) and zp else None

    # 实跑 z≥2 版(复现 wa_main G5:zpre_max 存在且 ≥2)
    z2_pop = [r for r in pop if zpre_max(r) is not None]
    z2_det = sum(1 for r in z2_pop if zpre_max(r) >= 2)
    # 冻结 max-stat 版(positive=S_old>max(20 distractor);同群体、可比)
    ms_pop = [r for r in pop if r.get("positive") is not None]
    ms_det = sum(1 for r in ms_pop if r["positive"])
    # 同时满足 z_pre 存在的子群体上直接对拍(最公平)
    both = [r for r in pop if zpre_max(r) is not None and r.get("positive") is not None]
    both_z2 = sum(1 for r in both if zpre_max(r) >= 2)
    both_ms = sum(1 for r in both if r["positive"])
    agree = sum(1 for r in both if (zpre_max(r) >= 2) == bool(r["positive"]))

    def by_group(key):
        out = {}
        for g in GROUPS:
            gr = [r for r in pop if r.get("group") == g]
            if key == "z2":
                gr = [r for r in gr if zpre_max(r) is not None]
                out[g] = f"{sum(1 for r in gr if zpre_max(r) >= 2)}/{len(gr)}"
            else:
                gr = [r for r in gr if r.get("positive") is not None]
                out[g] = f"{sum(1 for r in gr if r['positive'])}/{len(gr)}"
        return out

    res = {
        "_status": "硬伤4 正解(src/wa_g5_maxstat.py):本地 wa base 分片重算冻结 max-stat G5 vs 实跑 z≥2 版。",
        "band": list(BAND),
        "z2_variant(实跑口径)": {"n": len(z2_pop), "det": z2_det,
                              "rate": round(z2_det / len(z2_pop), 4) if z2_pop else None,
                              "by_group": by_group("z2")},
        "maxstat_variant(冻结 prereg 口径,positive=S_old>全20 distractor)": {
            "n": len(ms_pop), "det": ms_det,
            "rate": round(ms_det / len(ms_pop), 4) if ms_pop else None,
            "by_group": by_group("ms")},
        "head_to_head(同子群体 z_pre 存在)": {
            "n": len(both), "z2_det": both_z2, "maxstat_det": both_ms,
            "agree_rate": round(agree / len(both), 4) if both else None},
        "_window_caveat": "max-stat 判据=prereg 冻结口径;窗=el_idx(整个 eligible 前窗,首现前)非字面 [m-20,m-1](后者 distractor z 未存)。z≥2 版窗=窄 [m-20,m-5)。band 同 [16,48]。",
    }
    dst = os.path.join(_ROOT, "results", "wa_g5_maxstat.json")
    json.dump(res, open(dst, "w"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    print(f"\n写出 {dst}")


if __name__ == "__main__":
    main()
