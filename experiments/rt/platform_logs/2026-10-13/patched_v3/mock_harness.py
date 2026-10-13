#!/usr/bin/env python3
"""Local MOCK harness for orch_s3h.py / watchdog.py (v2 candidate vs v3 patched copies).

Everything runs inside a sandbox under this directory: platform paths and /tmp lock paths are rewritten into the
sandbox, nvidia-smi is a mock script, and rt.deltas is a fake module that reproduces run_shard's resume semantics
(skip existing delta files without a row, skip logged error cases unless --retry-errors) and uses the real
summarize() source extracted from src/rt/deltas.py. No GPU, no repository file and no results data are touched.

Usage: python3 mock_harness.py <workdir> <repo_root> [scenario ...]
"""
import ast, io, json, os, shutil, signal, subprocess, sys, threading, time as _time, types, hashlib

WORK = os.path.abspath(sys.argv[1])
REPO = os.path.abspath(sys.argv[2])
ONLY = set(sys.argv[3:])
SRC = {'v2': {'orch': f'{WORK}/orch_s3h.v2.py', 'wd': f'{WORK}/watchdog.v2.py'},
       'v3': {'orch': f'{WORK}/v3/orch_s3h.py', 'wd': f'{WORK}/v3/watchdog.py'}}
RESULTS = []


def check(name, cond, detail=''):
    RESULTS.append((name, bool(cond), detail))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ''), flush=True)


# ------------------------------------------------------------------ sandbox
def sandbox(name):
    sbx = f'{WORK}/sbx/{name}'
    if os.path.exists(sbx):
        shutil.rmtree(sbx)
    why = f'{sbx}/why'
    for p in ('why-arr-h100/logs/rt', 'why-arr-h100/results/rt/s2', 'why-arr-h100/src/rt',
              'why-arr-h100/experiments/rt', 'platform_out_h100/results/rt', 'xfer', 'why-arr'):
        os.makedirs(f'{why}/{p}', exist_ok=True)
    os.makedirs(f'{sbx}/tmp', exist_ok=True)
    os.makedirs(f'{sbx}/bin', exist_ok=True)
    smi = f'{sbx}/bin/nvidia-smi'
    with open(smi, 'w') as fh:
        fh.write('''#!/bin/bash
# MOCK nvidia-smi for local tests only
if [ -n "$FAKE_SMI_HANG" ]; then exec sleep 600.123; fi
case "$*" in
  *utilization.gpu*) for i in 0 1 2 3 4 5 6 7; do echo "$i, 0"; done;;
  *memory.used*) n=$(echo "$*" | sed -n 's/.*-i \\([0-9,]*\\).*/\\1/p')
     if [ -z "$n" ]; then for i in 0 1 2 3 4 5 6 7; do echo 0; done; else for x in $(echo $n | tr ',' ' '); do echo 0; done; fi;;
  *name*) for i in 0 1 2 3 4 5 6 7; do echo "NVIDIA H100 80GB HBM3"; done;;
  *) echo mock;;
esac
''')
    os.chmod(smi, 0o755)
    return {'sbx': sbx, 'PROJH': f'{why}/why-arr-h100', 'POUTH': f'{why}/platform_out_h100',
            'SHARE': f'{why}/xfer', 'bin': f'{sbx}/bin'}


def rewrite(src_text, sbx):
    t = src_text.replace('/inspire/hdd/project/ai4education/public/why', f'{sbx}/why')
    t = t.replace('/inspire/hdd/global_public/public_models', f'{sbx}/gp')
    for p in ("/tmp/why_wd_state.lock", "/tmp/why_orch_s3h.lock", "/tmp/s3_progress.json", "/tmp/t.log",
              "/tmp/t2.log", "/tmp/d11_h100.sha256"):
        t = t.replace(p, f'{sbx}/tmp/{os.path.basename(p)}')
    return t


class TimeShim:
    """time module proxy whose sleep is capped (fast polling loops)."""
    def __init__(self, cap=0.02):
        self.cap = cap
    def __getattr__(self, k):
        return getattr(_time, k)
    def sleep(self, s):
        _time.sleep(min(s, self.cap))


def pid_alive_mac(pid):
    try:
        os.kill(int(pid), 0)
    except Exception:
        return False
    st = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
    return bool(st) and not st.startswith('Z')


def load(ver, kind, sb, extra_subs=()):
    path = SRC[ver][kind]
    txt = rewrite(open(path, encoding='utf-8').read(), sb['sbx'])
    for a, b in extra_subs:
        assert a in txt, a
        txt = txt.replace(a, b)
    mod = types.ModuleType(f'{kind}_{ver}')
    mod.__file__ = path
    exec(compile(txt, path, 'exec'), mod.__dict__)
    mod.time = TimeShim()
    if kind == 'orch':
        mod.pid_alive = pid_alive_mac
        mod.RT_PGREP = 'pgrep -f "rt[.](run|pool|deltas)" || true'
        mod.gpu_mem = lambda gpus: [0] * len(gpus)
        mod.wait_gpus_free = lambda timeout_s=1200: True
        mod.assert_h100 = lambda item: ['NVIDIA H100 80GB HBM3'] * 8
        mod.hourly = lambda: None
    else:
        mod.alive = pid_alive_mac
    return mod


