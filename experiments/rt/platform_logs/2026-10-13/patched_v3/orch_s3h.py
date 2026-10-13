#!/usr/bin/env python3
"""S3-H overnight orchestrator (tmux unavailable offline; runs detached via nohup setsid).

执行单 S3-H 全流程自动执行。任何校验失败 -> 写 ⏸ 块到 report_h100.md 并退出（不重试、不硬闯、不删改数据）。
§0 裁决: error 行按意图判通过（每个 case 有 valid 行即可）。
补跑阶梯(§1.4): 首跑 40000(70B 34000) -> 续跑 26000 -> 18000。
Study 3 与父研究(s2/s2smoke 分片)内容禁读；只看行数/error 行数/GPU/进度行。例外（S3-H v2 修订 3/4）:
§6 冒烟(results/rt/s3smoke/, 旧事实)在 §3 之前跑；executor agent 或 leader 判英文连贯后 touch $SHARE/S3_SMOKE_GO，
§3–§5 照常进行，§7 前等 GO。§8.1 70B 冒烟: 代码只计行数；executor agent（非 leader）读 2 个 case 判连贯，把读取记录
写进 $SHARE/G3_SMOKE_GO，parent2 条目记录该读取。
单实例: /tmp/why_orch_s3h.lock；第二个实例不碰任何状态直接退出。
"""
import subprocess, time, os, sys, json, glob, re, threading, traceback, signal, fcntl, shlex, hashlib, ast

PROJH = '/inspire/hdd/project/ai4education/public/why/why-arr-h100'
POUTH = '/inspire/hdd/project/ai4education/public/why/platform_out_h100'
SHARE = '/inspire/hdd/project/ai4education/public/why/xfer'
P4090 = '/inspire/hdd/project/ai4education/public/why/why-arr'
GP = '/inspire/hdd/global_public/public_models'
M32 = f'{GP}/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B'
M70 = f'{GP}/deepseek-ai/DeepSeek-R1-Distill-Llama-70B'
BUNDLE = f'{SHARE}/s3_code_full.bundle'
BUNDLE_SHA = 'fdbcafa8a1efd86daf0cd1816ac96b6cda839bb2078073f049cfe1caacd4303f'
FREEZE_BASE = '4b75d08'
EXPECT_HEAD = '0be89c6'
ENV_OFF = 'export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_DATASETS_OFFLINE=1 PIP_NO_INDEX=1'
FROZEN_LIST = ('prereg-arr-addendum-s3.md src/rt src/study3/confirm.py src/study3/end_entry.py '
               'src/study3/ext_manifest.py src/study3/tests '
               'experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl '
               'experiments/rt/pools/study3/candidates.jsonl '
               'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml experiments/rt/deltas_s3_r1qwen32b_ext.yaml '
               'experiments/rt/study3_r1qwen32b_fresh.yaml experiments/rt/study3_r1qwen32b_ext.yaml '
               'experiments/rt/study3_smoke.yaml experiments/rt/pool_screen_s3.yaml')
REPORT = f'{POUTH}/report_h100.md'
STATE = f'{POUTH}/orch_state.json'
RT_LADDER = [40000, 26000, 18000]
RT70_LADDER = [34000, 26000, 18000]
CUR = {'phase': 'init', 'detail': 'started'}
WD_STATE = f'{POUTH}/watchdog_state.json'
WD_LOCK = '/tmp/why_wd_state.lock'          # node-local; watchdog.py uses the same path
LAUNCH_TIMEOUT = 120
H100_NAME = 'NVIDIA H100 80GB HBM3'         # report_h100.md H0a
D11_ENTRY = f'{POUTH}/parent_end_of_generation.txt'
D11_ENTRY_SHA = 'b192435ae7c98b41638b7a49c3fed86d464aa53d9ff123e485dfbd2ebe583b62'   # registry entry 10
S3_KEYS = {f'{c}/{p}/{b}' for c in ('base', 'rome_N') for p in ('efficacy', 'para0') for b in ('B0', 'B3')}
S3_MARKERS = ('S3_CODE_OK', 'S3_D_SMOKE_OK', 'S3_D_SMOKE_W4_OOM', 'S3_D_FRESH_DONE', 'S3_EXT_MANIFEST.txt',
              'S3_EXT_MANIFEST_DONE', 'S3_D_EXT_DONE', 'S3_SMOKE_DONE', 'S3_SMOKE_GO', 'S3_SMOKE_NOGO',
              'S3_G_FRESH_DONE', 'S3_G_EXT_DONE', 'S3_END')
W2_MARKERS = ('G3_SMOKE_GO', 'G3_SMOKE_NOGO', 'PARENT2_STARTED', 'PARENT2_END')   # second window (D11); never PARENT_END
ORCH_LOCK = '/tmp/why_orch_s3h.lock'      # node-local single-instance guard
WD_LOCK_MAX_S = 900                       # longest legitimate watchdog hold is its 120 s restart command
G3_READING = f'{POUTH}/g3_smoke_reading.txt'
P2_START = f'{SHARE}/PARENT2_STARTED'
_ORCH_FH = None
RT_PGREP = 'pgrep -af "rt[.](run|pool|deltas)" || true'

def log(msg):
    print(f"[{time.strftime('%F %T')}] {msg}", flush=True)

def utc():
    return time.strftime('%F %T', time.gmtime())

def rep(first_line, body):
    with open(REPORT, 'a') as f:
        f.write(f"\n{first_line}\n{body}\n")
    log(f"REPORT {first_line}")

def save_cur():
    try:
        with open(STATE, 'w') as f:
            json.dump({**CUR, 'ts': utc()}, f, ensure_ascii=False, indent=1)
    except Exception:
        pass

def halt(item, msg, tb=''):
    body = f"待裁决：{msg}\n（orchestrator 夜间自动停止，不重试不硬闯；时间 {utc()} UTC）"
    if tb:
        body += "\n```\n" + tb[-2000:] + "\n```"
    try:
        rep(f"## {item} ⏸ {utc()}", body)
    except Exception as e:
        log(f"REPORT WRITE FAILED in halt: {e}")
    CUR['phase'] = f'HALTED@{item}'
    save_cur()
    log(f"HALT {item}: {msg}" + (f"\n{tb[-2000:]}" if tb else ''))
    sys.exit(1)

def sh(cmd, timeout=1800):
    p = subprocess.Popen(['bash', '-c', cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)       # bash and its foreground python share pgid = p.pid
        except ProcessLookupError:
            pass
        p.communicate()
        raise
    return subprocess.CompletedProcess(p.args, p.returncode, out, err)

def sh_out(cmd, timeout=1800):
    r = sh(cmd, timeout)
    return r.stdout.strip(), r.returncode

def pid_alive(pid):
    """True iff /proc/<pid> exists and is not a zombie."""
    try:
        with open(f'/proc/{int(pid)}/stat') as f:
            return f.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except Exception:
        return False

def launch(cmd, item, what):
    """Run a background launch line (simple command `... & echo NEWPID=$!`); returns the worker pid."""
    out, rc = sh_out(cmd, LAUNCH_TIMEOUT)
    m = re.search(r'^NEWPID=(\d+)$', out, re.M)
    if not m:
        halt(item, f'{what} 启动失败 rc={rc} out={out[:200]}')
    return int(m.group(1))

def wait_gpus_free(timeout_s=1200):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        out, _ = sh_out('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits')
        vals = [int(x) for x in out.split() if x.strip().isdigit()]
        if len(vals) == 8 and all(v < 1024 for v in vals):
            return True
        time.sleep(10)
    return False

def gpu_mem(gpus):
    idx = ','.join(str(g) for g in gpus)
    out, _ = sh_out(f'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i {idx}')
    return [int(x) for x in out.split() if x.strip().isdigit()]

def cards_free(gpus, item):
    for g in gpus:
        m = gpu_mem([g])
        if len(m) != 1 or m[0] >= 1024:
            halt(item, f'GPU {g} memory.used={m} (nvidia-smi 失败或 >=1GB) 启动前置不满足')

def assert_gpus_free(gpus, item):
    """§1.2, once per launch batch (never inside a per-rank launch loop: pgrep is node-wide)."""
    cards_free(gpus, item)
    out, _ = sh_out(RT_PGREP)
    if out:
        halt(item, f'pgrep rt.(run|pool|deltas) 非空: {out[:300]}')

def assert_h100(item):
    out, rc = sh_out('nvidia-smi --query-gpu=name --format=csv,noheader')
    names = [l.strip() for l in out.splitlines() if l.strip()]
    if rc != 0 or len(names) != 8 or any(n != H100_NAME for n in names):
        halt(item, f'GPU 非 8×{H100_NAME}（D9；换硬件须 leader 先记偏差）: rc={rc} {names}')
    return names

class _WdLock:
    """Shared with watchdog.py. Bounded: a lock held longer than WD_LOCK_MAX_S halts (⏸) instead of stalling silently."""
    def __enter__(self):
        self.fh = open(WD_LOCK, 'a')
        t0 = time.time()
        while True:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() - t0 > WD_LOCK_MAX_S:
                    self.fh.close()
                    halt('WD-LOCK', f'{WD_LOCK} 被占用 >{WD_LOCK_MAX_S}s（看门狗卡住？nvidia-smi 挂起？）；看门狗状态无法更新')
                time.sleep(2)
    def __exit__(self, *a):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()

def wd_load():
    try:
        with open(WD_STATE) as f:
            st = json.load(f)
        if isinstance(st, dict) and isinstance(st.get('ranks'), list):
            return st
    except Exception:
        pass
    return {"ranks": []}

def wd_save(st):
    tmp = WD_STATE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, WD_STATE)

