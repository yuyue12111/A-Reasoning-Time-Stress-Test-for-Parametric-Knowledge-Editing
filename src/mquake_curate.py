"""E-MULTIHOP/W3 · MQuAKE-CF 干净 2-hop 池筛选(零卡,de-risk 必做件)。

panel 警:不筛就跑 = null 只说明"ROME 不传播到多跳"(无聊),非"回退是 cloze 局部"。
本筛把 3000 → 单改写 → 真干净 2-hop(下游答案非编辑对象本身、问题确从本 subject 起、新旧下游答案可分),
并**标记先验主导的 hop_answer_old**(Trump/华盛顿 尾)供后续 GPU base-floor 门(基座靠先验就答对的须丢)。

干净判据(全零卡、确定性):
  ① n_rewrites==1(单编辑,合我们单条协议)
  ② hop_answer_new / hop_answer_old 都在且**可分**(互不相等、互不为子串)→ 能判回退方向
  ③ hop_answer_new != o_new(不为子串)→ 2-hop 答案是真下游实体,非"就是被编辑对象"(否则非真 2-hop)
  ④ subject 字面在 hops[0] → 多跳问题确从本 subject 起(probe 不点名 o_old)
输出 data/mquake_clean.jsonl({case_id,s,r,prompt(单跳编辑),o_old,o_new,hop_q=hops[0],hop_answer_new,hop_answer_old})
  + 打印各阶段计数 + hop_answer_old 频次 top(先验尾,base-floor 门据此)。

用法:python src/mquake_curate.py [--in data/mquake_cf_3k.jsonl] [--out data/mquake_clean.jsonl]
"""
import argparse, ast, json
from collections import Counter


def _parse_list(v):
    if isinstance(v, list):
        return v
    try:
        x = ast.literal_eval(v)
        return x if isinstance(x, list) else [x]
    except Exception:
        return [v] if v else []


def _sub(a, b):
    a, b = str(a).lower(), str(b).lower()
    return a == b or a in b or b in a


def curate(rows):
    """返回 (clean_list, stage_counts)。纯函数。"""
    st = Counter()
    clean = []
    for r in rows:
        st["total"] += 1
        if str(r.get("n_rewrites")) != "1":
            continue
        st["single_rewrite"] += 1
        hops = _parse_list(r.get("hops"))
        han, hao = (r.get("hop_answer_new") or "").strip(), (r.get("hop_answer_old") or "").strip()
        o_new, s = (r.get("o_new") or "").strip(), (r.get("s") or "").strip()
        if not (hops and han and hao):
            st["drop_missing_fields"] += 1
            continue
        if _sub(han, hao):                       # 新旧下游答案不可分 → 判不了回退
            st["drop_new_old_indistinct"] += 1
            continue
        if _sub(han, o_new):                     # 2-hop 答案就是被编辑对象 = 退化(非真 2-hop)
            st["drop_degenerate_hop_is_onew"] += 1
            continue
        if s.lower() not in str(hops[0]).lower():  # 多跳问题不从本 subject 起
            st["drop_subj_not_in_hopq"] += 1
            continue
        st["clean"] += 1
        clean.append({"case_id": r["case_id"], "s": s, "r": r.get("r"), "prompt": r.get("prompt"),
                      "o_old": r.get("o_old"), "o_new": o_new, "hop_q": hops[0],
                      "hop_answer_new": han, "hop_answer_old": hao,
                      "o_old_aliases": r.get("o_old_aliases"), "o_new_aliases": r.get("o_new_aliases")})
    return clean, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/mquake_cf_3k.jsonl")
    ap.add_argument("--out", default="data/mquake_clean.jsonl")
    ap.add_argument("--prior-flag-thresh", type=int, default=15,
                    help="hop_answer_old 出现 >= 此频次 → 标先验主导(base-floor 门重点查)")
    args = ap.parse_args()
    rows = [json.loads(l) for l in open(args.inp) if l.strip()]
    clean, st = curate(rows)
    with open(args.out, "w") as f:
        for c in clean:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print("# 阶段计数:")
    for k in ["total", "single_rewrite", "drop_missing_fields", "drop_new_old_indistinct",
              "drop_degenerate_hop_is_onew", "drop_subj_not_in_hopq", "clean"]:
        print(f"#   {k:<28} {st.get(k,0)}")
    freq = Counter(c["hop_answer_old"] for c in clean)
    prior = {k: v for k, v in freq.items() if v >= args.prior_flag_thresh}
    print(f"# → {args.out}  (干净 {len(clean)} 条)")
    print(f"# ⚠先验主导 hop_answer_old(>={args.prior_flag_thresh} 次,GPU base-floor 门须查基座是否靠先验答对):")
    for k, v in freq.most_common(8):
        print(f"#   {k!r}: {v}{'  ← 先验尾' if k in prior else ''}")
    n_prior = sum(v for v in prior.values())
    print(f"# 先验尾合计 ~{n_prior}/{len(clean)} 条 → base-floor 后预计残池 ~{len(clean)-n_prior}")


if __name__ == "__main__":
    main()
