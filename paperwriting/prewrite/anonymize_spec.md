<!-- 写作前材料(gap-review anonymize-E5);折进 LaTeX 时复核数字;非写作真源 -->

# Anonymization & release-scrub spec (gap-review E5)

**Deliverable this specifies:** the design of `src/anonymize.py` (the de-identification / release-packaging
tool) plus a `scrub-grep` self-check. **This document is a spec only — no script code here** (implement the
tool before **7/20**, ahead of the 7/31 supplementary+code upload per gap-review E1). Line numbers cited by the
E5 charter (e.g. `results.json:764/852/…`) are *stale/indicative only* — `results.json` has since grown to
~2.3k lines. **The tool must be regex-driven, never line-number-driven** (line refs rot; patterns don't).

Venue context: AAAI-27 is **double-blind**. Anything that lets a reviewer deanonymize the authors, their
institution, their compute cluster, or the project must not appear in the released PDF, supplementary, or code.

---

## 1. Threat model — what counts as identifying

Eight leak classes, grouped by how they surface. (Concrete instances confirmed by a repo scan on 2026-07-08.)

| # | Class | Example tokens (verbatim) | Where it lives today |
|---|-------|---------------------------|----------------------|
| L1 | Author real name | `whyu`, `yuyue`, `linroger` | local paths; git author; `paper/genbench_review.md` |
| L2 | Author email / handle | `yuyue12111`, `hywang1109@163.com`, `linroger023@gmail.com` | **`.git` author identity**; not in prose |
| L3 | Local filesystem path | `/Users/whyu/GitProjects/why-aaai27/…` | `paper/genbench_review.md`, some `src/*.py` |
| L4 | Cluster / storage path | `/inspire/…`, `qb-ilm`, GPFS `$W/models/…` | build-note files, run scripts |
| L5 | Compute-platform name | `启智` (OpenI) | internal docs, run notes |
| L6 | Internal project codename | `WHYAAAI`, `WHYAAAI_DTYPE`, `WHYAAAI_MODEL`, `why-aaai`, `why-aaai27` | **38 tracked files** (env vars, dir name) |
| L7 | Internal workflow / doc names | workflow ids `w[a-z0-9]{8}` (see §4), `wf_[0-9a-f]{8}-…`, `终极review`, `gap-review`, `plan.md`, `sumandplan1.md` | `results.json`, `src/*.py` headers, `analysis/*` |
| L8 | VCS metadata | Chinese commit messages, `Co-Authored-By:` trailer, author name/email, branch names | `.git/` tree entirely |

Confirmed clean today: **`paper/draft.md` prose carries none of L1–L6** (scan returned zero hits). The risk is
almost entirely in (a) `results.json`, (b) a handful of `src/*.py` module headers, (c) `paper/genbench_review.md`,
and (d) `.git`. This is *why* an allowlist beats a scrub (§2).

**Not scrubbed (leave intact):** public dataset names (CounterFact/zsRE/MQuAKE), public model names
(R1-Distill-Qwen-32B, Llama-70B, …), public editor names (ROME/MEMIT/AlphaEdit), public library names
(EasyEdit/ThinkEdit), all reported metric values. These are load-bearing and non-identifying.

---

## 2. Design principle: whitelist packaging, not blacklist scrubbing

A blacklist scrub over the working tree would have to touch **38 files for `WHYAAAI` alone** and 11 for
`终极review` — high risk of a missed hit shipping. Instead:

> **`src/anonymize.py` builds a release bundle by copying an explicit allowlist of files into a clean staging
> directory, then applies deterministic scrub transforms, then hard-fails the build if the self-check grep
> (§4) finds any non-whitelisted hit.** Nothing ships unless it is on the manifest AND passes the grep.

### 2.1 Release manifest (allowlist) — three tiers

- **Ship as-is (after scrub pass):** `paper/*.tex`, compiled PDF, `paper/table_*.tex`, figure PDFs/PNGs.
- **Ship after per-file transform:** the `src/*.py` we choose to release (method/scoring code), each run through
  the path/name/codename/workflow-id rewrites in §3. Module *filenames* (`base_probe.py`, `genbench.py`,
  `think_budget.py`) are non-identifying and stay.
- **Ship only in derived form (never raw):** `results.json` → see §5. Internal-only files
  (`gap-review.md`, `plan.md`, `sumandplan1.md`, `paper/genbench_review.md`, `analysis/*`, `*review*.md`,
  `RUNBOOK.md`, `interplan*.md`, `report.md`, all `Pasted image*.png`) are **excluded from the manifest** and
  never enter the bundle.

Anything not explicitly on the manifest is absent by construction — the safest default.

---

## 3. Scrub transforms (applied per file in staging)

Deterministic, order-independent, idempotent. Each is a substitution, not a deletion, so structure survives.

| Transform | From → To |
|-----------|-----------|
| T1 path-home | `/Users/<user>/GitProjects/why-aaai27` and `/Users/<user>/…` → `<REPO_ROOT>` / `<PATH>` |
| T2 path-cluster | `/inspire/…`, `qb-ilm…`, GPFS `$W/…` → `<CLUSTER>` / `$DATA` |
| T3 name | `whyu` / `yuyue` / `linroger` / configured git name → `anon` (or drop) |
| T4 email | any RFC-822 address matching the author set → strip line or `<anon@example.com>` |
| T5 codename | `WHYAAAI_` → a neutral env prefix (e.g. `EDIT_`); `why-aaai27`/`why-aaai` → `<PROJECT>` |
| T6 platform | `启智` / OpenI references → `an internal cluster` |
| T7 workflow-id | `w[a-z0-9]{8}` real ids (§4) and `wf_[0-9a-f]{8}-…` → drop the parenthetical, or `<run-id>` |
| T8 provenance-Chinese | strip internal Chinese engineering annotations from released artifacts (see §5 for `results.json`; for `src/*.py` headers, replace the Chinese docstring with a short English one) |

**T5 caveat:** renaming `WHYAAAI_*` env vars must stay consistent across released code *and* any released
run-config so the bundle still runs. Do the rename repo-wide-in-staging, not per-file ad hoc.

**T8 caveat:** many `results.json`/`src` annotations reference `SUPERSEDED` / contamination-correction chains.
These are internal audit trail; they read as messy and can hint at the review process. Drop them from the
released derivation (§5), but **preserve the final chosen numbers** — the distilled artifact must still report
exactly the values the paper cites.

---

## 4. Self-check: `scrub-grep`

The mandated pattern (verbatim from the E5 charter — do not weaken):

```
whyu|yuyue|linroger|/Users/|/inspire/|qb-ilm|w[a-z0-9]{8}|启智|终极review
```

Augmented pattern (adds L2/L6/L7 tokens found in the scan — recommended):

```
whyu|yuyue|linroger|hywang|/Users/|/inspire/|qb-ilm|启智|终极review|WHYAAAI|why-aaai|w[a-z0-9]{8}|wf_[0-9a-f]{8}
```

Run over the **entire staging bundle including `.git`** (or, if shipping a tarball, over the tarball contents):

```
grep -rInE '<PATTERN>' <staging-dir>            # -I skip binaries, -n line, -r recurse
git -C <staging-dir> log --format='%an <%ae>%n%s%n%b'  | grep -E '<PATTERN>'   # VCS metadata
```

### 4.1 The `w[a-z0-9]{8}` false-positive rule (important)

`w[a-z0-9]{8}` matches ordinary English words, not just run ids. Confirmed false positives in-tree:
`workspace`, `worstcase`, `workflow`, `without`, `wikipedia`. **The check is not "zero matches"; it is "zero
matches after excluding a known-safe wordlist."** Real workflow ids confirmed in `results.json` (must be gone
post-scrub): `wz4rou8q3`, `wxl3p6hr7`, `wuq9wq97k`, `wtu31tkws`, `wq9e477xn`, `wjt97ozxo`, `wbho1h7a7`,
`wbhgnlufw`. Note one real id (`wbhgnlufw`) is all-letters, so a "must contain a digit" filter would miss it —
**use a safe-wordlist exclusion, not a digit heuristic**:

```
grep -roIE '\bw[a-z0-9]{8}\b' <staging-dir> \
  | grep -vwiE 'workspace|worstcase|workflow|without|wikipedia|worldwide|whatever|whenever' \
  # → must be EMPTY; any survivor is a real run id → build fails
```

### 4.2 CI gate

`src/anonymize.py --check` exits non-zero if the augmented grep (minus the safe-wordlist) yields any hit, if
`git log` metadata matches, or if any file outside the manifest is present. The release build target depends on
this gate — a dirty bundle cannot be produced.

---

## 5. `results.json` — never shipped raw

`results.json` is the noisiest leak source (workflow ids, Chinese provenance, `SUPERSEDED` audit chains,
internal file/line refs). Two acceptable release forms; pick one:

- **(A) English distilled JSON.** Keep the numeric/metric leaf values the paper cites; **drop every
  internal-annotation key** (`_note`, `_status`, `_interp`, `_diagnosis`, `_superseded_by`, `_bonus_*`,
  `_CORRECTION`, `_pending_draft_edits`, any key holding a workflow id or Chinese prose). Emit via a
  **key-allowlist**, not a blacklist, so a new internal key can't silently leak. Verify the distilled file
  passes §4.
- **(B) Per-case JSONL + summary tables only.** Ship the raw per-case scored rows (CounterFact case text is
  public) plus the aggregate tables. The JSONL export must also run a **field-allowlist** (drop internal tags
  like `cf200sup_strong`, model paths, workflow tags) and pass §4.