def update_watchdog(project, entries):
    with _WdLock():
        prev = {(rk.get('project'), rk.get('rank')): rk.get('restarts', 0) for rk in wd_load()['ranks']}
        ranks = []
        for e in entries:
            ranks.append({"type": "R", "project": project, "rank": e['rank'], "world": e.get('world', 8),
                          "pid": e['pid'], "gpus": e['gpus'], "zero_streak": 0,
                          "outglob": e.get('outglob', ''), "log": e.get('log', ''),
                          "cmd": e['cmd'], "restarts": prev.get((project, e['rank']), 0),
                          "started_at": time.time(), "status": "running"})
        wd_save({"ranks": ranks, "note": "watchdog v3 GPU util rule"})

def wd_pause_all():
    with _WdLock():
        st = wd_load()
        for rk in st['ranks']:
            rk['status'] = 'stopped'
        wd_save(st)

def wait_all_exit(entries, project, poll=60, stale_hours=10, item=None):
    """Adopt watchdog restarts; a 'restarting' rank counts as alive; halt on a watchdog pause; return True only
    when no tracked rank is alive and no rt process is left."""
    item = item or project
    t0, orphan_since = time.time(), None
    while True:
        with _WdLock():
            st = wd_load()
        restarting = []
        for rk in st['ranks']:
            if rk.get('project') != project:
                continue
            for e in entries:
                if rk.get('rank') != e['rank']:
                    continue
                if rk.get('status') == 'paused':
                    halt(item, f"看门狗第 4 次卡死停项（H-2）: rank {e['rank']}；不进入阶梯/重跑，待 leader 裁决")
                if rk.get('status') == 'restarting':
                    restarting.append(e['rank'])
                if rk.get('pid') and rk['pid'] != e['pid'] and pid_alive(rk['pid']):
                    e['pid'] = rk['pid']
                    e['cmd'] = rk.get('cmd', e['cmd'])
        alive = sorted(set([e['rank'] for e in entries if pid_alive(e['pid'])] + restarting))
        rt_ps, _ = sh_out(RT_PGREP)
        CUR['detail'] = f"{project}: alive ranks {alive}; rt procs {len(rt_ps.splitlines()) if rt_ps else 0}"
        save_cur()
        if not alive:
            if not rt_ps:
                return True
            orphan_since = orphan_since or time.time()
            if time.time() - orphan_since > 900:
                halt(item, f'登记 rank 均已退出但仍有 rt 进程（未登记/孤儿）: {rt_ps[:300]}')
        else:
            orphan_since = None
        if time.time() - t0 > stale_hours * 3600:
            return False
        time.sleep(poll)

def exit_ok(logpath):
    try:
        with open(logpath, errors='replace') as f:
            txt = f.read()
        return ('[rt.run] done' in txt) or ('done:' in txt)
    except Exception:
        return False

def screen_ok(logpath):
    """rt.pool screen ends by printing execute()'s dict, e.g. {'screen': 200} (src/rt/pool.py:326)."""
    try:
        with open(logpath, errors='replace') as f:
            return re.search(r"\{'screen': \d+\}\s*$", f.read(), re.M) is not None
    except Exception:
        return False

def only_err_cases(path):
    okc, errc = set(), set()
    try:
        with open(path, errors='replace') as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get('error'):
                    if d.get('case_id'):
                        errc.add(d['case_id'])
                elif d.get('case_id') and d.get('probe'):
                    okc.add(d['case_id'])
    except FileNotFoundError:
        pass
    return len(errc - okc)

def rank_incomplete(entries, globpats):
    """globpats: patterns with {rank} placeholder; sums onlyErr over matched files."""
    bad = []
    for e in entries:
        if not exit_ok(e['log']):
            bad.append((e['rank'], 'no-done-line'))
            continue
        files = []
        for gp in globpats:
            files += glob.glob(gp.format(rank=e['rank']))
        tot = sum(only_err_cases(f) for f in files)
        if tot > 0:
            bad.append((e['rank'], f'onlyErr={tot}'))
    return bad

def ladder_tokens(seq, idx):
    return seq[idx] if idx < len(seq) else None

def relaunch_rank(project, e, tokens):
    with _WdLock():
        st = wd_load()
    for rk in st['ranks']:
        if rk.get('project') == project and rk.get('rank') == e['rank'] and rk.get('status') in ('paused', 'restarting'):
            halt(project, f"rank {e['rank']} 看门狗状态 {rk.get('status')}，不做阶梯续跑")
    try:
        os.replace(e['log'], e['log'] + f".pre_{time.strftime('%Y%m%d_%H%M%S')}")
    except Exception:
        pass
    newcmd = re.sub(r'--max-batch-tokens \d+', f'--max-batch-tokens {tokens}', e['cmd'])
    newpid = launch(newcmd, project, f"rank {e['rank']} 阶梯续跑")
    e['pid'] = newpid
    e['cmd'] = newcmd
    with _WdLock():
        st = wd_load()
        for rk in st['ranks']:
            if rk.get('project') == project and rk.get('rank') == e['rank']:
                rk.update(pid=newpid, cmd=newcmd, zero_streak=0, started_at=time.time(), status='running')
        wd_save(st)
    log(f"{project} rank {e['rank']} relaunched tokens={tokens} pid={newpid}")

def start_rt_ranks(project, world, cmd_tpl, log_tpl, outglob_tpl, gpus_of_rank=None, tokens=40000):
    pids, entries = [], []
    for r in range(world):
        gpus = gpus_of_rank(r) if gpus_of_rank else [r]
        gpu_s = ','.join(str(g) for g in gpus)
        cmd = cmd_tpl.format(rank=r, tokens=tokens, gpus=gpu_s)
        logp = log_tpl.format(rank=r)
        rotate(logp)
        full = (f"cd {PROJH} || exit 1; {ENV_OFF}; unset WHYAAAI_DEVICE_MAP; "
                f"nohup env CUDA_VISIBLE_DEVICES={gpu_s} {cmd} > {logp} 2>&1 < /dev/null & echo NEWPID=$!")
        newpid = launch(full, project, f'rank {r}')
        pids.append(newpid)
        entries.append({"rank": r, "pid": newpid, "gpus": gpus, "cmd": full, "log": logp,
                        "outglob": outglob_tpl.replace('{rank}', str(r)), "world": world})
        time.sleep(2)
    update_watchdog(project, entries)
    return pids, entries

def marker(name):
    return os.path.exists(f'{SHARE}/{name}')

def rotate(path):
    """Keep a previous run's log as evidence instead of truncating it with `>`."""
    if os.path.exists(path):
        try:
            os.replace(path, path + f".pre_{time.strftime('%Y%m%d_%H%M%S')}")
        except OSError:
            pass

def touch_marker(name, item):
    if sh(f'touch {SHARE}/{name}').returncode != 0 or not marker(name):
        halt(item, f'touch {SHARE}/{name} 失败')

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

# ---------------- §2 ----------------