def run_exit(fn, *a, **k):
    """Call fn; return ('ok', value) or ('halt', code)."""
    try:
        return ('ok', fn(*a, **k))
    except SystemExit as e:
        return ('halt', e.code)


def report(sb):
    p = f"{sb['POUTH']}/report_h100.md"
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''


def close_orch_lock(mod):
    fh = getattr(mod, '_ORCH_FH', None)
    if fh:
        try:
            fh.close()
        except Exception:
            pass
        mod._ORCH_FH = None


# ------------------------------------------------------------------ fake rt.deltas
def fake_deltas_module():
    src = open(f'{REPO}/src/rt/deltas.py', encoding='utf-8').read()
    tree = ast.parse(src)
    summ = [ast.get_source_segment(src, n) for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == 'summarize'][0]
    return '''"""MOCK rt.deltas for local orchestrator tests: run_shard resume semantics + the real summarize()."""
import argparse, json, math, os, sys

''' + summ + '''


def _env(name):
    return {x.strip() for x in os.environ.get(name, '').split(',') if x.strip()}


def run(a):
    tag = 's3fresh' if 'fresh' in os.path.basename(a.config) else 's3ext'
    n = int(open(f'fake_pool_{tag}.txt').read())
    cases = [f'c{i:03d}' for i in range(n)]
    if a.limit:
        cases = cases[:a.limit]                       # limit before sharding, as deltas.cmd_run
    mine = [c for i, c in enumerate(cases) if i % a.world == a.rank]
    log_dir = f'results/rt/deltas_logs/{tag}'
    os.makedirs(log_dir, exist_ok=True)
    log_path = f'{log_dir}/r1qwen32b_ROME_cf_r{a.rank}of{a.world}.jsonl'
    print(f"[deltas] r1qwen32b ROME cf n={len(cases)} shard={len(mine)} rank={a.rank}/{a.world}", flush=True)
    if str(a.world) in _env('FAKE_LOAD_OOM'):
        print("torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 2.00 GiB", flush=True)
        sys.exit(1)
    if str(a.world) in _env('FAKE_CRASH'):
        print("RuntimeError: simulated crash", flush=True)
        sys.exit(1)
    errors = set()
    if os.path.exists(log_path):
        for line in open(log_path):
            if line.strip():
                r = json.loads(line)
                if r.get('status') == 'error':
                    errors.add(r['case_id'])
    counts = {"ok": 0, "error": 0, "skipped_existing": 0, "skipped_error": 0}
    os.makedirs('deltas/r1qwen32b/ROME/cf', exist_ok=True)
    with open(log_path, 'a') as fh:
        fh.write(json.dumps({"_meta": True, "rank": a.rank, "world": a.world, "limit": a.limit}) + "\\n")
        for c in mine:
            p = f'deltas/r1qwen32b/ROME/cf/{c}.pt'
            if os.path.exists(p):
                counts['skipped_existing'] += 1
                continue
            if c in errors and not a.retry_errors:
                counts['skipped_error'] += 1
                continue
            key = f'{a.world}:{c}'
            if key in _env('FAKE_OOM'):
                row = {"case_id": c, "status": "error", "stage": "edit",
                       "error": "OutOfMemoryError('CUDA out of memory. Tried to allocate 1.00 GiB')"}
                print(f"[delta-fail] {c} at edit: {row['error']}", flush=True)
            elif key in _env('FAKE_ERR') or (key in _env('FAKE_ERR_ONCE') and not a.retry_errors):
                row = {"case_id": c, "status": "error", "stage": "extract", "error": "ValueError('simulated')"}
                print(f"[delta-fail] {c} at extract: {row['error']}", flush=True)
            else:
                open(p, 'w').write('mock delta\\n')
                row = {"case_id": c, "status": "ok", "sha": "mock", "layers": [5],
                       "fit": {"5": {"rank": 1, "rel_err": 1e-6, "tol": 1e-4, "rel_delta": 0.01}},
                       "lp_first": {"before": {"target": -4.0, "o_old": -0.3}, "after": {"target": -0.02, "o_old": -5.0}},
                       "editor_nan": False, "editor_steps": 20, "wall_s": 1.0}
            counts[row['status']] += 1
            fh.write(json.dumps(row) + "\\n")
    print(f"[deltas] done: {counts}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd')
    r = sub.add_parser('run')
    for k in ('--config', '--model-path'):
        r.add_argument(k)
    r.add_argument('--model-parallel', action='store_true')
    r.add_argument('--rank', type=int, default=0)
    r.add_argument('--world', type=int, default=1)
    r.add_argument('--device', type=int, default=0)
    r.add_argument('--limit', type=int, default=None)
    r.add_argument('--retry-errors', action='store_true')
    s = sub.add_parser('summarize')
    s.add_argument('logs', nargs='+')
    a = ap.parse_args()
    if a.cmd == 'run':
        run(a)
    else:
        print(json.dumps(summarize(a.logs), indent=1))


if __name__ == '__main__':
    main()
'''


