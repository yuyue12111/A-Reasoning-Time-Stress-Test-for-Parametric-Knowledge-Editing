#!/usr/bin/env python3
"""H100 rt queue watchdog v3 (CPU background loop, not part of the rt queue).
Per 执行单 H-2 §0: sample nvidia-smi utilization every minute; if ALL GPUs of a
rank read 0% for 10 consecutive samples while the process is alive -> hang:
evidence -> kill -> wait GPUs < 1GB -> restart with the exact same command.
Row counts are NOT a hang signal. Max 3 auto-restarts per rank per item;
the 4th hang -> pause the item, mark ⏸.
"""
import subprocess, time, os, glob, json, fcntl

POUTH = '/inspire/hdd/project/ai4education/public/why/platform_out_h100'
STATE = f'{POUTH}/watchdog_state.json'
REPORT = f'{POUTH}/report_h100.md'
ERRLOG = f'{POUTH}/watchdog.err.log'
ZERO_LIMIT = 10        # consecutive 0% samples (1/min) -> hang
MAX_RESTARTS = 3       # per rank per item; 4th hang -> pause
LOCK = '/tmp/why_wd_state.lock'   # shared with orch_s3h.py (node-local)
GRACE_S = 1800         # leader decision: no hang counting in the first 30 min after a (re)start (model load)

class _Lock:
    def __enter__(self):
        self.fh = open(LOCK, 'a')
        fcntl.flock(self.fh, fcntl.LOCK_EX)
        return self
    def __exit__(self, *a):
        fcntl.flock(self.fh, fcntl.LOCK_UN)
        self.fh.close()

def safe_tag(s):
    return ''.join(c for c in str(s) if c.isalnum() or c in '-_.')

def load_state():
    try:
        with open(STATE) as f: return json.load(f)
    except Exception:
        return {"ranks": []}

def save_state(st):
    tmp = STATE + '.tmp'
    with open(tmp, 'w') as f: json.dump(st, f, indent=1)
    os.replace(tmp, STATE)

def alive(pid):
    """/proc/<pid> exists and is not a zombie (kill -0 succeeds on zombies)."""
    try:
        with open(f'/proc/{int(pid)}/stat') as f:
            return f.read().rsplit(')', 1)[1].split()[0] != 'Z'
    except Exception:
        return False