def phase_s2(resume=False):
    CUR['phase'] = 'S2 wait-bundle'; save_cur()
    while not os.path.exists(BUNDLE):
        time.sleep(60)
    CUR['phase'] = 'S2 sync'; save_cur()
    out, _ = sh_out(f'sha256sum {BUNDLE}')
    h = out.split()[0] if out else ''
    if h != BUNDLE_SHA:
        halt('S3H-§2', f'bundle sha256 mismatch: got {h} expect {BUNDLE_SHA}')
    names = assert_h100('S3H-§2')
    if not resume:
        stale = [m for m in S3_MARKERS + W2_MARKERS if marker(m)] + ([G3_READING] if os.path.exists(G3_READING) else [])
        if stale:
            halt('S3H-§2', f'无 S3_CODE_OK 却已有 Study 3/第二窗口标记 {stale}（陈旧标记会使阶段被跳过或绕过人工门）')
        sh('pkill -f "python3? -m [r]t[.](run|pool|deltas)" || true')
        time.sleep(5)
        sh('pkill -9 -f "python3? -m [r]t[.](run|pool|deltas)" || true')
        if not wait_gpus_free():
            halt('S3H-§2', "pkill G10' 后 20 分钟内 8 卡未全部 <1GB")
        wd_pause_all()
        rep(f"## S3H-§2 G10'-stop ✓ {utc()}",
            f"- G10' 进程已全部停止（不删除任何分片），8 卡 <1GB；bundle sha256 校验通过；GPU 8×{names[0]}")
    else:
        rt_ps, _ = sh_out(RT_PGREP)
        if rt_ps:
            halt('S3H-§2 resume', f'续跑启动时仍有上一轮遗留 rt 进程（非污染信号，待 leader 裁决）: {rt_ps[:300]}')
        if not wait_gpus_free():
            halt('S3H-§2 resume', '8 卡未全部 <1GB')
    os.chdir(PROJH)
    out, rc = sh_out('git status --porcelain --untracked-files=no')
    if out:
        halt('S3H-§2', f'git status dirty: {out[:300]}')
    if not resume:
        g = sh(f'git fetch {BUNDLE} claude/paper-review-understanding-8732e6:refs/remotes/bundle/s3', 600)
        if g.returncode != 0:
            halt('S3H-§2', f'git fetch bundle failed rc={g.returncode}: {g.stderr.strip()[-400:]}')
        g = sh('git checkout -B claude/paper-review-understanding-8732e6 refs/remotes/bundle/s3', 600)
        if g.returncode != 0:
            halt('S3H-§2', f'git checkout -B failed rc={g.returncode}: {g.stderr.strip()[-400:]}')
    head, _ = sh_out('git log -1 --format=%h')
    if head != EXPECT_HEAD:
        halt('S3H-§2', f'HEAD={head} expect {EXPECT_HEAD}')
    if sh(f'git merge-base --is-ancestor {FREEZE_BASE} HEAD').returncode != 0:
        halt('S3H-§2', 'freeze commit not in history')
    g = sh(f'git diff --stat {FREEZE_BASE} HEAD -- {FROZEN_LIST}')
    if g.returncode != 0:
        halt('S3H-§2', f'git diff rc={g.returncode}: {g.stderr.strip()[-400:]}')
    diff = g.stdout
    if diff.strip():
        halt('S3H-§2', f'frozen files changed:\n{diff[:800]}')
    r = sh(f'{ENV_OFF} && PYTHONPATH=src python3 src/rt/tests/run_all.py > /tmp/t.log 2>&1; echo exit=$?', 3600)
    tail = sh_out('tail -1 /tmp/t.log')[0]
    if 'exit=0' not in r.stdout or '193 passed' not in tail:
        halt('S3H-§2', f'rt tests failed: tail={tail}')
    r2 = sh(f'{ENV_OFF} && PYTHONPATH=src python3 -m unittest study3.tests.test_confirm > /tmp/t2.log 2>&1; echo rc=$?', 1800)
    if 'rc=0' not in r2.stdout:
        halt('S3H-§2', f'study3.tests.test_confirm failed: {sh_out("tail -5 /tmp/t2.log")[0][:400]}')
    out, _ = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -c \"import json;from rt import run;"
                    f"h=json.loads(open('results/rt/s2/r1qwen32b_s2_base_r0of8.jsonl').readline());"
                    f"print('CODE_HASH_OK' if run.code_sha256()==h['code_sha256'] else 'CODE_HASH_MISMATCH')\"")
    if 'CODE_HASH_OK' not in out:
        halt('S3H-§2', f'CODE_HASH check: {out[:200]}')
    # §2.9 as amended: the lean import path rt.deltas actually uses (a bare `import easyeditor` fails on NGC by design)
    ee, rc = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src:source/EasyEdit python3 -c "
                    f"\"from rt.deltas import ensure_easyedit_importable as f; s=f(); import easyeditor; "
                    f"easyeditor.BaseEditor; easyeditor.ROMEHyperParams; "
                    f"from easyeditor.models.rome import rome_main; print('EASYEDIT' + '_OK', s)\" 2>&1", 1800)
    ee_ok = [l for l in ee.splitlines() if l.startswith('EASYEDIT_OK')]
    if rc != 0 or not ee_ok:
        halt('S3H-§2', f'EasyEdit lean import 失败 rc={rc}（不跳到 §8：D10 父项在 Study 3 之后）: {ee[-400:]}')
    if not resume:
        out, _ = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -c \"import json,os;"
                        f"ids=[json.loads(l)['case_id'] for l in open('experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl')];"
                        f"print('existing fresh deltas:',sum(os.path.exists(f'deltas/r1qwen32b/ROME/cf/{{c}}.pt') for c in ids))\"")
        if 'existing fresh deltas: 0' not in out:
            halt('S3H-§2', f'fresh deltas not clean: {out[:200]}')
        if os.path.exists(f'{PROJH}/results/rt/s3') or os.path.exists(f'{PROJH}/results/rt/pool_s3'):
            halt('S3H-§2', 'results/rt/s3 or results/rt/pool_s3 already exists')
        if sh(f"echo '{BUNDLE_SHA} {head} {utc()}' > {SHARE}/S3_CODE_OK").returncode != 0:
            halt('S3H-§2', 'S3_CODE_OK 写入失败')
        rep(f"## S3H-§2 ✓ {utc()}",
            f"- bundle sha256 OK; HEAD={head}; freeze-in-history; 冻结清单无改动; rt tests 193 passed; study3.tests.test_confirm OK; CODE_HASH_OK; fresh deltas=0; s3/pool_s3 不存在\n"
            f"- EasyEdit lean import: {ee_ok[0][:200]}\n"
            f"- GPU: 8×{names[0]}\n"
            f"- touch {SHARE}/S3_CODE_OK")
    else:
        rec = open(f'{SHARE}/S3_CODE_OK').read().split()
        if not rec or rec[0] != BUNDLE_SHA:
            halt('S3H-§2 resume', f'S3_CODE_OK 内容与 bundle 不符: {rec[:2]}')
        rep(f"## S3H-§2 resume ✓ {utc()}",
            f"- S3_CODE_OK 已在: 跳过 §2.2 pkill / §2.4 checkout / §2.10（按设计）；HEAD={head}、冻结、测试、CODE_HASH、EasyEdit 复核通过；GPU 8×{names[0]}")

# ---------------- §3/§5 deltas ----------------

def parse_summarize(txt):
    """rt.deltas summarize prints one json.dumps(..., indent=1) object; tolerate stray lines before it."""
    cands = [txt]
    i = txt.rfind('\n{')
    if i >= 0:
        cands.append(txt[i + 1:])
    for c in cands:
        try:
            d = json.loads(c)
            if isinstance(d, dict):
                return d
        except Exception:
            pass
    d = {}
    for k in ('cases', 'ok', 'errors', 'editor_nan', 'max_rank', 'max_rel_err', 'median_p_target_after'):
        m = re.search(rf'"?{k}"?\s*[:=]\s*([0-9.eE+-]+)', txt)
        if m:
            d[k] = m.group(1)
    return d if d else None

def fnum(d, k):
    try:
        return float(d.get(k))
    except Exception:
        return None

def edit_world():
    """World chosen by the §3 smoke (D9a), recorded in S3_D_SMOKE_OK; §5 inherits it. Absent -> 4; unreadable -> ⏸."""
    p = f'{SHARE}/S3_D_SMOKE_OK'
    if not os.path.exists(p):
        return 4
    try:
        tok = open(p).read().split()[0]
    except Exception as ex:
        halt('S3H-§3/§5', f'S3_D_SMOKE_OK 不可读: {type(ex).__name__}: {ex}')
    if tok not in ('world=2', 'world=4'):
        halt('S3H-§3/§5', f'S3_D_SMOKE_OK 首字段 {tok!r} 不是 world=2/world=4')
    return 2 if tok == 'world=2' else 4