FAKE_DELTAS = None


def deltas_sandbox(name, n):
    sb = sandbox(name)
    pj = sb['PROJH']
    open(f'{pj}/src/rt/__init__.py', 'w').close()
    with open(f'{pj}/src/rt/deltas.py', 'w') as fh:
        fh.write(FAKE_DELTAS)
    with open(f'{pj}/fake_pool_s3fresh.txt', 'w') as fh:
        fh.write(str(n))
    with open(f'{pj}/fake_pool_s3ext.txt', 'w') as fh:
        fh.write(str(n))
    return sb


def set_fake_env(**kw):
    for k in ('FAKE_OOM', 'FAKE_ERR', 'FAKE_ERR_ONCE', 'FAKE_LOAD_OOM', 'FAKE_CRASH'):
        os.environ.pop(k, None)
    for k, v in kw.items():
        os.environ[k] = v


def summ_json(sb):
    p = f"{sb['POUTH']}/summarize_S3_fresh.json"
    try:
        return json.loads(open(p).read())
    except Exception:
        return None


def smoke_marker(sb):
    p = f"{sb['SHARE']}/S3_D_SMOKE_OK"
    return open(p).read().split()[0] if os.path.exists(p) else None


def scen_deltas():
    N = 20
    cases = [
        # name, env, expect v3 (outcome, world), note
        ('no-OOM', {}, ('ok', 4)),
        ('A: w4 case0 ok, case4 OOM', {'FAKE_OOM': '4:c004'}, ('ok', 2)),
        ('B: w4 case0 OOM, case4 ok', {'FAKE_OOM': '4:c000'}, ('ok', 2)),
        ('full OOM (both w4 cases)', {'FAKE_OOM': '4:c000,4:c004'}, ('ok', 2)),
        ('OOM at model load (w4)', {'FAKE_LOAD_OOM': '4'}, ('ok', 2)),
        ('A + non-OOM error on world-2 smoke case2', {'FAKE_OOM': '4:c004', 'FAKE_ERR': '2:c002'}, ('halt', None)),
        ('B + non-OOM error on world-2 smoke case0', {'FAKE_OOM': '4:c000', 'FAKE_ERR': '2:c000'}, ('halt', None)),
        ('A + transient formal error -> --retry-errors', {'FAKE_OOM': '4:c004', 'FAKE_ERR_ONCE': '2:c011'}, ('ok', 2)),
    ]
    for ver in ('v2', 'v3'):
        print(f"\n== deltas_phase §3 OOM fallback ({ver}), pool n={N}")
        for ci, (nm, env, exp) in enumerate(cases):
            sb = deltas_sandbox(f'deltas_{ver}_{ci}', N)
            mod = load(ver, 'orch', sb)
            os.chdir(sb['PROJH'])
            set_fake_env(**env)
            out = run_exit(mod.deltas_phase, 's3fresh', 'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml', N, 'S3H-§3',
                           smoke=True, world=4)
            sj = summ_json(sb)
            got = (out[0], out[1] if out[0] == 'ok' else None)
            det = f"outcome={out}; S3_D_SMOKE_OK={smoke_marker(sb)}; formal summarize cases/ok={(sj or {}).get('cases')}/{(sj or {}).get('ok')}"
            if out[0] == 'halt':
                last = [l for l in report(sb).splitlines() if l.startswith('待裁决')][-1:]
                det += f"; halt: {last[0][:160] if last else '?'}"
            if ver == 'v3':
                good = got == exp and (out[0] != 'ok' or (sj and sj.get('cases') == N and sj.get('ok') == N))
                check(f'v3 deltas {nm}', good, det)
            else:
                print(f"  [info] v2 deltas {nm}: {det}")
        # resume after world-4 OOM + an interrupted world-2 smoke
        nm = 'resume: w4 OOM, world-2 smoke crashed, restart'
        sb = deltas_sandbox(f'deltas_{ver}_resume', N)
        mod = load(ver, 'orch', sb)
        os.chdir(sb['PROJH'])
        set_fake_env(FAKE_OOM='4:c000,4:c004', FAKE_CRASH='2')
        first = run_exit(mod.deltas_phase, 's3fresh', 'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml', N, 'S3H-§3',
                         smoke=True, world=4)
        set_fake_env(FAKE_OOM='4:c000,4:c004')                   # the restart: node back, same OOM behaviour
        smoke = not mod.marker('S3_D_SMOKE_OK')
        second = run_exit(mod.deltas_phase, 's3fresh', 'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml', N, 'S3H-§3',
                          smoke=smoke, world=mod.edit_world())
        sj = summ_json(sb)
        det = f"first={first}; restart={second}; S3_D_SMOKE_OK={smoke_marker(sb)}; cases/ok={(sj or {}).get('cases')}/{(sj or {}).get('ok')}"
        if second[0] == 'halt':
            last = [l for l in report(sb).splitlines() if l.startswith('待裁决')][-1:]
            det += f"; halt: {last[0][:160] if last else '?'}"
        if ver == 'v3':
            check(f'v3 deltas {nm}', first[0] == 'halt' and second == ('ok', 2) and sj and sj.get('ok') == N, det)
        else:
            print(f"  [info] v2 deltas {nm}: {det}")
    # §5 inherits world 2 (no smoke, no r*of4 logs in s3ext)
    sb = deltas_sandbox('deltas_v3_s5', N)
    mod = load('v3', 'orch', sb)
    os.chdir(sb['PROJH'])
    set_fake_env()
    with open(f"{sb['SHARE']}/S3_D_SMOKE_OK", 'w') as fh:
        fh.write('world=2 x\n')
    out = run_exit(mod.deltas_phase, 's3ext', 'experiments/rt/deltas_s3_r1qwen32b_ext.yaml', N, 'S3H-§5',
                   smoke=False, world=mod.edit_world())
    sj = json.loads(open(f"{sb['POUTH']}/summarize_S3_ext.json").read()) if out[0] == 'ok' else None
    check('v3 §5 at inherited world 2', out == ('ok', 2) and sj and sj['cases'] == N and sj['ok'] == N, f'{out} {sj and (sj["cases"], sj["ok"])}')
    with open(f"{sb['SHARE']}/S3_D_SMOKE_OK", 'w') as fh:
        fh.write('')
    out = run_exit(mod.edit_world)
    check('v3 edit_world halts on an empty S3_D_SMOKE_OK', out[0] == 'halt', str(out))
    set_fake_env()