def all_utils():
    """return dict gpu_index -> util% (int); empty dict on failure."""
    try:
        r = subprocess.run(['bash','-c',
            'nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        log_err('nvidia-smi timeout (all_utils)')
        return {}
    out = {}
    try:
        for line in r.stdout.strip().splitlines():
            idx, util = [x.strip() for x in line.split(',')]
            out[int(idx)] = int(util)
    except Exception:
        return {}
    return out

def gpu_vals(gpus):
    u = all_utils()
    if not u: return []
    return [u.get(int(g), -1) for g in gpus]

def gpu_mem(gpus):
    idx = ','.join(str(g) for g in gpus)
    try:
        r = subprocess.run(['bash','-c',
            f'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i {idx}'],
            capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        log_err(f'nvidia-smi timeout (gpu_mem {idx})')
        return []                 # busy() treats [] as busy -> pause, never a restart onto unknown cards
    try:
        return [int(x.strip()) for x in r.stdout.split() if x.strip()]
    except Exception:
        return []

def _run_quiet(args, timeout):
    try:
        subprocess.run(args, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log_err(f'timeout {timeout}s: {str(args)[:120]}')

def collect_evidence(project, rank, pid):
    ts = time.strftime('%Y%m%d_%H%M%S')
    base = f'{POUTH}/hang_{safe_tag(project)}_r{safe_tag(rank)}_{ts}'
    _run_quiet(['bash','-c',
        f'if command -v py-spy >/dev/null 2>&1; then py-spy dump --pid {pid}; else echo "py-spy not installed -> skipped"; fi > {base}_pyspy.txt 2>&1'],
        120)
    _run_quiet(['bash','-c',
        f'top -b -n1 -H -p {pid} 2>/dev/null | head -20 > {base}_top.txt'], 120)
    _run_quiet(['bash','-c',
        f'nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv > {base}_smi.txt 2>&1; '
        f'nvidia-smi topo -m >> {base}_smi.txt 2>&1'], 120)
    return [f'{base}_pyspy.txt', f'{base}_top.txt', f'{base}_smi.txt']

def append_report(text):
    try:
        with open(REPORT,'a') as f: f.write(text + '\n')
    except Exception:
        pass

def now_str():
    return time.strftime('%F %T')

def log_err(msg):
    try:
        with open(ERRLOG,'a') as f: f.write(f"{now_str()} | {msg}\n")
    except Exception:
        pass

def utc():
    return time.strftime('%F %T', time.gmtime())

def _find(st, snap):
    for rk in st.get('ranks', []):
        if rk.get('project') == snap['project'] and rk.get('rank') == snap['rank'] and rk.get('pid') == snap['pid']:
            return rk
    return None

def _pause(snap, why, ev_names):
    with _Lock():
        st = load_state()
        rk = _find(st, snap)
        if rk is not None:
            rk['status'] = 'paused'
            save_state(st)
    append_report(
        f"\n## {safe_tag(snap['project'])} ⏸ {utc()}\n"
        f"待裁决：rank {snap['rank']} {why}；按 H-2 停止本项（不重启），由 leader 检查裁定。\n"
        f"- 取证文件: {ev_names}\n")

def handle_hang(snap, now):
    """evidence -> TERM -> (KILL) -> wait process gone and GPUs <1GB -> restart, or pause.
    ``snap`` is a copy of the entry, already marked 'restarting' under the lock."""
    pid = snap['pid']
    ev = collect_evidence(snap['project'], snap['rank'], pid)
    ev_names = ', '.join(e.split('/')[-1] for e in ev)
    def busy():
        m = gpu_mem(snap['gpus'])
        return alive(pid) or not m or any(x >= 1000 for x in m), m
    _run_quiet(['kill', '-TERM', str(pid)], 30)
    b, m = True, []
    for _ in range(60):
        time.sleep(5)
        b, m = busy()
        if not b:
            break
    if b:
        _run_quiet(['kill', '-KILL', str(pid)], 30)
        for _ in range(12):
            time.sleep(5)
            b, m = busy()
            if not b:
                break
    if b:
        return _pause(snap, f'kill(TERM→KILL) 后进程仍在或 GPU {snap["gpus"]} 显存 {m} 未 <1GB', ev_names)
    if snap.get('restarts', 0) >= MAX_RESTARTS:
        return _pause(snap, f'第 4 次卡死（全部 GPU 连续 {ZERO_LIMIT} 分钟 0% 且进程存活）', ev_names)
    logp = snap.get('log')
    if logp and os.path.exists(logp):
        try: os.replace(logp, logp + '.pre_' + time.strftime('%Y%m%d_%H%M%S'))
        except Exception: pass
    with _Lock():
        st = load_state()
        rk = _find(st, snap)
        if rk is None or rk.get('status') != 'restarting':
            log_err(f"{snap.get('project')} r{snap.get('rank')}: entry replaced by orchestrator; no restart")
            return
        try:
            r = subprocess.run(['bash', '-c', rk['cmd']], capture_output=True, text=True, timeout=120)
            out = r.stdout or ''
        except subprocess.TimeoutExpired:
            out = ''
        newpid = None
        for line in out.splitlines():
            line = line.strip()
            if line.startswith('NEWPID='):
                try: newpid = int(line.split('=', 1)[1])
                except Exception: newpid = None
        if not newpid:
            rk['status'] = 'paused'
            save_state(st)
            append_report(f"\n## {safe_tag(snap['project'])} ⏸ {utc()}\n待裁决：rank {snap['rank']} 重启命令未返回 NEWPID（或 120s 超时），未跟踪\n")
            return
        rk.update(pid=newpid, restarts=rk.get('restarts', 0) + 1, zero_streak=0, started_at=time.time(), status='running')
        save_state(st)
    append_report(
        f"- {now_str()} | rank {snap['rank']} | GPU 全 0% 连续 ≥{ZERO_LIMIT}min | 自动重启 #{rk['restarts']}"
        f"| 取证 {ev_names} | 新 pid {newpid}\n")

def main():
    while True:
        hangs = []
        try:
            now = time.time()
            utils = all_utils()       # sampled before taking the shared lock: a hung nvidia-smi must never hold it
            with _Lock():
                st = load_state()
                dirty = False
                for rk in st.get('ranks', []):
                    try:
                        if rk.get('status') != 'running':
                            continue
                        pid = rk['pid']
                        if not alive(pid):
                            if rk.get('zero_streak', 0):
                                rk['zero_streak'] = 0
                                dirty = True
                            continue  # exited: the orchestrator checks completion
                        if not utils or now - rk.get('started_at', 0) < GRACE_S:
                            continue
                        vals = [utils.get(int(g), -1) for g in rk['gpus']]
                        if vals and all(v == 0 for v in vals):
                            rk['zero_streak'] = rk.get('zero_streak', 0) + 1
                            dirty = True          # v3 never saved the streak, so it could not reach ZERO_LIMIT
                            if rk['zero_streak'] >= ZERO_LIMIT:
                                append_report(
                                    f"- {now_str()} | rank {rk['rank']} | 判定卡死: 全部 GPU 连续 {rk['zero_streak']} 次 0%（pid {pid}）\n")
                                rk['status'] = 'restarting'
                                hangs.append(dict(rk))
                        elif rk.get('zero_streak', 0) != 0:
                            rk['zero_streak'] = 0
                            dirty = True
                    except Exception as e:
                        log_err(f"{rk.get('project')} r{rk.get('rank')}: {type(e).__name__}: {e}")
                if dirty:
                    save_state(st)
        except Exception as e:
            log_err(f"loop: {type(e).__name__}: {e}")
        for snap in hangs:
            try:
                handle_hang(snap, time.time())
            except Exception as e:
                log_err(f"handle_hang {snap.get('project')} r{snap.get('rank')}: {type(e).__name__}: {e}")
                _pause(snap, f'看门狗处理异常 {type(e).__name__}', '-')
        time.sleep(60)

if __name__ == '__main__':
    main()