def deltas_phase(tag, cfg, expect_n, item, smoke=True, world=4):
    CUR['phase'] = item; save_cur()
    sub = tag                                  # config log_dir is results/rt/deltas_logs/<tag>
    lp = {'s3fresh': 's3d_fresh', 's3ext': 's3d_ext'}[tag]
    env = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; "
           f"unset WHYAAAI_DTYPE WHYAAAI_MODEL")
    def gpus_of(r):
        return [2*r, 2*r+1] if world == 4 else [4*r+i for i in range(4)]
    def oom_in(path):
        try:
            t = open(path, errors='replace').read()
        except FileNotFoundError:
            return False
        return ('OutOfMemoryError' in t) or ('CUDA out of memory' in t)
    logdir = f'{PROJH}/results/rt/deltas_logs/{sub}'
    def logs_of(w):
        return sorted(glob.glob(f'{logdir}/r1qwen32b_ROME_cf_r*of{w}.jsonl'))
    def run_summarize(expect_files=None, own_only=False):
        own = logs_of(world)
        if not own or (expect_files is not None and len(own) != expect_files):
            halt(item, f'summarize 日志数 {len(own)} (world {world}, 期望 {expect_files})')
        # D9(a) fallback at world 2: a world-4 smoke case edited before the OOM keeps its delta file, and every world-2
        # run skips it without writing a row (deltas.py run_shard, skipped_existing), so its only ok row is in r0of4.
        # The world-4 logs go first: summarize keeps the latest row per case, so world-2 rows replace world-4 error rows.
        prior = [] if (world != 2 or own_only) else logs_of(4)
        r = sh(f"{env} && python3 -m rt.deltas summarize " + ' '.join(shlex.quote(p) for p in prior + own), 3600)
        if r.returncode != 0:
            halt(item, f'summarize rc={r.returncode}: {r.stderr.strip()[-400:]}')
        return r.stdout.strip()
    def done_counts(path):
        """The `[deltas] done: {...}` counts of a finished rt.deltas run (deltas.py cmd_run), or None."""
        try:
            m = re.findall(r"^\[deltas\] done: (\{.*\})\s*$", open(path, errors='replace').read(), re.M)
            return ast.literal_eval(m[-1]) if m else None
        except Exception:
            return None
    if smoke:
        def smoke_cmd(w, cards, logp):
            # --limit cuts the pool before sharding (deltas.py 987-989): 2*w gives rank 0 exactly 2 cases
            return (f"{env} && CUDA_VISIBLE_DEVICES={cards} python3 -m rt.deltas run --config {cfg} --model-path {M32} "
                    f"--model-parallel --rank 0 --world {w} --device 0 --limit {2*w} > {logp} 2>&1; echo rc=$?")
        smoke_log = f'{PROJH}/logs/rt/{lp}_smoke.out'
        w4_log = f'{logdir}/r1qwen32b_ROME_cf_r0of4.jsonl'
        rc = '0'
        if not marker('S3_D_SMOKE_W4_OOM'):
            assert_gpus_free([0, 1], item)
            r = sh(smoke_cmd(4, '0,1', smoke_log), 14400)
            rc = r.stdout.strip().split('rc=')[-1]
            # export_case turns an OOM in the edit into an error row with rc 0; an OOM at load exits non-zero.
            # Persist the outcome: a restart must not re-run world 4 (it would skip the error cases and print no OOM).
            if oom_in(smoke_log) or oom_in(w4_log):
                if sh(f"echo 'world4-smoke-OOM {utc()}' > {SHARE}/S3_D_SMOKE_W4_OOM").returncode != 0 \
                        or not marker('S3_D_SMOKE_W4_OOM'):
                    halt(item, 'S3_D_SMOKE_W4_OOM 写入失败')
        if marker('S3_D_SMOKE_W4_OOM'):
            rep(f"## {item} smoke-OOM-retry ⏸→run {utc()}", '- 冒烟 OOM（已记 S3_D_SMOKE_W4_OOM）-> 按 §3.1 改每进程 4 卡 world 2 再冒烟一次')
            world = 2
            smoke_log = f'{PROJH}/logs/rt/{lp}_smoke2.out'
            assert_gpus_free([0, 1, 2, 3], item)
            r = sh(smoke_cmd(2, '0,1,2,3', smoke_log), 14400)
            rc = r.stdout.strip().split('rc=')[-1]
            if rc != '0' or oom_in(smoke_log):
                halt(item, f'4卡 world2 冒烟仍失败 rc={rc}; tail: {sh_out(f"tail -5 {smoke_log}")[0][:400]}')
        elif rc != '0':
            halt(item, f'冒烟失败(非OOM) rc={rc}; tail: {sh_out(f"tail -5 {smoke_log}")[0][:400]}')
        s0 = run_summarize()
        d = parse_summarize(s0)
        if not d:
            halt(item, f'冒烟 summarize 无法解析: {s0[:400]}')
        qual = (fnum(d, 'editor_nan') == 0 and fnum(d, 'max_rel_err') is not None and fnum(d, 'max_rel_err') < 1e-4
                and fnum(d, 'median_p_target_after') is not None and fnum(d, 'median_p_target_after') >= 0.9)
        why = ''
        if world == 4:
            ok_n = fnum(d, 'ok') == 2
        else:
            # rank 0 of world 2 owns cases 0 and 2; case 0 may already carry a world-4 delta (skipped, no row).
            # The world-2 run itself must be error-free and account for both cases.
            cnt = done_counts(smoke_log)
            o2 = parse_summarize(run_summarize(own_only=True))
            ok_n = (isinstance(cnt, dict) and cnt.get('error') == 0 and cnt.get('skipped_error') == 0
                    and cnt.get('ok', 0) + cnt.get('skipped_existing', 0) == 2
                    and bool(o2) and not o2.get('errors') and fnum(o2, 'editor_nan') == 0
                    and (fnum(o2, 'ok') or 0) >= 1 and (fnum(d, 'ok') or 0) >= 2)
            why = f"; world2 冒烟计数 {cnt}; 仅 r*of2: ok={(o2 or {}).get('ok')} errors={(o2 or {}).get('errors')}"
        if not (ok_n and qual):
            halt(item, f'冒烟通过条件未满足: {json.dumps(d)[:400]}{why}')
        if sh(f"echo 'world={world} {utc()}' > {SHARE}/S3_D_SMOKE_OK").returncode != 0:
            halt(item, 'S3_D_SMOKE_OK 写入失败')
        rep(f"## {item} smoke ✓ {utc()}", f"- world={world}; summarize: {json.dumps(d)[:300]}")
    def launch_all(extra, suffix):
        es = []
        assert_gpus_free(sorted(g for rr in range(world) for g in gpus_of(rr)), item)
        for rr in range(world):
            gs = gpus_of(rr)
            gpu_s = ','.join(map(str, gs))
            logn = f'{lp}_r{rr}{suffix}.out'
            rotate(f'{PROJH}/logs/rt/{logn}')
            cmd = (f"cd {PROJH} || exit 1; {ENV_OFF}; export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; "
                   f"unset WHYAAAI_DTYPE WHYAAAI_MODEL; nohup env CUDA_VISIBLE_DEVICES={gpu_s} python3 -m rt.deltas run "
                   f"--config {cfg} --model-path {M32} --model-parallel --rank {rr} --world {world} --device 0{extra} "
                   f"> logs/rt/{logn} 2>&1 < /dev/null & echo NEWPID=$!")
            pid = launch(cmd, item, f'正式 rank {rr}')
            es.append({"rank": rr, "pid": pid, "gpus": gs, "cmd": cmd,
                       "log": f'{PROJH}/logs/rt/{logn}', "outglob": '', "world": world})
        update_watchdog(item, es)
        if not wait_all_exit(es, item, stale_hours=12):
            halt(item, '正式编辑 12 小时未结束')
        nodone = [e['rank'] for e in es if '[deltas] done:' not in open(e['log'], errors='replace').read()]
        if nodone:
            halt(item, f'rank {nodone} 未正常退出（日志无 [deltas] done:，§3.2 要求全部退出码 0）')
    launch_all('', '')
    def passed(d):
        return bool(d) and fnum(d, 'cases') == expect_n and fnum(d, 'ok') == expect_n and \
            fnum(d, 'editor_nan') == 0 and fnum(d, 'max_rank') == 1 and \
            fnum(d, 'max_rel_err') is not None and fnum(d, 'max_rel_err') < 1e-4
    out_json = f'{POUTH}/summarize_S3_{"fresh" if tag=="s3fresh" else "ext"}.json'
    s = run_summarize(expect_files=world)
    with open(out_json, 'w') as f:
        f.write(s)
    d = parse_summarize(s)
    if not passed(d):
        rep(f"## {item} retry-errors ⏸→run {utc()}", f"- summarize 未过: {json.dumps(d or {})[:400]}\n- 按单原命令加 --retry-errors 重跑一次")
        launch_all(' --retry-errors', '_retry')
        s = run_summarize(expect_files=world)
        with open(out_json, 'w') as f:
            f.write(s)
        d = parse_summarize(s)
        if not passed(d):
            halt(item, f'retry-errors 后仍未过: {json.dumps(d or {})[:400]}')
    return world

# ---------------- §4 ----------------

def phase_s4():
    CUR['phase'] = 'S4 screen'; save_cur()
    env = f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src"
    tags = ['r1qwen32b', 'r1qwen14b', 'r1llama8b', 'r1qwen7b', 'r1qwen1_5b']
    models = []
    for t in tags:
        out, rc = sh_out(f"ls {P4090}/results/rt/pool/{t}_pool_screen_r0of*.jsonl")
        f = out.splitlines()[0] if out and rc == 0 else None
        if not f:
            halt('S3H-§4', f'{t} pool screen 分片找不到')
        mp, _ = sh_out(f"python3 -c \"import json;print(json.loads(open('{f}').readline())['model']['path'])\"")
        if not mp or not os.path.isdir(mp):
            halt('S3H-§4', f'{t} model path 缺失或本节点不存在: {mp!r}')
        models.append((t, mp))
        rep(f"## S3H-§4 model-path {utc()}", f"- {t} {mp}")
    for t, mp in models:
        CUR['phase'] = f'S4 screen {t}'; save_cur()
        assert_gpus_free(list(range(8)), 'S3H-§4')
        entries = []
        for r in range(8):
            rotate(f'{PROJH}/logs/rt/s3screen_{t}_r{r}.out')
            cmd = (f"cd {PROJH} || exit 1; {ENV_OFF}; nohup env CUDA_VISIBLE_DEVICES={r} WHYAAAI_MODEL={mp} PYTHONPATH=src "
                   f"python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag {t} "
                   f"--rank {r} --world 8 > logs/rt/s3screen_{t}_r{r}.out 2>&1 < /dev/null & echo NEWPID=$!")
            pid = launch(cmd, 'S3H-§4', f'{t} rank {r}')
            entries.append({"rank": r, "pid": pid, "gpus": [r], "cmd": cmd,
                            "log": f'{PROJH}/logs/rt/s3screen_{t}_r{r}.out', "outglob": '', "world": 8})
        update_watchdog(f'S4-{t}', entries)
        if not wait_all_exit(entries, f'S4-{t}', stale_hours=10, item='S3H-§4'):
            halt('S3H-§4', f'{t} screen 10 小时未结束')
        redo = [e for e in entries if not screen_ok(e['log'])]
        if redo:
            assert_gpus_free(sorted({g for e in redo for g in e['gpus']}), 'S3H-§4')
            for e in redo:
                rep(f"## S3H-§4 {t} r{e['rank']} rerun ⏸→run {utc()}", "- rank 日志无 {'screen': N} 结束行 -> 原命令续跑一次")
                try:
                    os.replace(e['log'], e['log'] + f".pre_{time.strftime('%Y%m%d_%H%M%S')}")
                except FileNotFoundError:
                    pass
                e['pid'] = launch(e['cmd'], 'S3H-§4', f"{t} rank {e['rank']} 重跑")
            update_watchdog(f'S4-{t}', entries)
            if not wait_all_exit(entries, f'S4-{t}', stale_hours=6, item='S3H-§4'):
                halt('S3H-§4', f'{t} screen 重跑 6 小时未结束')
            for e in entries:
                if not screen_ok(e['log']):
                    halt('S3H-§4', f"{t} rank {e['rank']} 重跑后仍无 screen 结束行")
        q = sh(f"{env} python3 -m rt.pool qualify --config experiments/rt/pool_screen_s3.yaml --model-tag {t}", 3600)
        if q.returncode != 0 or not re.search(rf'^\[pool\] {re.escape(t)}: qualified ', q.stdout, re.M):
            halt('S3H-§4', f'qualify {t} 失败 rc={q.returncode}: {q.stdout.strip()[:200]} | {q.stderr.strip()[-300:]}')
        rep(f"## S3H-§4 qualify {t} ✓ {utc()}", f"- {q.stdout.strip()[:300]}")
    m = sh(f"{env} python3 -m study3.ext_manifest", 3600)
    if m.returncode != 0 or '[study3.ext_manifest] qualified' not in m.stdout:
        halt('S3H-§4', f'ext_manifest 失败 rc={m.returncode}: {m.stdout.strip()[:200]} | {m.stderr.strip()[-300:]}')
    rep(f"## S3H-§4 ext_manifest ✓ {utc()}", f"- {m.stdout.strip()[:400]}")
    return record_ext_manifest()