# ------------------------------------------------------------------ main() control flow (v3)
def scen_main():
    print('\n== main() control flow (v3, phases stubbed)')

    def build(name, markers=(), real_wait_go=False):
        sb = sandbox(f'main_{name}')
        mod = load('v3', 'orch', sb)
        for m in markers:
            open(f"{sb['SHARE']}/{m}", 'w').close()
        calls = []

        def rec(nm, ret=None, touch=None):
            def f(*a, **k):
                calls.append(nm)
                if touch:
                    open(f"{sb['SHARE']}/{touch}", 'w').close()
                return ret
            return f
        mod.phase_s2 = rec('s2')
        mod.phase_s6 = rec('s6', touch='S3_SMOKE_DONE')
        mod.deltas_phase = lambda tag, *a, **k: calls.append(f'deltas:{tag}') or k.get('world', 4)
        mod.phase_s4 = rec('s4', ret=7)
        mod.record_ext_manifest = rec('rec_ext', ret=7)
        if not real_wait_go:
            def wg(item, go, nogo, who, need_note=False):
                calls.append(f'wait_go:{go}')
                open(f"{sb['SHARE']}/{go}", 'w').close()
            mod.wait_go = wg
        else:
            orig = mod.wait_go
            def wg(*a, **k):
                calls.append(f'wait_go:{a[1]}')
                return orig(*a, **k)
            mod.wait_go = wg
        mod.gen_phase = lambda kind, n, item, flag: calls.append(f'gen:{kind}:{n}') or open(flag, 'w').close()
        mod.s3_finalize = rec('finalize', touch='S3_END')
        for nm in ('registered_parent_intact', 'g3_smoke', 'g3_formal', 'g10_resume', 'g11_run', 'parent2_end'):
            setattr(mod, nm, rec(nm))
        return sb, mod, calls

    sb, mod, calls = build('fresh')
    out = run_exit(mod.main)
    close_orch_lock(mod)
    exp = ['s2', 's6', 'deltas:s3fresh', 's4', 'deltas:s3ext', 'wait_go:S3_SMOKE_GO', 'gen:fresh:309', 'gen:ext:7',
           'finalize', 'registered_parent_intact', 'g3_smoke', 'g3_formal', 'g10_resume', 'g11_run', 'parent2_end']
    check('fresh start order: §2 -> §6 smoke -> §3 -> §4 -> §5 -> wait GO -> §7 -> close-out -> §8', calls == exp, str(calls))

    sb, mod, calls = build('s3end', markers=('S3_CODE_OK', 'S3_SMOKE_DONE', 'S3_SMOKE_GO', 'S3_D_FRESH_DONE',
                                             'S3_EXT_MANIFEST_DONE', 'S3_D_EXT_DONE', 'S3_G_FRESH_DONE', 'S3_END'))
    out = run_exit(mod.main)
    close_orch_lock(mod)
    exp = ['s2', 'registered_parent_intact', 'g3_smoke', 'g3_formal', 'g10_resume', 'g11_run', 'parent2_end']
    check('S3_END (leader close-out, ext world incomplete) skips all Study 3 work', calls == exp and out[0] == 'ok', str(calls))

    sb, mod, calls = build('nogo_nodone', markers=('S3_CODE_OK', 'S3_SMOKE_NOGO'))
    out = run_exit(mod.main)
    close_orch_lock(mod)
    check('restart with S3_SMOKE_NOGO but no S3_SMOKE_DONE halts at §6 before §3', out[0] == 'halt' and calls == ['s2'],
          f'{out} {calls}')

    sb, mod, calls = build('go_nodone', markers=('S3_CODE_OK', 'S3_SMOKE_GO'))
    out = run_exit(mod.main)
    close_orch_lock(mod)
    check('S3_SMOKE_GO without S3_SMOKE_DONE halts at §6', out[0] == 'halt' and calls == ['s2'], f'{out} {calls}')

    sb, mod, calls = build('nogo_done', markers=('S3_CODE_OK', 'S3_SMOKE_DONE', 'S3_SMOKE_NOGO'), real_wait_go=True)
    out = run_exit(mod.main)
    close_orch_lock(mod)
    check('S3_SMOKE_NOGO touched during edits: §3–§5 finish, halt at the §7 gate',
          out[0] == 'halt' and calls == ['s2', 'deltas:s3fresh', 's4', 'deltas:s3ext', 'wait_go:S3_SMOKE_GO']
          and 'executor agent 或 leader' in report(sb), f'{out} {calls}')

    sb, mod, calls = build('go_done_resume', markers=('S3_CODE_OK', 'S3_SMOKE_DONE', 'S3_SMOKE_GO', 'S3_D_SMOKE_OK',
                                                      'S3_D_FRESH_DONE', 'S3_EXT_MANIFEST_DONE', 'S3_D_EXT_DONE',
                                                      'S3_G_FRESH_DONE'), real_wait_go=True)
    with open(f"{sb['SHARE']}/S3_D_SMOKE_OK", 'w') as fh:
        fh.write('world=4 x\n')
    out = run_exit(mod.main)
    close_orch_lock(mod)
    exp = ['s2', 'rec_ext', 'wait_go:S3_SMOKE_GO', 'gen:ext:7', 'finalize', 'registered_parent_intact', 'g3_smoke',
           'g3_formal', 'g10_resume', 'g11_run', 'parent2_end']
    check('resume mid-§7 (fresh done): skips smoke and edits, runs ext then close-out and §8', calls == exp, str(calls))

    # stale second-window markers on a fresh start
    sb = sandbox('main_stale')
    mod = load('v3', 'orch', sb)
    open(f"{sb['SHARE']}/s3_code_full.bundle", 'w').close()
    mod.BUNDLE_SHA = hashlib.sha256(b'').hexdigest()
    open(f"{sb['SHARE']}/G3_SMOKE_GO", 'w').close()
    out = run_exit(mod.phase_s2, resume=False)
    check('fresh start with a leftover G3_SMOKE_GO halts in §2', out[0] == 'halt' and 'G3_SMOKE_GO' in report(sb), str(out))

    # resume while rt ranks still run: halt before the watchdog reset
    sb = sandbox('main_resume_alive')
    mod = load('v3', 'orch', sb)
    open(f"{sb['SHARE']}/S3_CODE_OK", 'w').close()
    st = {'ranks': [{'project': 'S3H-§7 fresh', 'rank': r, 'pid': 99990 + r, 'status': 'running'} for r in range(8)]}
    with open(mod.WD_STATE, 'w') as fh:
        json.dump(st, fh)
    mod.RT_PGREP = "echo '4242 python3 -m rt.run --config x'"
    out = run_exit(mod.main)
    close_orch_lock(mod)
    after = json.load(open(mod.WD_STATE))
    check('resume with live rt ranks halts and keeps their watchdog entries', out[0] == 'halt' and len(after['ranks']) == 8,
          f"{out} ranks_after={len(after['ranks'])}")
    v2 = load('v2', 'orch', sandbox('main_resume_alive_v2'))
    open(f"{v2.SHARE}/S3_CODE_OK", 'w').close()
    open(f"{v2.SHARE}/s3_code_full.bundle", 'w').close()
    v2.BUNDLE_SHA = hashlib.sha256(b'').hexdigest()
    with open(v2.WD_STATE, 'w') as fh:
        json.dump(st, fh)
    v2.RT_PGREP = "echo '4242 python3 -m rt.run --config x'"
    out = run_exit(v2.main)
    print(f"  [info] v2 same scenario: {out}, ranks after = {len(json.load(open(v2.WD_STATE))['ranks'])}")

    # second instance exits without touching anything
    sb = sandbox('main_single')
    mod = load('v3', 'orch', sb)
    import fcntl
    holder = open(mod.ORCH_LOCK, 'a')
    fcntl.flock(holder, fcntl.LOCK_EX | fcntl.LOCK_NB)
    with open(mod.WD_STATE, 'w') as fh:
        json.dump(st, fh)
    runner = f"{sb['sbx']}/second.py"
    with open(runner, 'w') as fh:
        fh.write(f"""import sys, types
sys.argv = ['x']
src = open({SRC['v3']['orch']!r}, encoding='utf-8').read()
src = src.replace('/inspire/hdd/project/ai4education/public/why', {sb['sbx'] + '/why'!r})
src = src.replace('/tmp/why_orch_s3h.lock', {mod.ORCH_LOCK!r}).replace('/tmp/why_wd_state.lock', {mod.WD_LOCK!r})
m = types.ModuleType('o'); exec(compile(src, 'orch', 'exec'), m.__dict__)
m.main()
""")
    r = subprocess.run([sys.executable, '-I', runner], capture_output=True, text=True, timeout=60)
    holder.close()
    check('second orchestrator instance exits 2 and leaves report/watchdog state untouched',
          r.returncode == 2 and not os.path.exists(f"{sb['POUTH']}/report_h100.md")
          and len(json.load(open(mod.WD_STATE))['ranks']) == 8, f'rc={r.returncode} out={r.stdout.strip()[:120]}')


