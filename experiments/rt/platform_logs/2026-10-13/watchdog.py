#!/usr/bin/env python3
"""H100 rt queue watchdog v3 (CPU background loop, not part of the rt queue).
Per 执行单 H-2 §0: sample nvidia-smi utilization every minute; if ALL GPUs of a
rank read 0% for 10 consecutive samples while the process is alive -> hang:
evidence -> kill -> wait GPUs < 1GB -> restart with the exact same command.
Row counts are NOT a hang signal. Max 3 auto-restarts per rank per item;
the 4th hang -> pause the item, mark ⏸.
"""
import subprocess, time, os, glob, json

POUTH = '/inspire/hdd/project/ai4education/public/why/platform_out_h100'
STATE = f'{POUTH}/watchdog_state.json'
REPORT = f'{POUTH}/report_h100.md'
ERRLOG = f'{POUTH}/watchdog.err.log'
ZERO_LIMIT = 10        # consecutive 0% samples (1/min) -> hang
MAX_RESTARTS = 3       # per rank per item; 4th hang -> pause

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
    r = subprocess.run(['bash','-c',f'kill -0 {pid} 2>/dev/null && echo Y || echo N'],
                       capture_output=True, text=True)
    return r.stdout.strip() == 'Y'

def all_utils():
    """return dict gpu_index -> util% (int); empty dict on failure."""
    r = subprocess.run(['bash','-c',
        'nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader,nounits'],
        capture_output=True, text=True)
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
    r = subprocess.run(['bash','-c',
        f'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i {idx}'],
        capture_output=True, text=True)
    try:
        return [int(x.strip()) for x in r.stdout.split() if x.strip()]
    except Exception:
        return []

def collect_evidence(project, rank, pid):
    ts = time.strftime('%Y%m%d_%H%M%S')
    base = f'{POUTH}/hang_{safe_tag(project)}_r{safe_tag(rank)}_{ts}'
    subprocess.run(['bash','-c',
        f'if command -v py-spy >/dev/null 2>&1; then py-spy dump --pid {pid}; else echo "py-spy not installed -> skipped"; fi > {base}_pyspy.txt 2>&1'],
        capture_output=True)
    subprocess.run(['bash','-c',
        f'top -b -n1 -H -p {pid} 2>/dev/null | head -20 > {base}_top.txt'], capture_output=True)
    subprocess.run(['bash','-c',
        f'nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv > {base}_smi.txt 2>&1; '
        f'nvidia-smi topo -m >> {base}_smi.txt 2>&1'], capture_output=True)
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

def handle_hang(rk, now):
    """evidence -> kill -> wait GPUs <1GB -> restart (or pause at 4th hang)."""
    pid = rk['pid']
    ev = collect_evidence(rk['project'], rk['rank'], pid)
    ev_names = ', '.join(e.split('/')[-1] for e in ev)
    subprocess.run(['bash','-c',f'kill {pid}'], capture_output=True)
    for _ in range(60):
        time.sleep(5)
        m = gpu_mem(rk['gpus'])
        if m and all(x < 1000 for x in m): break
    logp = rk.get('log')
    if logp and os.path.exists(logp):
        try: os.replace(logp, logp + '.pre_' + time.strftime('%Y%m%d_%H%M%S'))
        except Exception: pass
    if rk.get('restarts', 0) >= MAX_RESTARTS:
        append_report(
            f"\n## {safe_tag(rk['project'])} ⏸ 自动\n"
            f"待裁决：rank {rk['rank']} 第 4 次卡死（全部 GPU 连续 {ZERO_LIMIT} 分钟 0% 且进程存活），按 H-2 停止本项，由 leader 检查裁定。\n"
            f"- 取证文件: {ev_names}\n"
            f"- 时间: {now_str()}\n")
        rk['status'] = 'paused'
        append_report(f"- {now_str()} | rank {rk['rank']} | 停止（第4次GPU全0%卡死）| 取证 {ev_names}\n")
        return
    r = subprocess.run(['bash','-c', rk['cmd']], capture_output=True, text=True)
    newpid = None
    for line in (r.stdout or '').splitlines():
        line = line.strip()
        if line.startswith('NEWPID='):
            try: newpid = int(line.split('=',1)[1])
            except Exception: newpid = None
    if newpid:
        rk['pid'] = newpid
    rk['restarts'] = rk.get('restarts', 0) + 1
    rk['zero_streak'] = 0
    rk['started_at'] = now
    save_state(rk)
    append_report(
        f"- {now_str()} | rank {rk['rank']} | GPU 全 0% 连续 ≥{ZERO_LIMIT}min | 自动重启 #{rk['restarts']}"
        f"| 取证 {ev_names} | 新 pid {rk['pid']}\n")

def main():
    while True:
        try:
            st = load_state()
            now = time.time()
            utils = all_utils()
            dirty = False
            for rk in st.get('ranks', []):
                try:
                    if rk.get('status') != 'running':
                        continue
                    pid = rk['pid']
                    if not alive(pid):
                        rk['zero_streak'] = 0
                        continue  # exited: main agent checks exit codes
                    if not utils:
                        continue  # sampling failed this round; skip
                    vals = [utils.get(int(g), -1) for g in rk['gpus']]
                    if vals and all(v == 0 for v in vals):
                        rk['zero_streak'] = rk.get('zero_streak', 0) + 1
                        if rk['zero_streak'] >= ZERO_LIMIT:
                            append_report(
                                f"- {now_str()} | rank {rk['rank']} | 判定卡死: 全部 GPU 连续 {rk['zero_streak']} 次 0%（pid {pid}）\n")
                            handle_hang(rk, now)
                            dirty = True
                    else:
                        if rk.get('zero_streak', 0) != 0:
                            rk['zero_streak'] = 0
                            dirty = True
                except Exception as e:
                    log_err(f"{rk.get('project')} r{rk.get('rank')}: {type(e).__name__}: {e}")
            if dirty:
                save_state(st)
        except Exception as e:
            log_err(f"loop: {type(e).__name__}: {e}")
        time.sleep(60)

if __name__ == '__main__':
    main()