def record_ext_manifest():
    """§4.4 / D9(c): identity record written and read back before any §5 work; idempotent on resume."""
    mf = f'{PROJH}/experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl'
    if not os.path.exists(mf):
        halt('S3H-§4', 'manifest_r1qwen32b_ext.jsonl 未生成')
    mf_sha = sha256_file(mf)
    with open(mf) as fh:
        mf_n = sum(1 for _ in fh)
    rec_p = f'{SHARE}/S3_EXT_MANIFEST.txt'
    if not os.path.exists(rec_p):
        try:
            with open(rec_p, 'w') as fh:
                fh.write(f"{mf_sha}  {mf} n={mf_n} {time.strftime('%FT%TZ', time.gmtime())}\n")
                fh.flush()
                os.fsync(fh.fileno())
        except OSError as ex:
            halt('S3H-§4', f'S3_EXT_MANIFEST.txt 写入失败: {ex}；§5 不开始')
    try:
        rec = open(rec_p).read().split()
    except OSError as ex:
        halt('S3H-§4', f'S3_EXT_MANIFEST.txt 读回失败: {ex}')
    if len(rec) < 4 or rec[0] != mf_sha or rec[2] != f'n={mf_n}':
        halt('S3H-§4', f'S3_EXT_MANIFEST.txt 与 manifest 不符: {rec[:4]} expect sha={mf_sha} n={mf_n}')
    if sh(f"mkdir -p {POUTH}/pools_study3 && cp -a {PROJH}/experiments/rt/pools/study3/. {POUTH}/pools_study3/").returncode != 0:
        halt('S3H-§4', 'cp pools_study3 失败')
    touch_marker('S3_EXT_MANIFEST_DONE', 'S3H-§4')
    rep(f"## S3H-§4 ✓ {utc()}", f"- manifest n={mf_n} sha256={mf_sha}; S3_EXT_MANIFEST.txt 已写并读回一致; pools_study3 已拷; touch S3_EXT_MANIFEST_DONE")
    return mf_n

# ---------------- smoke (§6) ----------------

