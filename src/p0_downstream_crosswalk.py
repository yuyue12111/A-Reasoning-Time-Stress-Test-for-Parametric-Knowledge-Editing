"""Post-hoc P0 membership crosswalks for X1, necessity, W-A, and logit-lens.

This is a CPU-only audit.  It never changes the preregistered X1 gate and it
does not infer missing logit-lens case IDs from aggregate figures.
"""
import argparse
from collections import Counter, defaultdict
import glob
import hashlib
import json
import os
import subprocess

import metrics


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMBERSHIP_LABELS = ("old", "new", "neither")
ROUTES = ("Reflective-override", "Bridge", "Recall", "Associative")
X1_SOURCE_TO_ITEM = {
    "main_b3_greedy": ("a3", "32b"),
    "f2_b1_greedy": ("b16", "qwen32b-F2B1"),
    "f3_historical_sample_seed2": ("b16", "qwen32b-sample"),
}


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def sha_file(path):
    h = hashlib.sha256()
    with open(_abs(path), "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_record(path):
    return {"path": path, "sha256": sha_file(path)}


def sha_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path):
    with open(_abs(path), encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path):
    rows = []
    with open(_abs(path), encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            if not raw.strip():
                raise ValueError(f"{path}:{lineno}: blank line")
            try:
                row = json.loads(raw)
            except Exception as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{lineno}: expected JSON object")
            rows.append(row)
    return rows


def git_provenance():
    try:
        commit = subprocess.check_output(
            ["git", "-C", ROOT, "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(
            ["git", "-C", ROOT, "status", "--porcelain"], text=True,
            stderr=subprocess.DEVNULL).strip())
        return {"commit": commit, "dirty_worktree": dirty}
    except Exception:
        return {"commit": "unavailable", "dirty_worktree": None}


def load_membership(path):
    audit = read_json(path)
    if audit.get("summary", {}).get("technical_status") != "PASS":
        raise ValueError("P0 membership technical audit is not PASS")
    rows = audit.get("rows") or []
    if len(rows) != 101:
        raise ValueError(f"expected 101 P0 membership rows, got {len(rows)}")
    by_item = {}
    for row in rows:
        item_id = row.get("item_id")
        if not item_id or item_id in by_item:
            raise ValueError(f"invalid/duplicate P0 item_id: {item_id!r}")
        if row.get("membership") not in MEMBERSHIP_LABELS:
            raise ValueError(f"{item_id}: invalid membership={row.get('membership')!r}")
        by_item[item_id] = row
    return audit, by_item


def load_routes(path, membership_by_item):
    taxonomy = read_json(path)
    if (taxonomy.get("status") != "PASS" or
            taxonomy.get("corrected_taxonomy_status") != "COMPLETE"):
        raise ValueError("corrected taxonomy is not COMPLETE/PASS")
    by_item = {}
    for row in taxonomy.get("items") or []:
        item_id = row.get("item_id")
        if not item_id or item_id in by_item:
            raise ValueError(f"invalid/duplicate corrected route item_id: {item_id!r}")
        if row.get("primary") not in ROUTES:
            raise ValueError(f"{item_id}: invalid corrected route={row.get('primary')!r}")
        if membership_by_item.get(item_id, {}).get("membership") != "old":
            raise ValueError(f"{item_id}: corrected route attached to non-OLD membership")
        by_item[item_id] = row
    old_ids = {item_id for item_id, row in membership_by_item.items()
               if row["membership"] == "old"}
    if set(by_item) != old_ids:
        raise ValueError("corrected route IDs do not exactly match majority-OLD membership IDs")
    if len(by_item) != taxonomy.get("n_members"):
        raise ValueError("corrected taxonomy n_members mismatch")
    return taxonomy, by_item


def load_source_cot_features(membership_by_item, aliases):
    """Re-read every frozen source row and recompute CLR with the paper metric.

    Historical A3 prefeatures used a raw-COT hit.  The paper metric first removes
    literal subject restatements.  Keep both fields so downstream audits cannot
    accidentally treat them as the same instrument, even when their values happen
    to agree on this frozen subset.
    """
    line_cache, features, paths = {}, {}, set()
    for item_id, frozen in membership_by_item.items():
        path = frozen.get("source_path")
        line_no = frozen.get("source_line")
        expected_sha = frozen.get("source_row_sha256")
        if not path or not isinstance(line_no, int) or line_no < 1 or not expected_sha:
            raise ValueError(f"{item_id}: incomplete frozen source locator")
        if path not in line_cache:
            with open(_abs(path), encoding="utf-8") as f:
                line_cache[path] = f.read().splitlines()
            paths.add(path)
        lines = line_cache[path]
        if line_no > len(lines):
            raise ValueError(f"{item_id}: source_line={line_no} beyond {path}")
        raw = lines[line_no - 1]
        if sha_text(raw) != expected_sha:
            raise ValueError(f"{item_id}: frozen source-row SHA mismatch for {path}:{line_no}")
        row = json.loads(raw)
        if row.get("case_id") != frozen.get("case_id"):
            raise ValueError(f"{item_id}: source case_id mismatch")
        if row.get("o_old") != frozen.get("o_old"):
            raise ValueError(f"{item_id}: source o_old mismatch")
        cot = row.get("cot") or ""
        subject = row.get("s") or ""
        old = row.get("o_old")
        raw_clr = bool(metrics.hit(cot, old, aliases))
        paper_clr = bool(metrics.hit(metrics._without_subject(cot, subject), old, aliases))
        features[item_id] = {
            "historical_raw_clr_in_cot": raw_clr,
            "paper_clr_subject_scrubbed": paper_clr,
            "subject_scrub_changed_clr": raw_clr != paper_clr,
            "source_path": path,
            "source_line": line_no,
        }
    return features, [source_record(path) for path in sorted(paths)]


def load_a3_labels(paths):
    by_key = {}
    provenance = []
    for path in paths:
        scale = os.path.basename(path).split("labels_", 1)[1].split(".jsonl", 1)[0]
        provenance.append(source_record(path))
        for row in read_jsonl(path):
            key = (scale, row.get("case_id"))
            if not key[1] or key in by_key:
                raise ValueError(f"duplicate/missing A3 label key: {key}")
            by_key[key] = row
    return by_key, provenance


def membership_counter(rows):
    counts = Counter(row["p0_membership"] for row in rows)
    return {label: counts[label] for label in MEMBERSHIP_LABELS}


def route_counter(rows, key="corrected_route"):
    counts = Counter(row.get(key) for row in rows if row.get(key))
    return {route: counts[route] for route in ROUTES}


def membership_clr_blocks(rows, field="clr_in_cot"):
    blocks = {}
    for label in MEMBERSHIP_LABELS:
        subset = [row for row in rows if row["p0_membership"] == label]
        blocks[label] = {
            "n": len(subset),
            "clr_in_cot": sum(bool(row[field]) for row in subset),
            "corrected_routes": route_counter(subset),
        }
    non_old = [row for row in rows if row["p0_membership"] != "old"]
    blocks["non_old_combined"] = {
        "n": len(non_old),
        "clr_in_cot": sum(bool(row[field]) for row in non_old),
    }
    return blocks


def build_a3_crosswalk(membership_by_item, route_by_item, label_by_key,
                       historical_necessity, source_features):
    rows = []
    for item_id, membership in membership_by_item.items():
        if membership.get("pool") != "a3":
            continue
        key = (membership["cell"], membership["case_id"])
        if key not in label_by_key:
            raise ValueError(f"P0 A3 row has no historical label row: {key}")
        label = label_by_key[key]
        corrected = route_by_item.get(item_id)
        source = source_features.get(item_id)
        if source is None:
            raise ValueError(f"{item_id}: missing frozen source CLR recomputation")
        rows.append({
            "item_id": item_id,
            "scale": membership["cell"],
            "case_id": membership["case_id"],
            "historical_necessity_in_population": bool(label.get("in_population")),
            "historical_route": label.get("primary"),
            # Compatibility field: historical/raw A3 instrument.
            "clr_in_cot": bool((label.get("prefeatures") or {}).get("clr_in_cot")),
            "historical_raw_clr_in_cot": source["historical_raw_clr_in_cot"],
            "paper_clr_subject_scrubbed": source["paper_clr_subject_scrubbed"],
            "subject_scrub_changed_clr": source["subject_scrub_changed_clr"],
            "p0_membership": membership["membership"],
            "membership_vote_counts": membership.get("vote_counts"),
            "corrected_route": corrected.get("primary") if corrected else None,
        })
    rows.sort(key=lambda row: (row["scale"], row["case_id"]))
    if len(rows) != 33:
        raise ValueError(f"expected 33 frozen A3 P0 candidates, got {len(rows)}")

    legacy = [row for row in rows if row["historical_necessity_in_population"]]
    legacy_routes = route_counter(legacy, key="historical_route")
    legacy_clr = sum(row["clr_in_cot"] for row in legacy)
    legacy_paper_clr = sum(row["paper_clr_subject_scrubbed"] for row in legacy)
    expected = historical_necessity.get("pooled", {}).get("reversions", {})
    if (len(legacy), legacy_clr) != (expected.get("n"), expected.get("clr_in_cot")):
        raise ValueError("recomputed historical necessity n/CLR disagrees with results/necessity.json")
    expected_routes = {route: (expected.get("routes") or {}).get(route, 0) for route in ROUTES}
    if legacy_routes != expected_routes:
        raise ValueError("recomputed historical necessity route counts disagree with results/necessity.json")

    corrected_legacy_old = [row for row in legacy if row["p0_membership"] == "old"]
    all_old = [row for row in rows if row["p0_membership"] == "old"]
    if any(row["corrected_route"] is None for row in all_old):
        raise ValueError("an A3 majority-OLD row lacks a corrected route")
    if any(row["corrected_route"] is not None for row in rows
           if row["p0_membership"] != "old"):
        raise ValueError("an A3 non-OLD row retained a corrected route")

    return {
        "status": "PASS",
        "historical_necessity_19": {
            "n": len(legacy),
            "historical_clr_in_cot": legacy_clr,
            "paper_clr_subject_scrubbed": legacy_paper_clr,
            "historical_routes": legacy_routes,
            "p0_membership_counts": membership_counter(legacy),
            "membership_by_clr": membership_clr_blocks(legacy),
            "membership_by_paper_clr": membership_clr_blocks(
                legacy, field="paper_clr_subject_scrubbed"),
            "corrected_old_subset": {
                "n": len(corrected_legacy_old),
                "clr_in_cot": sum(row["clr_in_cot"] for row in corrected_legacy_old),
                "paper_clr_subject_scrubbed": sum(
                    row["paper_clr_subject_scrubbed"] for row in corrected_legacy_old),
                "routes": route_counter(corrected_legacy_old),
            },
            "rows": legacy,
            "authority_note": ("The 19-row table is the historical results/necessity.json denominator "
                               "defined by results/a3/labels_*.jsonl in_population. P0 membership is "
                               "a post-hoc semantic crosswalk, not a rewrite of that historical artifact."),
        },
        "all_a3_candidates_33": {
            "n": len(rows),
            "p0_membership_counts": membership_counter(rows),
            "membership_by_clr": membership_clr_blocks(rows),
            "membership_by_paper_clr": membership_clr_blocks(
                rows, field="paper_clr_subject_scrubbed"),
            "subject_scrub_changed_n": sum(row["subject_scrub_changed_clr"] for row in rows),
            "rows": rows,
        },
        "clr_instrument_note": ("historical/raw CLR is retained for exact reproduction of "
                                "results/necessity.json; paper_clr_subject_scrubbed is independently "
                                "recomputed from each frozen source COT with metrics._without_subject. "
                                "They agree on this 33-row A3 subset, but remain distinct instruments."),
    }


def x1_item_id(row):
    source = row.get("source")
    if source not in X1_SOURCE_TO_ITEM:
        raise ValueError(f"unknown X1 source arm: {source!r}")
    pool, cell = X1_SOURCE_TO_ITEM[source]
    return f"{pool}|{cell}|{row['case_id']}"


def build_x1_crosswalk(manifest_rows, gate, membership_by_item, route_by_item):
    if len(manifest_rows) != 18:
        raise ValueError(f"expected 18 frozen X1 manifest rows, got {len(manifest_rows)}")
    gate_rows = gate.get("per_case") or []
    gate_by_case = {row.get("case_id"): row for row in gate_rows}
    if len(gate_by_case) != 18:
        raise ValueError("X1 gate does not contain 18 unique per-case rows")
    rows = []
    seen = set()
    for manifest in manifest_rows:
        item_id = x1_item_id(manifest)
        if item_id in seen:
            raise ValueError(f"duplicate X1 mapped item_id: {item_id}")
        seen.add(item_id)
        if item_id not in membership_by_item:
            raise ValueError(f"X1 row absent from P0 frozen candidate pool: {item_id}")
        case_id = manifest["case_id"]
        if case_id not in gate_by_case:
            raise ValueError(f"X1 manifest case missing from official gate: {case_id}")
        membership = membership_by_item[item_id]
        official = gate_by_case[case_id]
        rows.append({
            "manifest_index": len(rows) + 1,
            "item_id": item_id,
            "case_id": case_id,
            "source": manifest["source"],
            "source_path": manifest.get("source_path"),
            "source_line": manifest.get("source_line"),
            "p0_membership": membership["membership"],
            "membership_vote_counts": membership.get("vote_counts"),
            "corrected_route": route_by_item.get(item_id, {}).get("primary"),
            "official_x1_b0_strict": bool(official.get("b0_strict")),
            "official_x1_answer_judge": official.get("judge"),
            "official_x1_success": bool(official.get("success")),
        })
    by_source = {}
    for source in X1_SOURCE_TO_ITEM:
        subset = [row for row in rows if row["source"] == source]
        by_source[source] = {"n": len(subset), "membership_counts": membership_counter(subset)}
    return {
        "status": "PASS",
        "n": len(rows),
        "membership_counts": membership_counter(rows),
        "by_source": by_source,
        "rows": rows,
        "official_preregistered_gate": {
            "status": gate.get("status"),
            "success": gate.get("success"),
            "n_frozen": gate.get("n_frozen"),
            "required": gate.get("required"),
            "verdict": "UNCHANGED: preregistered 9/18 FAIL",
        },
        "claim_ceiling": ("P0 membership is a post-hoc source-membership diagnostic only. It does not "
                          "recompute, rescue, or filter the official X1 gate."),
    }


def load_wa_edited(pattern):
    paths = sorted(glob.glob(_abs(pattern)))
    if not paths:
        raise ValueError(f"no W-A edited shards matched {pattern}")
    rows, seen = [], set()
    provenance = []
    for path_abs in paths:
        path = os.path.relpath(path_abs, ROOT)
        provenance.append(source_record(path))
        for lineno, row in enumerate(read_jsonl(path), 1):
            if row.get("_meta"):
                continue
            case_id = row.get("case_id")
            if not case_id or case_id in seen:
                raise ValueError(f"duplicate/missing W-A edited case_id: {case_id!r}")
            seen.add(case_id)
            rows.append({**row, "_source_path": path, "_source_line": lineno})
    return rows, provenance


def build_wa_crosswalk(wa_rows, membership_by_item, route_by_item):
    a3_32b = {row["case_id"]: row for row in membership_by_item.values()
              if row.get("pool") == "a3" and row.get("cell") == "32b"}
    a2rev = [row for row in wa_rows if row.get("group") == "a2rev"]
    if len(a2rev) != 16:
        raise ValueError(f"expected 16 W-A edited a2rev rows, got {len(a2rev)}")
    detailed = []
    for row in sorted(a2rev, key=lambda item: item["case_id"]):
        case_id = row["case_id"]
        membership = a3_32b.get(case_id)
        item_id = f"a3|32b|{case_id}" if membership else None
        detailed.append({
            "case_id": case_id,
            "wa_group": "a2rev",
            "wa_probe_status": row.get("gate") or ("error" if row.get("error") else "measured"),
            "wa_source_path": row["_source_path"],
            "wa_source_line": row["_source_line"],
            "p0_item_id": item_id,
            "p0_membership": membership.get("membership") if membership else None,
            "corrected_route": route_by_item.get(item_id, {}).get("primary") if item_id else None,
        })
    overlap = [row for row in detailed if row["p0_membership"] is not None]
    missing = [row["case_id"] for row in detailed if row["p0_membership"] is None]
    p0_not_wa = sorted(set(a3_32b) - {row["case_id"] for row in a2rev})

    group_overlap = {}
    for group in sorted({row.get("group") for row in wa_rows if row.get("group")}):
        ids = {row["case_id"] for row in wa_rows if row.get("group") == group}
        group_overlap[group] = {
            "wa_n": len(ids),
            "overlap_with_p0_a3_32b": len(ids & set(a3_32b)),
        }
    return {
        "status": "PASS",
        "a2rev": {
            "wa_n": len(a2rev),
            "overlap_n": len(overlap),
            "overlap_membership_counts": membership_counter(overlap),
            "wa_cases_missing_from_p0_a3_32b": missing,
            "p0_a3_32b_cases_missing_from_wa_a2rev": p0_not_wa,
            "rows": detailed,
        },
        "all_group_overlap_counts": group_overlap,
        "interpretation": ("W-A lexical/frozen group label a2rev is not semantic committed-OLD: only the "
                           "P0-overlap rows can be crosswalked, and their P0 memberships are reported "
                           "without relabeling the W-A artifact."),
    }


def build_logitlens_crosswalk(path, membership_by_item, route_by_item, expected_n=23):
    if not os.path.exists(_abs(path)):
        return {
            "status": "BLOCKED_MISSING_PER_ITEM_ARTIFACT",
            "expected_path": path,
            "expected_authoritative_n": expected_n,
            "missing": True,
            "reason": ("paperwriting/results.json contains only an aggregate n=23 record. Without the raw "
                       "per-item JSONL, case IDs cannot be recovered or guessed."),
        }
    raw = read_jsonl(path)
    rows, seen = [], set()
    for lineno, row in enumerate(raw, 1):
        if row.get("_meta"):
            continue
        if row.get("error"):
            raise ValueError(f"{path}:{lineno}: logit-lens error row prevents a 23-item crosswalk")
        case_id = row.get("case_id")
        if not case_id or case_id in seen:
            raise ValueError(f"{path}:{lineno}: missing/duplicate case_id={case_id!r}")
        seen.add(case_id)
        item_id = f"a3|32b|{case_id}"
        membership = membership_by_item.get(item_id)
        rows.append({
            "case_id": case_id,
            "p0_item_id": item_id if membership else None,
            "p0_membership": membership.get("membership") if membership else None,
            "corrected_route": route_by_item.get(item_id, {}).get("primary") if membership else None,
            "edit_intact_at_cloze": row.get("edit_intact_at_cloze"),
            "gap_top": row.get("gap_top"),
        })
    if len(rows) != expected_n:
        raise ValueError(f"expected {expected_n} per-item logit-lens rows, got {len(rows)}")
    overlap = [row for row in rows if row["p0_membership"] is not None]
    return {
        "status": "PASS",
        "path": path,
        "sha256": sha_file(path),
        "n": len(rows),
        "p0_overlap_n": len(overlap),
        "p0_overlap_membership_counts": membership_counter(overlap),
        "not_in_p0_candidate_pool": [row["case_id"] for row in rows
                                      if row["p0_membership"] is None],
        "rows": rows,
    }


def build_report(args):
    membership_audit, membership_by_item = load_membership(args.membership_audit)
    taxonomy, route_by_item = load_routes(args.corrected_taxonomy, membership_by_item)
    aliases = read_json(args.aliases)
    source_features, frozen_source_provenance = load_source_cot_features(
        membership_by_item, aliases)
    label_paths = sorted(glob.glob(_abs(args.a3_labels_glob)))
    label_paths = [os.path.relpath(path, ROOT) for path in label_paths]
    if not label_paths:
        raise ValueError(f"no A3 label files matched {args.a3_labels_glob}")
    label_by_key, label_provenance = load_a3_labels(label_paths)
    historical_necessity = read_json(args.necessity)
    manifest_rows = read_jsonl(args.x1_manifest)
    x1_gate = read_json(args.x1_gate)
    wa_rows, wa_provenance = load_wa_edited(args.wa_edited_glob)

    logitlens = build_logitlens_crosswalk(
        args.logitlens, membership_by_item, route_by_item, args.logitlens_expected_n)
    report = {
        "status": ("PASS" if logitlens["status"] == "PASS"
                   else "PASS_WITH_BLOCKED_COMPONENT"),
        "technical_status": "PASS",
        "official_x1_gate": "UNCHANGED: preregistered 9/18 FAIL",
        "x1": build_x1_crosswalk(manifest_rows, x1_gate, membership_by_item, route_by_item),
        "necessity_and_a3": build_a3_crosswalk(
            membership_by_item, route_by_item, label_by_key, historical_necessity,
            source_features),
        "wa": build_wa_crosswalk(wa_rows, membership_by_item, route_by_item),
        "logitlens": logitlens,
        "provenance": {
            "code": source_record("src/p0_downstream_crosswalk.py"),
            "git": git_provenance(),
            "inputs": {
                "membership_audit": source_record(args.membership_audit),
                "corrected_taxonomy": source_record(args.corrected_taxonomy),
                "x1_manifest": source_record(args.x1_manifest),
                "x1_gate": source_record(args.x1_gate),
                "historical_necessity": source_record(args.necessity),
                "aliases": source_record(args.aliases),
                "frozen_chain_sources": frozen_source_provenance,
                "a3_labels": label_provenance,
                "wa_edited_shards": wa_provenance,
                "logitlens": ({"path": args.logitlens, "sha256": sha_file(args.logitlens)}
                               if os.path.exists(_abs(args.logitlens)) else
                               {"path": args.logitlens, "missing": True}),
            },
            "membership_source_status": membership_audit["summary"]["technical_status"],
            "taxonomy_source_status": taxonomy["corrected_taxonomy_status"],
        },
        "claim_ceiling": ("All membership-dependent numbers are post-hoc diagnostics over frozen "
                          "artifacts. They do not alter X1, select cases, or authorize new GPU runs."),
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--membership-audit", default="results/p0_membership_audit.json")
    ap.add_argument("--corrected-taxonomy", default="results/p0_corrected_taxonomy.json")
    ap.add_argument("--x1-manifest", default="data/x1_replay_manifest.jsonl")
    ap.add_argument("--x1-gate", default="results/x1_replay_gate.json")
    ap.add_argument("--necessity", default="results/necessity.json")
    ap.add_argument("--aliases", default="data/aliases.json")
    ap.add_argument("--a3-labels-glob", default="results/a3/labels_*.jsonl")
    ap.add_argument("--wa-edited-glob", default="results/wa/edited_r*of8.jsonl")
    ap.add_argument("--logitlens", default="results/probe/logitlens_cf200_ROME_B3.jsonl")
    ap.add_argument("--logitlens-expected-n", type=int, default=23)
    ap.add_argument("--out", default="results/p0_downstream_crosswalk.json")
    args = ap.parse_args()
    report = build_report(args)
    os.makedirs(os.path.dirname(_abs(args.out)) or ROOT, exist_ok=True)
    with open(_abs(args.out), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    summary = {
        "status": report["status"],
        "x1_membership": report["x1"]["membership_counts"],
        "necessity_19_membership": report["necessity_and_a3"]["historical_necessity_19"]["p0_membership_counts"],
        "a3_33_membership": report["necessity_and_a3"]["all_a3_candidates_33"]["p0_membership_counts"],
        "wa_a2rev": {key: report["wa"]["a2rev"][key] for key in
                     ("wa_n", "overlap_n", "overlap_membership_counts",
                      "wa_cases_missing_from_p0_a3_32b")},
        "logitlens": report["logitlens"]["status"],
        "out": args.out,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