Either way the released artifact must reproduce exactly the values in the paper's tables. Do **not** hand-copy
numbers into the spec/tool — derive the distilled file from `results.json` programmatically so it stays in sync.

---

## 6. `.git` handling

The working repo's history is unshippable: author `yuyue12111 <hywang1109@163.com>`, Chinese commit subjects,
and `Co-Authored-By:` trailers. Release the bundle as **either** a fresh `git init` with a single squashed
commit under a neutral author (`anon <anon@example.com>`), **or** a plain tarball with no VCS. Never ship the
real `.git`. Also strip PDF metadata (author/producer/title) from the compiled paper (`exiftool`/`qpdf`), since
LaTeX embeds the local username by default.

---

## 7. Acceptance checklist (build is releasable iff all pass)

1. Bundle contains only manifest files (§2.1); no excluded internal doc present.
2. Augmented scrub-grep (§4) over staging **incl. `.git`/tarball** → clean (w-id check via §4.1 wordlist).
3. `git log` / VCS metadata → no author-identity or Chinese-message match.
4. `results.json` present only in distilled/JSONL form (§5); key/field-allowlist applied; cited numbers reproduce.
5. PDF metadata stripped (§6).
6. Human eyeball of surviving `w[a-z0-9]{8}` matches (confirm all are safe words) and of any `src/*.py` header.

---

## 8. Residual risks (out of automated scope — note, don't over-engineer)

- **Stylometry / self-citation:** the tool can't anonymize writing style or a `\cite` to the authors' prior
  work; that's an authoring-time judgment call at submission.
- **Filename fingerprints:** config/run names (`probe32b.yaml`, `run_esup_h200.sh`) encode the compute
  platform (`h200`/`h100`). Low risk, but rename to generic hardware tags if shipping run scripts.
- **arXiv-id fingerprint:** citing a cluster of very recent (2606.x) papers can hint at timing/venue; an
  authoring concern, not a scrub target.
- **False-positive burden:** §4.1's safe-wordlist needs a manual glance each release as new English `w…8`
  words enter the code — accept this as the cost of the mandated broad pattern.