def answer_stats(paths):
    """Answer-field stats of smoke data rows (no _meta, no error rows). Report-only; never a verdict."""
    n = empty = 0
    lens = []
    for p in paths:
        with open(p, errors='replace') as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get('_meta') or d.get('error') or not d.get('probe'):
                    continue
                a = (d.get('answer') or '').strip()
                n += 1
                lens.append(len(a))
                empty += (not a)
    lens.sort()
    return {'rows': n, 'empty_answers': empty, 'answer_len_min': lens[0] if lens else None,
            'answer_len_median': lens[len(lens) // 2] if lens else None}

def phase_s6():
    CUR['phase'] = 'S6 smoke'; save_cur()
    assert_gpus_free([0], 'S3H-§6')
    cmd = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP && "
           f"CUDA_VISIBLE_DEVICES=0 WHYAAAI_MODEL={M32} python3 -m rt.run --config experiments/rt/study3_smoke.yaml "
           f"--conditions base,rome_N --rank 0 --world 1 --device cuda --batch-size 16 --max-batch-tokens 40000 "
           f"> logs/rt/s3smoke.log 2>&1; echo rc=$?")
    r = sh(cmd, 14400)
    rc = r.stdout.strip().split('rc=')[-1]
    if rc != '0':
        halt('S3H-§6', f'冒烟退出码 {rc}; tail: {sh_out(f"tail -5 {PROJH}/logs/rt/s3smoke.log")[0][:400]}')
    files = sorted(glob.glob(f'{PROJH}/results/rt/s3smoke/*.jsonl'))
    per = {}
    for p in files:
        base = os.path.basename(p)
        cond = 'base' if '_base_' in base else ('rome_N' if '_rome_N_' in base else None)
        if not cond:
            continue
        n = e = 0
        with open(p, errors='replace') as f:
            for line in f:
                d = json.loads(line)
                if d.get('error'):
                    e += 1
                elif d.get('case_id') and d.get('probe'):
                    n += 1
        per.setdefault(cond, [0, 0])
        per[cond][0] += n
        per[cond][1] += e
    if per.get('base', [0])[0] != 8 or per.get('rome_N', [0])[0] != 8 or per.get('base', [0, 0])[1] or per.get('rome_N', [0, 0])[1]:
        halt('S3H-§6', f'冒烟行数不符: {per}')
    st = answer_stats(files)
    if sh(f"mkdir -p {POUTH}/results/rt/s3smoke && cp -a {PROJH}/results/rt/s3smoke/. {POUTH}/results/rt/s3smoke/").returncode != 0:
        halt('S3H-§6', 'cp results/rt/s3smoke -> POUTH 失败')
    rep(f"## S3H-§6 ⏸ {utc()}",
        f"- 退出码 0; base=8 行, rome_N=8 行, 0 error; answer 字段统计(仅供复核参考): {json.dumps(st)}\n"
        f"- results/rt/s3smoke 已拷 POUTH。按 S3-H v2 第 3 条：§3–§5 照常继续，§7 启动前等待。executor agent（只读 results/rt/s3smoke/）"
        f"或 leader 判定英文连贯：通过 touch {SHARE}/S3_SMOKE_GO，不通过 touch {SHARE}/S3_SMOKE_NOGO")
    touch_marker('S3_SMOKE_DONE', 'S3H-§6')

def wait_go(item, go, nogo, who, need_note=False):
    """Human gate in $SHARE. NOGO halts (and wins over GO). need_note: GO must carry the reader's note (non-empty)."""
    CUR['phase'] = f'{item} wait {go}'; save_cur()
    asked = False
    while True:
        if marker(nogo):
            halt(item, f'{who} 判定不通过（{nogo}）')
        if marker(go):
            try:
                has_note = os.path.getsize(f'{SHARE}/{go}') > 0
            except OSError:
                has_note = False
            if has_note or not need_note:
                break
            if not asked:
                rep(f"## {item} ⏸ {utc()}", f"- {SHARE}/{go} 存在但为空：按 S3-H v2 第 4 条须写入读取记录（见上一块），未放行")
                asked = True
        time.sleep(300)
    rep(f"## {item} ✓ {utc()}", f"- 已见 {SHARE}/{go}（{who} 判定通过）")

# ---------------- §7 generation ----------------

def s3_progress(world):
    pf = '/tmp/s3_progress.json'                       # path fixed by S3-H §7.2
    try:
        os.remove(pf)
    except FileNotFoundError:
        pass
    r = sh(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -m study3.end_entry --stopped-at progress --out {pf}", 600)
    if r.returncode != 0 or not os.path.exists(pf):
        halt('S3H-§7', f'end_entry progress rc={r.returncode}: {(r.stdout + r.stderr)[-300:]}')
    try:
        with open(pf) as f:
            w = json.load(f)['worlds'][world]
    except Exception as ex:
        halt('S3H-§7', f'end_entry progress 解析失败 world={world}: {type(ex).__name__}: {ex}')
    keys = {k: w.get(k) for k in ('n_complete_efficacy', 'valid_rows', 'error_rows')}
    log(f"progress[{world}]: {json.dumps(keys)[:300]}")
    return keys

def gen_phase(kind, expect_n, item, share_flag):
    CUR['phase'] = item; save_cur()
    if marker('S3_END'):
        halt(item, 'S3_END 已存在：addendum §4 登记终点之后不得再生成 Study 3')
    assert_gpus_free(list(range(8)), item)
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study3_r1qwen32b_{kind}.yaml "
           f"--conditions base,rome_N --rank {{rank}} --world 8 --device cuda --batch-size 16 "
           f"--max-batch-tokens {{tokens}}")
    pids, entries = start_rt_ranks(item, 8, tpl, f'{PROJH}/logs/rt/s3g_{kind}_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s3/*_r{{rank}}of8.jsonl')
    if not wait_all_exit(entries, item, stale_hours=14):
        halt(item, '生成 14 小时未结束')
    li = 1
    while True:
        keys = s3_progress(kind)
        vr = keys.get('valid_rows') or {}
        if (keys.get('n_complete_efficacy') == expect_n and set(vr) == S3_KEYS
                and all(vr[k] == expect_n for k in S3_KEYS)):
            break
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt(item, f'18000 档续跑后仍未齐: {json.dumps(keys)[:300]}')
        if marker('S3_END'):
            halt(item, 'S3_END 已存在（登记终点已收尾）：不再阶梯续跑 Study 3')
        rep(f"## {item} ladder{tok} ⏸→run {utc()}",
            f"- progress={json.dumps(keys)[:300]}\n- 按 §1.4 阶梯以 {tok} 续跑全部 8 rank（rt.run 只补缺失键；不读 s3 分片）")
        assert_gpus_free(list(range(8)), item)
        for e in entries:
            relaunch_rank(item, e, tok)
        if not wait_all_exit(entries, item, stale_hours=10):
            halt(item, f'阶梯续跑({tok}) 10 小时未结束')
        li += 1
    touch_marker(os.path.basename(share_flag), item)
    rep(f"## {item} ✓ {utc()}", f"- n_complete_efficacy={expect_n}; 8 个组合 valid 行={expect_n}; touch {share_flag}")

def s3_finalize():
    item = 'S3H-§7收尾'
    CUR['phase'] = 'S7 finalize'; save_cur()
    rt_ps, _ = sh_out(RT_PGREP)
    if rt_ps:
        halt(item, f'rt 进程仍在运行，拒绝写结束条目: {rt_ps[:300]}')
    ts = sh_out("TZ=UTC-8 date '+%F %T UTC+8'")[0]
    r = sh(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -m study3.end_entry --stopped-at \"{ts}\"", 1800)
    ej = f'{PROJH}/experiments/rt/s3_end_of_generation.json'
    try:
        ent = json.load(open(ej))
    except Exception as ex:
        halt(item, f'end_entry 未生成可读 json rc={r.returncode}: {ex} {(r.stdout + r.stderr)[-300:]}')
    if r.returncode != 0:
        halt(item, f'end_entry rc={r.returncode}: {(r.stdout + r.stderr)[-300:]}')
    if sh(f'mkdir -p {POUTH}/results/rt/s3 && cp -a {PROJH}/results/rt/s3/. {POUTH}/results/rt/s3/', 7200).returncode != 0 \
            or sh(f'cp {ej} {POUTH}/').returncode != 0:
        halt(item, 'cp results/rt/s3 或 s3_end_of_generation.json -> POUTH 失败')
    badcp = [rel for rel, h in ent.get('shards', {}).items()
             if not os.path.exists(f'{POUTH}/{rel}') or sha256_file(f'{POUTH}/{rel}') != h]
    if badcp:
        halt(item, f'POUTH 副本与结束条目 sha256 不符: {badcp[:5]}')
    touch_marker('S3_END', item)
    rep(f"## S3H-§7 END ✓ {utc()}",
        f"- end_entry stopped-at {ts}; results/rt/s3 与 s3_end_of_generation.json 已拷 POUTH（sha256 逐片核对）; touch S3_END\n- 未运行 study3.confirm（按单留给 leader）")

# ---------------- §8 parent queue (second window, D11) ----------------

def _prefix_sha(path, n):
    """sha256 of the first n bytes of path (None if the file is shorter)."""
    h = hashlib.sha256()
    left = n
    with open(path, 'rb') as fh:
        while left > 0:
            b = fh.read(min(1 << 20, left))
            if not b:
                break
            h.update(b)
            left -= len(b)
    return h.hexdigest() if left == 0 else None

def _d11_registered(item):
    """The registered entry (registry entry 10) and its 120 H100 lines `<sha256>  <PROJH>/results/rt/s2/...`."""
    try:
        ok = sha256_file(D11_ENTRY) == D11_ENTRY_SHA
    except OSError:
        ok = False
    if not ok:
        halt(item, f'登记的 parent_end_of_generation.txt 缺失或已变（应为 {D11_ENTRY_SHA[:12]}…）')
    reg = []
    with open(D11_ENTRY) as fh:
        for line in fh:
            parts = line.rstrip('\n').split('  ', 1)
            if len(parts) == 2 and parts[1].startswith(f'{PROJH}/results/rt/s2/'):
                reg.append((parts[0], parts[1]))
    if len(reg) != 120:
        halt(item, f'D11 条目 H100 行数 {len(reg)} != 120')
    return reg

def registered_parent_intact(item):
    """D11 guard. Until PARENT2_STARTED exists (written just before G10', the first window-2 writer to registered
    shards): all 120 registered H100 shards hash to their registered values. Afterwards (G10' appends to 56 of them by
    design): each still begins with exactly its registered bytes, i.e. window 2 only appended. Bytes only, no row parsed."""
    reg = _d11_registered(item)
    if not marker('PARENT2_STARTED'):
        bad = [p for h, p in reg if not os.path.exists(p) or sha256_file(p) != h]
        if bad:
            halt(item, f'PROJH results/rt/s2 与 D11 登记条目不符（第二窗口写入前；待 leader）: {bad[:5]}')
        return reg
    try:
        st = json.load(open(P2_START))
        sizes = st.get('sizes')
        if st.get('entry_sha') != D11_ENTRY_SHA or not isinstance(sizes, dict):
            raise ValueError('entry_sha/sizes 不符')
    except Exception as ex:
        halt(item, f'PARENT2_STARTED 不可读或与 D11 条目不符: {type(ex).__name__}: {ex}')
    if set(sizes) != {p for _, p in reg}:
        halt(item, 'PARENT2_STARTED 的分片集合与 D11 条目不符')
    bad = [p for h, p in reg if not os.path.exists(p) or os.path.getsize(p) < sizes[p]
           or _prefix_sha(p, sizes[p]) != h]
    if bad:
        halt(item, f'登记分片的已登记前缀被改（不是只追加；待 leader）: {bad[:5]}')
    return reg

def mark_parent2_started(item):
    """Record the registered byte sizes immediately before window 2 first appends to registered shards (G10')."""
    if marker('PARENT2_STARTED'):
        return
    reg = registered_parent_intact(item)          # full-hash check (marker absent)
    rec = {'entry_sha': D11_ENTRY_SHA, 'utc': utc(), 'sizes': {p: os.path.getsize(p) for _, p in reg}}
    try:
        with open(P2_START + '.tmp', 'w') as fh:
            json.dump(rec, fh)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(P2_START + '.tmp', P2_START)
    except OSError as ex:
        halt(item, f'PARENT2_STARTED 写入失败: {ex}')
    if not marker('PARENT2_STARTED'):
        halt(item, 'PARENT2_STARTED 写入后不可见')
    rep(f"## {item} PARENT2_STARTED ✓ {utc()}",
        f"- 120 个登记分片 sha256 = D11 登记值；登记字节数已记入 {P2_START}（此后续跑只核登记前缀，允许 G10' 追加写）")

def record_g3_reading(files):
    """S3-H v2 amendment 4: the executor's reading of the 2 smoke cases, for the parent2 entry (written once)."""
    if os.path.exists(G3_READING):
        return
    gp = f'{SHARE}/G3_SMOKE_GO'
    try:
        note = ' '.join(open(gp, errors='replace').read().split())[:500]
        mt = time.strftime('%FT%TZ', time.gmtime(os.path.getmtime(gp)))
        shards = '; '.join(f'{os.path.basename(p)} sha256={sha256_file(p)}' for p in files)
        line = (f"G3pp 70B smoke reading (S3-H v2 amendment 4): {shards} (2 cases, second-window outcomes) were read "
                f"for coherent English (R1-Llama risks: missing spaces, missing BOS) by the executor agent; the leader "
                f"does not read them. G3_SMOKE_GO mtime {mt}; note: {note}\n")
        with open(G3_READING + '.tmp', 'w') as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(G3_READING + '.tmp', G3_READING)
    except OSError as ex:
        halt("S3H-§8 G3'' smoke", f'g3_smoke_reading.txt 写入失败: {ex}')
    rep(f"## S3H-§8 G3'' smoke reading ✓ {utc()}", f"- 读取记录已写 {G3_READING}（parent2 条目将包含）: {line[:300]}")

def g3_smoke():
    CUR['phase'] = 'S8 G3smoke'; save_cur()
    cfg = 'experiments/rt/study2_r1llama70b_eff.yaml'
    cfg_path = f'{PROJH}/{cfg}'
    if not os.path.exists(cfg_path):
        halt('S3H-§8 G3冒烟', f'{cfg} 不存在（bundle 后应带来）')
    assert_gpus_free([0, 1], 'S3H-§8 G3冒烟')
    cfg_txt = open(cfg_path).read()
    dev_flag = '' if 'device_map' in cfg_txt else '--device auto'
    rep(f"## S3H-§8 G3'' smoke note {utc()}",
        f"- 70B 配置{'含' if 'device_map' in cfg_txt else '不含'} device_map 字段"
        + ('；按 H-2 原文 G3'' 既定参数补 --device auto（S3-H §8.1 模板省略，视为沿用，非改方案）' if dev_flag else ''))
    cmd = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP && "
           f"CUDA_VISIBLE_DEVICES=0,1 WHYAAAI_MODEL={M70} python3 -m rt.run --config {cfg} --rank 0 --world 8 "
           f"--run-tag s2smoke --limit 2 --max-batch-tokens 34000 {dev_flag} "
           f"> logs/rt/s2smoke70.log 2>&1; echo rc=$?")
    r = sh(cmd, 14400)
    rc = r.stdout.strip().split('rc=')[-1]
    if rc != '0':
        halt('S3H-§8 G3冒烟', f'退出码 {rc}; tail: {sh_out(f"tail -8 {PROJH}/logs/rt/s2smoke70.log")[0][:500]}')
    files = sorted(glob.glob(f'{PROJH}/results/rt/s2/r1llama70b_s2smoke_*_r0of8.jsonl'))   # --run-tag keeps out_dir s2
    per = {}
    for p in files:
        base = os.path.basename(p)
        cond = 'base' if '_base_' in base else ('rome_N' if '_rome_N_' in base else None)
        if not cond:
            continue
        n = e = 0
        with open(p, errors='replace') as f:
            for line in f:
                d = json.loads(line)
                if d.get('error'):
                    e += 1
                elif d.get('case_id') and d.get('probe'):
                    n += 1
        per.setdefault(cond, [0, 0])
        per[cond][0] += n
        per[cond][1] += e
    if per.get('base', [0])[0] != 4 or per.get('rome_N', [0])[0] != 4:
        halt('S3H-§8 G3冒烟', f'行数不符: {per}')
    rep(f"## S3H-§8 G3'' smoke ⏸ {utc()}",
        f"- 退出码 0; valid 行 base={per['base'][0]}, rome_N={per['rome_N'][0]}; error 行 base={per['base'][1]}, rome_N={per['rome_N'][1]}\n"
        f"- orchestrator 只计行数、未读文本。按 S3-H v2 第 4 条：由 executor agent（非 leader；leader 不读这些第二窗口未见父结果）"
        f"读 {PROJH}/results/rt/s2/r1llama70b_s2smoke_{{base,rome_N}}_r0of8.jsonl 的 2 个 case，判英文连贯（R1-Llama 已知风险：缺空格、缺 BOS）。"
        f"通过：把读取记录写进 GO，例如 echo \"reader=executor-agent utc=$(date -u +%FT%TZ) verdict=coherent\" > {SHARE}/G3_SMOKE_GO"
        f"（空文件不放行）；不通过：touch {SHARE}/G3_SMOKE_NOGO。parent2 条目将记录该读取")
    wait_go("S3H-§8 G3'' smoke", 'G3_SMOKE_GO', 'G3_SMOKE_NOGO', who='executor agent（leader 未读）', need_note=True)
    record_g3_reading(files)