# ------------------------------------------------------------------ D11 guard (v2 vs v3)
CONDS = ['base', 'rome_N', 'rome_T', 'rome_D', 'rome_P', 'rome_C', 'rome_B0P', 'rome_B1', 'rome_a0.5', 'rome_a2',
         'rome_a3', 'rome_samp', 'ike']
G10 = ['rome_B0P', 'rome_B1', 'rome_a0.5', 'rome_a2', 'rome_a3', 'ike', 'rome_samp']


def d11_fixture(sb):
    pj = sb['PROJH']
    files = [f'{pj}/results/rt/s2/r1qwen32b_s2_{c}_r{k}of8.jsonl' for c in CONDS for k in range(8)]
    files += [f'{pj}/results/rt/s2/r1qwen32b_s2h2b_{c}_r{k}of8.jsonl' for c in ('base', 'rome_N') for k in range(8)]
    lines = []
    for p in files:
        with open(p, 'w') as fh:
            fh.write(json.dumps({'_meta': True, 'mock': os.path.basename(p)}) + '\n' + '{"mock": 1}\n' * 3)
        lines.append(f'{hashlib.sha256(open(p, "rb").read()).hexdigest()}  {p}')
    lines.append(f'{"0" * 64}  {sb["sbx"]}/why/why-arr/results/rt/s2/r1qwen7b_s2smoke_base_r0of1.jsonl')
    lines.append('stopped: MOCK entry for local tests')
    ent = f"{sb['POUTH']}/parent_end_of_generation.txt"
    with open(ent, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    return files, hashlib.sha256(open(ent, 'rb').read()).hexdigest()


def scen_d11():
    print('\n== D11 guard (registered parent shards) across a window-2 restart')
    for ver in ('v2', 'v3'):
        sb = sandbox(f'd11_{ver}')
        mod = load(ver, 'orch', sb)
        files, esha = d11_fixture(sb)
        mod.D11_ENTRY_SHA = esha
        out0 = run_exit(mod.registered_parent_intact, 'S3H-§8')
        if ver == 'v3':
            out1 = run_exit(mod.mark_parent2_started, "S3H-§8 G10'")
        g10 = [p for p in files if any(f'_s2_{c}_r' in p for c in G10)]
        for p in g10:                                      # G10' resume appends rows by design
            with open(p, 'a') as fh:
                fh.write('{"mock": "window2"}\n')
        out2 = run_exit(mod.registered_parent_intact, 'S3H-§8')
        if ver == 'v3':
            check('v3 intact before window 2', out0[0] == 'ok' and len(out0[1]) == 120, str(out0[0]))
            check('v3 PARENT2_STARTED written before G10\'', out1[0] == 'ok' and mod.marker('PARENT2_STARTED'), str(out1))
            check(f'v3 restart after G10\' appended to {len(g10)} registered shards passes (append-only)', out2[0] == 'ok', str(out2[0]))
            victim = [p for p in files if '_s2_rome_T_r3' in p][0]
            b = bytearray(open(victim, 'rb').read())
            b[5] ^= 1
            open(victim, 'wb').write(bytes(b))
            out3 = run_exit(mod.registered_parent_intact, 'S3H-§8')
            check('v3 a byte changed inside a registered prefix halts', out3[0] == 'halt', str(out3))
            b[5] ^= 1
            open(victim, 'wb').write(bytes(b))
            g = [p for p in files if '_s2_ike_r2' in p][0]
            open(g, 'wb').write(open(g, 'rb').read()[:20])
            out4 = run_exit(mod.registered_parent_intact, 'S3H-§8')
            check('v3 a truncated G10\' shard halts', out4[0] == 'halt', str(out4))
            os.remove(mod.P2_START)
            out5 = run_exit(mod.registered_parent_intact, 'S3H-§8')
            check('v3 without PARENT2_STARTED any change halts (full hash)', out5[0] == 'halt', str(out5))
        else:
            print(f"  [info] v2: before window 2 {out0[0]}; restart after G10' appended -> {out2}")


# ------------------------------------------------------------------ G3'' smoke reading -> parent2 entry (v3)
def scen_g3():
    print("\n== G3'' smoke reading provenance and parent2 entry (v3)")
    sb = sandbox('g3')
    mod = load('v3', 'orch', sb)
    files, esha = d11_fixture(sb)
    mod.D11_ENTRY_SHA = esha
    pj = sb['PROJH']
    with open(f'{pj}/experiments/rt/study2_r1llama70b_eff.yaml', 'w') as fh:
        fh.write('model:\n  device_map: auto\n')
    real_sh = mod.sh

    def sh(cmd, timeout=1800):
        if 'rt.run' in cmd and 's2smoke' in cmd:
            for c in ('base', 'rome_N'):
                with open(f'{pj}/results/rt/s2/r1llama70b_s2smoke_{c}_r0of8.jsonl', 'w') as fh:
                    fh.write(json.dumps({'_meta': True}) + '\n')
                    for i in range(4):
                        fh.write(json.dumps({'case_id': f'k{i // 2}', 'probe': 'efficacy', 'budget': ['B0', 'B3'][i % 2]}) + '\n')
            return subprocess.CompletedProcess(cmd, 0, 'rc=0\n', '')
        return real_sh(cmd, timeout)
    mod.sh = sh
    go = f"{sb['SHARE']}/G3_SMOKE_GO"
    open(go, 'w').close()                                  # touched, but no reading note yet

    def write_note():
        _time.sleep(1.0)
        with open(go, 'w') as fh:
            fh.write('reader=executor-agent utc=2026-10-20T01:02:03Z verdict=coherent (mock)\n')
    th = threading.Thread(target=write_note)
    th.start()
    out = run_exit(mod.g3_smoke)
    th.join()
    rp = report(sb)
    reading = open(mod.G3_READING).read() if os.path.exists(mod.G3_READING) else ''
    check('empty G3_SMOKE_GO is not accepted (one ⏸ prompt), the note is then accepted', out[0] == 'ok'
          and rp.count('存在但为空') == 1, str(out))
    check('report credits the executor, never "leader 复核通过"', 'executor agent（leader 未读） 判定通过' in rp
          and 'leader 复核通过' not in rp and '待 leader 裁定' not in rp)
    shas = [hashlib.sha256(open(f'{pj}/results/rt/s2/r1llama70b_s2smoke_{c}_r0of8.jsonl', 'rb').read()).hexdigest()
            for c in ('base', 'rome_N')]
    check('reading record has shards+sha256, executor-not-leader, GO mtime and the note',
          all(s in reading for s in shas) and 'executor agent' in reading and 'mtime' in reading
          and 'verdict=coherent' in reading, reading[:200])
    out = run_exit(mod.parent2_end)
    pe = f"{sb['POUTH']}/parent2_end_of_generation.txt"
    lines = open(pe).read().splitlines() if os.path.exists(pe) else []
    check('parent2 entry = sha256 lines, then the reading line, then the stopped line',
          out[0] == 'ok' and len(lines) >= 3 and lines[-2].startswith('G3pp 70B smoke reading')
          and lines[-1].startswith('stopped: second window') and mod.marker('PARENT2_END')
          and os.path.isdir(f"{sb['POUTH']}/results/rt/s2_window2"), f'{out} tail={lines[-2:]}')
    sb2 = sandbox('g3_missing')
    mod2 = load('v3', 'orch', sb2)
    f2, e2 = d11_fixture(sb2)
    mod2.D11_ENTRY_SHA = e2
    out = run_exit(mod2.parent2_end)
    check('parent2_end halts when the reading record is missing', out[0] == 'halt'
          and not os.path.exists(f"{sb2['POUTH']}/parent2_end_of_generation.txt"), str(out))


# ------------------------------------------------------------------ watchdog lock / heartbeat / hang restart
def kill_tree(p):
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except Exception:
        pass
    subprocess.run(['pkill', '-f', f'{WORK}/sbx/'], capture_output=True)


def scen_watchdog():
    print('\n== watchdog: shared lock while nvidia-smi hangs; orchestrator lock deadline; heartbeat; hang restart')
    for ver in ('v2', 'v3'):
        sb = sandbox(f'wd_{ver}')
        orch = load('v3', 'orch', sb)                       # the orchestrator side under test is always v3's _WdLock
        orch.WD_LOCK_MAX_S = 6
        with open(orch.WD_STATE, 'w') as fh:
            json.dump({'ranks': []}, fh)
        wd_src = rewrite(open(SRC[ver]['wd'], encoding='utf-8').read(), sb['sbx'])
        wd_path = f"{sb['sbx']}/watchdog_{ver}.py"
        with open(wd_path, 'w') as fh:
            fh.write(wd_src)
        env = dict(os.environ, PATH=f"{sb['bin']}:{os.environ['PATH']}", FAKE_SMI_HANG='1')
        p = subprocess.Popen([sys.executable, '-I', wd_path], env=env, start_new_session=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _time.sleep(2.0)
        t0 = _time.time()
        out = run_exit(lambda: orch._WdLock().__enter__().__exit__())
        dt = _time.time() - t0
        kill_tree(p)
        if ver == 'v3':
            check('v3 watchdog: orchestrator gets the shared lock while nvidia-smi hangs', out[0] == 'ok' and dt < 3,
                  f'{out} after {dt:.1f}s')
        else:
            check('v2 watchdog + v3 orchestrator: lock held by hung nvidia-smi -> bounded ⏸ (WD-LOCK), not a silent stall',
                  out[0] == 'halt' and 'WD-LOCK' in report(sb), f'{out} after {dt:.1f}s')
    # heartbeat with a hung nvidia-smi
    for ver in ('v2', 'v3'):
        sb = sandbox(f'hb_{ver}')
        subs = (("'timeout -k 10 60 nvidia-smi", "'timeout -k 1 3 nvidia-smi"),) if ver == 'v3' else ()
        src = rewrite(open(SRC[ver]['orch'], encoding='utf-8').read(), sb['sbx'])
        for a, b in subs:
            src = src.replace(a, b)
        tmpmod = types.ModuleType('h')
        exec(compile(src, 'orch', 'exec'), tmpmod.__dict__)

        class Stop(BaseException):
            pass

        class HbTime(TimeShim):
            n = 0
            def sleep(self, s):
                HbTime.n += 1
                if HbTime.n > 1:
                    raise Stop()
        tmpmod.time = HbTime()
        old_path, old_env = os.environ['PATH'], os.environ.get('FAKE_SMI_HANG')
        os.environ['PATH'] = f"{sb['bin']}:{old_path}"
        os.environ['FAKE_SMI_HANG'] = '1'
        def tgt():
            try:
                tmpmod.hourly()
            except BaseException:
                pass
        th = threading.Thread(target=tgt, daemon=True)
        th.start()
        th.join(15)
        os.environ['PATH'] = old_path
        os.environ.pop('FAKE_SMI_HANG', None)
        rp = report(sb)
        subprocess.run(['pkill', '-f', f'{sb["bin"]}/nvidia-smi'], capture_output=True)
        subprocess.run(['pkill', '-f', 'sleep 600.123'], capture_output=True)
        if ver == 'v3':
            check('v3 hourly heartbeat is written while nvidia-smi hangs', '## ORCH heartbeat ✓' in rp, rp.strip()[-160:])
        else:
            print(f"  [info] v2 hourly with hung nvidia-smi: heartbeat written within 15 s = {'## ORCH' in rp}")
    # hang detection + restart still works with the v3 watchdog
    sb = sandbox('wd_restart')
    wd = load('v3', 'wd', sb)
    wd.GRACE_S, wd.ZERO_LIMIT = 5, 2
    os.environ['PATH'] = f"{sb['bin']}:{os.environ['PATH']}"
    cmd = "cd /tmp || exit 1; nohup sleep 300.321 > /dev/null 2>&1 < /dev/null & echo NEWPID=$!"
    r = subprocess.run(['bash', '-c', cmd], capture_output=True, text=True)
    pid0 = int(r.stdout.strip().split('=')[1])
    st = {'ranks': [{'type': 'R', 'project': 'MOCK', 'rank': 0, 'world': 8, 'pid': pid0, 'gpus': [0],
                     'zero_streak': 0, 'outglob': '', 'log': f"{sb['sbx']}/r0.log", 'cmd': cmd, 'restarts': 0,
                     'started_at': 0, 'status': 'running'}]}
    with open(wd.STATE, 'w') as fh:
        json.dump(st, fh)
    th = threading.Thread(target=wd.main, daemon=True)
    th.start()
    t0 = _time.time()
    new = None
    while _time.time() - t0 < 40:
        try:
            rk = json.load(open(wd.STATE))['ranks'][0]
            if rk.get('restarts', 0) >= 1 and rk.get('status') == 'running' and rk.get('pid') != pid0:
                new = rk
                break
        except Exception:
            pass
        _time.sleep(0.2)
    check('v3 watchdog still detects a 0% hang, kills it and restarts with the stored command',
          new is not None and not pid_alive_mac(pid0) and pid_alive_mac(new['pid'])
          and _time.time() - new['started_at'] < 60, f"new={new and (new['pid'], new['restarts'], new['status'])}")
    if new:
        # stop the loop from restarting again: mark stopped, then kill the mock sleeper
        with open(wd.STATE, 'w') as fh:
            json.dump({'ranks': []}, fh)
    subprocess.run(['pkill', '-f', 'sleep 300.321'], capture_output=True)


if __name__ == '__main__':
    FAKE_DELTAS = fake_deltas_module()
    os.environ['PATH'] = os.environ['PATH']
    for nm, fn in (('deltas', scen_deltas), ('main', scen_main), ('d11', scen_d11), ('g3', scen_g3),
                   ('watchdog', scen_watchdog)):
        if not ONLY or nm in ONLY:
            fn()
    os.chdir(WORK)
    bad = [r for r in RESULTS if not r[1]]
    print(f"\nSUMMARY: {len(RESULTS) - len(bad)}/{len(RESULTS)} checks passed")
    for r in bad:
        print(f"  FAILED: {r[0]} -- {r[2]}")
    sys.exit(1 if bad else 0)