def g3_formal():
    CUR['phase'] = 'S8 G3 formal'; save_cur()
    cfg = 'experiments/rt/study2_r1llama70b_eff.yaml'
    cfg_txt = open(f'{PROJH}/{cfg}').read()
    dev_flag = '' if 'device_map' in cfg_txt else '--device auto'
    slots = {0: [0, 1], 1: [2, 3], 2: [4, 5], 3: [6, 7]}
    for batch in ([0, 1, 2, 3], [4, 5, 6, 7]):
        entries = []
        assert_gpus_free(sorted(g for k in batch for g in slots[k % 4]), 'S3H-§8 G3 formal')
        for k in batch:
            gs = slots[k % 4]
            gpu_s = ','.join(map(str, gs))
            cmd = (f"cd {PROJH} || exit 1; {ENV_OFF}; export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP; "
                   f"nohup env CUDA_VISIBLE_DEVICES={gpu_s} WHYAAAI_MODEL={M70} python3 -m rt.run --config {cfg} "
                   f"--rank {k} --world 8 --max-batch-tokens 34000 {dev_flag} "
                   f"> logs/rt/g70_r{k}.log 2>&1 < /dev/null & echo NEWPID=$!")
            pid = launch(cmd, 'S3H-§8 G3 formal', f'rank {k}')
            entries.append({"rank": k, "pid": pid, "gpus": gs, "cmd": cmd,
                            "log": f'{PROJH}/logs/rt/g70_r{k}.log',
                            "outglob": f'{PROJH}/results/rt/s2/r1llama70b_s2_{{cond}}_r{k}of8.jsonl', "world": 8})
        update_watchdog("G3p", entries)
        if not wait_all_exit(entries, "G3p", stale_hours=20, item='S3H-§8 G3 formal'):
            halt('S3H-§8 G3 formal', f'batch {batch} 20 小时未结束')
        li = 1
        while True:
            bad = []
            for e in entries:
                if not exit_ok(e['log']):
                    bad.append(e['rank']); continue
                rows, tot_only = {}, 0
                for cond in ('base', 'rome_N'):
                    files = glob.glob(f"{PROJH}/results/rt/s2/r1llama70b_s2_{cond}_r{e['rank']}of8.jsonl")
                    okc, errc, keys = set(), set(), set()
                    for f in files:
                        with open(f, errors='replace') as fh:
                            for line in fh:
                                d = json.loads(line)
                                if d.get('error'):
                                    errc.add(d.get('case_id'))
                                elif d.get('case_id') and d.get('probe'):
                                    okc.add(d['case_id']); keys.add((d['case_id'], d.get('budget')))
                    rows[cond] = len(keys)
                    tot_only += len(errc - okc)
                if rows.get('base', 0) != 100 or rows.get('rome_N', 0) != 100 or tot_only > 0:
                    bad.append(e['rank'])
            if not bad:
                break
            tok = ladder_tokens(RT70_LADDER, li)
            if tok is None:
                halt('S3H-§8 G3 formal', f'18000 档后仍未齐: bad={bad}')
            rep(f"## S3H-§8 G3'' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
            assert_gpus_free(sorted(g for e in entries if e['rank'] in bad for g in e['gpus']), 'S3H-§8 G3 formal')
            for e in entries:
                if e['rank'] in bad:
                    relaunch_rank("G3p", e, tok)
            if not wait_all_exit(entries, "G3p", stale_hours=20, item='S3H-§8 G3 formal'):
                halt('S3H-§8 G3 formal', f'阶梯续跑({tok}) 20 小时未结束')
            li += 1
    rep(f"## S3H-§8 G3'' ✓ {utc()}", "- 8 rank 全部: base/rome_N 各 100 个 (case,budget) valid 键、未重做 error case=0（§0 按意图）")

def g10_resume():
    CUR['phase'] = 'S8 G10 resume'; save_cur()
    conds = ['rome_B0P', 'rome_B1', 'rome_a0.5', 'rome_a2', 'rome_a3', 'ike', 'rome_samp']
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml "
           f"--rank {{rank}} --world 8 --device cuda --batch-size 16 --max-batch-tokens {{tokens}} "
           f"--conditions {','.join(conds)} --stage 1")
    mark_parent2_started("S3H-§8 G10'")           # last moment before window 2 appends to registered shards
    assert_gpus_free(list(range(8)), "S3H-§8 G10'")
    pids, entries = start_rt_ranks("G10r", 8, tpl, f'{PROJH}/logs/rt/s2_32_sec1_resume_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s2/r1qwen32b_s2_*_r{{rank}}of8.jsonl')
    li = 1
    while True:
        if not wait_all_exit(entries, "G10r", stale_hours=8, item="S3H-§8 G10'"):
            halt("S3H-§8 G10'", '续跑 8 小时未结束')
        bad = rank_incomplete(entries, [f'{PROJH}/results/rt/s2/r1qwen32b_s2_{c}_r{{rank}}of8.jsonl' for c in conds])
        if not bad:
            break
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt("S3H-§8 G10'", f'18000 档后仍未齐: {bad}')
        rep(f"## S3H-§8 G10' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
        assert_gpus_free(sorted(g for e in entries if any(b[0] == e['rank'] for b in bad) for g in e['gpus']), "S3H-§8 G10'")
        for e in entries:
            if any(b[0] == e['rank'] for b in bad):
                relaunch_rank("G10r", e, tok)
        li += 1
    rep(f"## S3H-§8 G10' ✓ {utc()}", "- 全部 rank 分片齐（每 case 有 valid 行，§0 按意图）")

def g11_run():
    CUR['phase'] = 'S8 G11'; save_cur()
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml "
           f"--rank {{rank}} --world 8 --device cuda --batch-size 16 --max-batch-tokens {{tokens}} --stage 2")
    assert_gpus_free(list(range(8)), "S3H-§8 G11")
    pids, entries = start_rt_ranks("G11r", 8, tpl, f'{PROJH}/logs/rt/s2_32_sec2_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s2/r1qwen32b_s2_*_r{{rank}}of8.jsonl')
    li = 1
    while True:
        if not wait_all_exit(entries, "G11r", stale_hours=10, item="S3H-§8 G11"):
            halt("S3H-§8 G11", '10 小时未结束')
        bad = rank_incomplete(entries, [f'{PROJH}/results/rt/s2/r1qwen32b_s2_{c}_r{{rank}}of8.jsonl'
                                        for c in ('rome_own', 'rome_filler', 'rome_swap')])
        if not bad:
            break
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt("S3H-§8 G11", f'18000 档后仍未齐: {bad}')
        rep(f"## S3H-§8 G11' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
        assert_gpus_free(sorted(g for e in entries if any(b[0] == e['rank'] for b in bad) for g in e['gpus']), "S3H-§8 G11")
        for e in entries:
            if any(b[0] == e['rank'] for b in bad):
                relaunch_rank("G11r", e, tok)
        li += 1
    rep(f"## S3H-§8 G11' ✓ {utc()}", "- 全部 rank 分片齐（每 case 有 valid 行，§0 按意图）")

def parent2_end():
    """Supplement 1 §2 / D11: window 2 gets its own entry; never write parent_end_of_generation.txt,
    PARENT_END or POUTH/results/rt/s2."""
    item = 'S3H-§8 第二窗口收尾'
    CUR['phase'] = 'S8 parent2 end'; save_cur()
    rt_ps, _ = sh_out(RT_PGREP)
    if rt_ps:
        halt(item, f'rt 进程仍在运行，拒绝写第二窗口条目: {rt_ps[:300]}')
    pe = f'{POUTH}/parent2_end_of_generation.txt'
    snap = f'{POUTH}/results/rt/s2_window2'
    for p in (pe, pe + '.tmp', snap, f'{SHARE}/PARENT2_END'):
        if os.path.exists(p):
            halt(item, f'{p} 已存在，拒绝覆盖')
    if sha256_file(D11_ENTRY) != D11_ENTRY_SHA:
        halt(item, '登记的 parent_end_of_generation.txt 已变')
    if not os.path.exists(G3_READING) or os.path.getsize(G3_READING) == 0:
        halt(item, f'{G3_READING} 缺失：S3-H v2 第 4 条要求 parent2 条目记录 70B 冒烟的读取')
    out, _ = sh_out(f"set -o pipefail; sha256sum {PROJH}/results/rt/s2/*.jsonl > {pe}.tmp && "
                    f"cat {G3_READING} >> {pe}.tmp && "
                    f"echo \"stopped: second window (D11, supplementary; G3pp, G10p resume, G11p queue complete); "
                    f"written $(date -u +%FT%TZ)\" >> {pe}.tmp && mv {pe}.tmp {pe} && echo OK", 7200)
    if 'OK' not in out:
        halt(item, 'sha256sum results/rt/s2 -> parent2_end_of_generation.txt 失败')
    if sh(f'mkdir -p {POUTH}/results/rt && cp -a {PROJH}/results/rt/s2 {snap}', 7200).returncode != 0:
        halt(item, 'cp results/rt/s2 -> POUTH/results/rt/s2_window2 失败')
    if sha256_file(D11_ENTRY) != D11_ENTRY_SHA:
        halt(item, '收尾期间登记条目被改')
    touch_marker('PARENT2_END', item)
    rep(f"## S3H-§8 PARENT2_END ✓ {utc()}",
        "- 第二窗口（D11 补充）结束条目 parent2_end_of_generation.txt 已写（绝对路径 sha256 + 70B 冒烟读取记录（修订 4）+ stopped 行）; "
        "results/rt/s2 已拷 POUTH/results/rt/s2_window2; touch PARENT2_END\n"
        "- 未改动登记终点: parent_end_of_generation.txt（sha256 复核 = 登记值）、PARENT_END、POUTH/results/rt/s2；未运行 rt.study2")

# ---------------- hourly reporter ----------------

def hourly():
    while True:
        time.sleep(3600)
        try:
            alive = 0
            try:
                out, _ = sh_out('pgrep -cf "rt[.](run|pool|deltas)" || true', 120)
                alive = int(out) if out.strip().isdigit() else 0
            except Exception:
                pass
            try:
                gpu, _ = sh_out('timeout -k 10 60 nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader '
                                '2>/dev/null | tr "\\n" " "', 120)
            except Exception:
                gpu = 'nvidia-smi 超时/失败'
            rep(f"## ORCH heartbeat ✓ {utc()}",
                f"- 心跳（非停止）: 阶段 {CUR.get('phase')} | {CUR.get('detail')} | rt 进程 {alive} | {(gpu or 'nvidia-smi 无输出')[:200]}")
        except Exception:
            pass

# ---------------- main ----------------

def main():
    global _ORCH_FH
    _ORCH_FH = open(ORCH_LOCK, 'a')               # kept open for the life of the process; not inherited by children
    try:
        fcntl.flock(_ORCH_FH, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"[{utc()}] another orch_s3h.py holds {ORCH_LOCK}; exiting without touching report/state/watchdog", flush=True)
        os._exit(2)
    if marker('S3_CODE_OK'):
        rt_ps, _ = sh_out(RT_PGREP)
        if rt_ps:
            halt('S3H-§2 resume', f'续跑启动时仍有上一轮遗留 rt 进程；看门狗状态未重置（这些 rank 仍受看门狗跟踪），待 leader 裁决: {rt_ps[:300]}')
    with _WdLock():
        wd_save({"ranks": [], "note": "reset by orch_s3h at start"})
    t = threading.Thread(target=hourly, daemon=True)
    t.start()
    log('orchestrator started (S3-H)')
    rep(f"## S3H-ORCH start ✓ {utc()}",
        "- 夜间自动执行已启动（nohup setsid 等价 tmux detached）：等待 $SHARE/s3_code_full.bundle → §2…§8；任何校验失败写 ⏸ 停止；补跑阶梯 40k→26k→18k（70B 34k→26k→18k）；看门狗 v3 长驻")
    try:
        phase_s2(resume=marker('S3_CODE_OK'))
    except SystemExit:
        raise
    except Exception as e:
        halt('S3H-§2', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    if marker('S3_END'):
        rep(f"## S3H-§3–§7 ✓ {utc()}",
            f"- 已见 {SHARE}/S3_END（addendum §4 登记终点，s3_finalize 或 leader 收尾）：不再运行任何 Study 3 冒烟/编辑/筛选/生成，直接进入 §8")
    else:
        try:
            # S3-H v2 amendment 3: the generation smoke uses only old Study 2 deltas, so it runs before §3 and its
            # review overlaps the edits; only §7 waits for S3_SMOKE_GO.
            if not marker('S3_SMOKE_DONE'):
                if marker('S3_SMOKE_GO') or marker('S3_SMOKE_NOGO'):
                    halt('S3H-§6', 'S3_SMOKE_GO/NOGO 已存在但没有 S3_SMOKE_DONE（冒烟未完成即被放行/否决），待 leader')
                phase_s6()
                if not wait_gpus_free():
                    halt('S3H-§6', '冒烟结束后 20 分钟内 8 卡未全部 <1GB')
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§6', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            if not marker('S3_D_FRESH_DONE'):
                deltas_phase('s3fresh', 'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml', 309, 'S3H-§3',
                             smoke=not marker('S3_D_SMOKE_OK'), world=edit_world())
                touch_marker('S3_D_FRESH_DONE', 'S3H-§3')
                rep(f"## S3H-§3 ✓ {utc()}", "- cases=309 ok=309 errors 空 editor_nan=0 max_rank=1 max_rel_err<1e-4; summarize 已存 POUTH; touch S3_D_FRESH_DONE")
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§3', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            ext_n = record_ext_manifest() if marker('S3_EXT_MANIFEST_DONE') else phase_s4()
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§4', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            if not marker('S3_D_EXT_DONE'):
                deltas_phase('s3ext', 'experiments/rt/deltas_s3_r1qwen32b_ext.yaml', ext_n, 'S3H-§5', smoke=False,
                             world=edit_world())
                touch_marker('S3_D_EXT_DONE', 'S3H-§5')
                rep(f"## S3H-§5 ✓ {utc()}", f"- cases={ext_n} ok={ext_n} 其余条件同 §3; touch S3_D_EXT_DONE")
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§5', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            wait_go('S3H-§6', 'S3_SMOKE_GO', 'S3_SMOKE_NOGO', who='executor agent 或 leader（S3-H v2 第 3 条）')
            if not marker('S3_G_FRESH_DONE'):
                gen_phase('fresh', 309, 'S3H-§7 fresh', f'{SHARE}/S3_G_FRESH_DONE')
            if not marker('S3_G_EXT_DONE'):
                gen_phase('ext', ext_n, 'S3H-§7 ext', f'{SHARE}/S3_G_EXT_DONE')
            if not marker('S3_END'):
                s3_finalize()
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§6/7', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    try:
        registered_parent_intact('S3H-§8')
        g3_smoke()
        g3_formal()
        g10_resume()
        g11_run()
        parent2_end()
    except SystemExit:
        raise
    except Exception as e:
        halt('S3H-§8', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    rep(f"## S3H-ALL ✓ {utc()}", "- S3-H 全部项完成（父研究第二窗口为 D11 补充结果）")
    CUR['phase'] = 'DONE'
    save_cur()
    log('orchestrator DONE')

if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except BaseException as e:
        halt('S3H-ORCH', f'未捕获异常 {type(e).__name__}: {e}', traceback.format_exc())
