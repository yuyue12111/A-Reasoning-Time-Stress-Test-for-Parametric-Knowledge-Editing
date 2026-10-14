#!/usr/bin/env python3
"""S3-H overnight orchestrator (tmux unavailable offline; runs detached via nohup setsid).

执行单 S3-H 全流程自动执行。任何校验失败 -> 写 ⏸ 块到 report_h100.md 并退出（不重试、不硬闯、不删改数据）。
§0 裁决: error 行按意图判通过（每个 case 有 valid 行即可）。
补跑阶梯(§1.2): rt.run 40000->26000->18000; 70B 34000->26000->18000。
Study 3 与父研究(s2 分片)内容禁读；只看行数/error 行数/GPU/进度行。例外: §6 与 §8.1a 冒烟旧事实文件
（单授权肉眼检查 -> 夜间以自动启发检查代替, 回报中注明待 leader 复核）。
"""
import subprocess, time, os, sys, json, glob, re, threading, traceback

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

def halt(item, msg):
    rep(f"## {item} ⏸ {utc()}",
        f"待裁决：{msg}\n（orchestrator 夜间自动停止，不重试不硬闯；时间 {utc()} UTC）")
    CUR['phase'] = f'HALTED@{item}'
    save_cur()
    log(f"HALT {item}: {msg}")
    sys.exit(1)

def sh(cmd, timeout=1800):
    return subprocess.run(['bash', '-c', cmd], capture_output=True, text=True, timeout=timeout)

def sh_out(cmd, timeout=1800):
    r = sh(cmd, timeout)
    return r.stdout.strip(), r.returncode

def wait_gpus_free(timeout_s=1200):
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        out, _ = sh_out('nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits')
        vals = [int(x) for x in out.split() if x.strip().isdigit()]
        if vals and all(v < 1024 for v in vals):
            return True
        time.sleep(10)
    return False

def gpu_mem(gpus):
    idx = ','.join(str(g) for g in gpus)
    out, _ = sh_out(f'nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits -i {idx}')
    return [int(x) for x in out.split() if x.strip().isdigit()]

def assert_gpus_free(gpus, item):
    for g in gpus:
        m = gpu_mem([g])
        if m and m[0] >= 1024:
            halt(item, f'GPU {g} memory.used={m[0]}MiB >= 1GB 启动前置不满足')
    out, _ = sh_out('pgrep -af "rt[.](run|pool|deltas)" || true')
    if out:
        halt(item, f'pgrep rt.(run|pool|deltas) 非空: {out[:300]}')

def update_watchdog(project, entries):
    ranks = []
    for e in entries:
        ranks.append({"type": "R", "project": project, "rank": e['rank'], "world": e.get('world', 8),
                      "pid": e['pid'], "gpus": e['gpus'], "zero_streak": 0,
                      "outglob": e.get('outglob', ''), "log": e.get('log', ''),
                      "cmd": e['cmd'], "restarts": 0, "started_at": time.time(), "status": "running"})
    with open(f'{POUTH}/watchdog_state.json', 'w') as f:
        json.dump({"ranks": ranks, "note": "watchdog v3 GPU util rule"}, f, indent=1)

def wd_pause_all():
    try:
        with open(f'{POUTH}/watchdog_state.json') as f:
            st = json.load(f)
        for rk in st.get('ranks', []):
            rk['status'] = 'stopped'
        with open(f'{POUTH}/watchdog_state.json', 'w') as f:
            json.dump(st, f, indent=1)
    except Exception:
        pass

def wait_all_exit(entries, project, poll=60, stale_hours=10):
    t0 = time.time()
    while True:
        alive = [e['rank'] for e in entries if os.path.exists(f"/proc/{e['pid']}")]
        CUR['detail'] = f"{project}: alive ranks {alive}"
        save_cur()
        if not alive:
            return True
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

def relaunch_rank(project, e, tokens, extra_args=''):
    try:
        os.replace(e['log'], e['log'] + f".pre_{time.strftime('%Y%m%d_%H%M%S')}")
    except Exception:
        pass
    newcmd = re.sub(r'--max-batch-tokens \d+', f'--max-batch-tokens {tokens}', e['cmd'])
    if extra_args and extra_args not in newcmd:
        newcmd = newcmd.replace('& echo NEWPID=$!', f'{extra_args} & echo NEWPID=$!')
    out, rc = sh_out(newcmd)
    newpid = None
    for line in out.splitlines():
        if line.startswith('NEWPID='):
            newpid = int(line.split('=', 1)[1])
    if not newpid:
        halt(project, f"rank {e['rank']} 阶梯续跑启动失败 out={out[:200]}")
    e['pid'] = newpid
    try:
        with open(f'{POUTH}/watchdog_state.json') as f:
            st = json.load(f)
        for rk in st.get('ranks', []):
            if rk.get('rank') == e['rank']:
                rk['pid'] = newpid
                rk['cmd'] = newcmd
                rk['zero_streak'] = 0
                rk['started_at'] = time.time()
        with open(f'{POUTH}/watchdog_state.json', 'w') as f:
            json.dump(st, f, indent=1)
    except Exception:
        pass
    log(f"{project} rank {e['rank']} relaunched tokens={tokens} pid={newpid}")

def start_rt_ranks(project, world, cmd_tpl, log_tpl, outglob_tpl, gpus_of_rank=None, tokens=40000):
    pids, entries = [], []
    for r in range(world):
        gpus = gpus_of_rank(r) if gpus_of_rank else [r]
        gpu_s = ','.join(str(g) for g in gpus)
        cmd = cmd_tpl.format(rank=r, tokens=tokens, gpus=gpu_s)
        logp = log_tpl.format(rank=r)
        full = (f"cd {PROJH} && {ENV_OFF} && "
                f"CUDA_VISIBLE_DEVICES={gpu_s} nohup {cmd} > {logp} 2>&1 & echo NEWPID=$!")
        out, rc = sh_out(full)
        newpid = None
        for line in out.splitlines():
            if line.startswith('NEWPID='):
                newpid = int(line.split('=', 1)[1])
        if not newpid:
            halt(project, f'rank {r} 启动失败 rc={rc} out={out[:200]}')
        pids.append(newpid)
        entries.append({"rank": r, "pid": newpid, "gpus": gpus, "cmd": full, "log": logp,
                        "outglob": outglob_tpl.format(rank=r), "world": world})
        time.sleep(2)
    update_watchdog(project, entries)
    return pids, entries

# ---------------- §2 ----------------

def phase_s2():
    CUR['phase'] = 'S2 wait-bundle'; save_cur()
    while not os.path.exists(BUNDLE):
        time.sleep(60)
    CUR['phase'] = 'S2 sync'; save_cur()
    out, _ = sh_out(f'sha256sum {BUNDLE}')
    h = out.split()[0] if out else ''
    if h != BUNDLE_SHA:
        halt('S3H-§2', f'bundle sha256 mismatch: got {h} expect {BUNDLE_SHA}')
    sh('pkill -f "python -m [r]t.run" || true')
    time.sleep(5)
    sh('pkill -9 -f "python -m [r]t.run" || true')
    if not wait_gpus_free():
        halt('S3H-§2', "pkill G10' 后 20 分钟内 8 卡未全部 <1GB")
    wd_pause_all()
    rep(f"## S3H-§2 G10'-stop ✓ {utc()}",
        "- G10' 进程已全部停止（不删除任何分片），8 卡 <1GB；bundle sha256 校验通过")
    os.chdir(PROJH)
    out, rc = sh_out('git status --porcelain --untracked-files=no')
    if out:
        halt('S3H-§2', f'git status dirty: {out[:300]}')
    if sh(f'git fetch {BUNDLE} claude/paper-review-understanding-8732e6:refs/remotes/bundle/s3', 600).returncode != 0:
        halt('S3H-§2', 'git fetch bundle failed')
    if sh('git checkout -B claude/paper-review-understanding-8732e6 refs/remotes/bundle/s3', 600).returncode != 0:
        halt('S3H-§2', 'git checkout -B failed')
    head, _ = sh_out('git log -1 --format=%h')
    if head != EXPECT_HEAD:
        halt('S3H-§2', f'HEAD={head} expect {EXPECT_HEAD}')
    if sh(f'git merge-base --is-ancestor {FREEZE_BASE} HEAD').returncode != 0:
        halt('S3H-§2', 'freeze commit not in history')
    diff = sh(f'git diff --stat {FREEZE_BASE} HEAD -- {FROZEN_LIST}').stdout
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
    ee, rc = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src:source/EasyEdit python3 -c 'import easyeditor; print(\"EASYEDIT_OK\")'")
    skip_s3 = 'EASYEDIT_OK' not in ee
    out, _ = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -c \"import json,os;"
                    f"ids=[json.loads(l)['case_id'] for l in open('experiments/rt/pools/study2/manifest_r1qwen32b_fresh.jsonl')];"
                    f"print('existing fresh deltas:',sum(os.path.exists(f'deltas/r1qwen32b/ROME/cf/{{c}}.pt') for c in ids))\"")
    if 'existing fresh deltas: 0' not in out:
        halt('S3H-§2', f'fresh deltas not clean: {out[:200]}')
    if os.path.exists(f'{PROJH}/results/rt/s3') or os.path.exists(f'{PROJH}/results/rt/pool_s3'):
        halt('S3H-§2', 'results/rt/s3 or results/rt/pool_s3 already exists')
    sh_out(f'touch {SHARE}/S3_CODE_OK')
    rep(f"## S3H-§2 ✓ {utc()}",
        f"- bundle sha256 OK; HEAD={head}; freeze-in-history; 冻结清单无改动; rt tests 193 passed; study3.tests.test_confirm OK; CODE_HASH_OK; fresh deltas=0; s3/pool_s3 不存在\n"
        f"- EasyEdit: {'EASYEDIT_OK' if not skip_s3 else 'IMPORT FAILED -> 按 §2.9 跳过 §3–§7 直接做 §8'}\n"
        f"- touch {SHARE}/S3_CODE_OK")
    return skip_s3

# ---------------- §3/§5 deltas ----------------

def parse_summarize(txt):
    try:
        return json.loads(txt)
    except Exception:
        pass
    d = {}
    for k in ('cases', 'ok', 'errors', 'editor_nan', 'max_rank', 'max_rel_err', 'median_p_target_after'):
        m = re.search(rf'{k}\s*[:=]\s*([0-9.eE+-]+)', txt)
        if m:
            d[k] = m.group(1)
    return d if d else None

def fnum(d, k):
    try:
        return float(d.get(k))
    except Exception:
        return None

def deltas_subdir(tag):
    """derive the deltas_logs subdir actually used by this tag's run logs."""
    for rr in range(4):
        lp = f'{PROJH}/logs/rt/{tag}_r{rr}.out'
        if os.path.exists(lp):
            m = re.search(r'results/rt/deltas_logs/([A-Za-z0-9_.-]+)/', open(lp, errors='replace').read())
            if m:
                return m.group(1)
    return 's3fresh' if tag == 's3fresh' else 's3ext'

def deltas_phase(tag, cfg, expect_n, item, smoke=True):
    CUR['phase'] = item; save_cur()
    env = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; "
           f"unset WHYAAAI_DTYPE WHYAAAI_MODEL")
    world, gpus_of = 4, (lambda r: [2*r, 2*r+1])
    if smoke:
        smoke_log = f'{PROJH}/logs/rt/{tag}_smoke.out'
        sm = (f"{env} && CUDA_VISIBLE_DEVICES=0,1 python3 -m rt.deltas run --config {cfg} --model-path {M32} "
              f"--model-parallel --rank 0 --world 4 --device 0 --limit 2 > {smoke_log} 2>&1; echo rc=$?")
        r = sh(sm, 14400)
        rc = r.stdout.strip().split('rc=')[-1]
        if rc != '0':
            oom = os.path.exists(smoke_log) and 'OutOfMemoryError' in open(smoke_log, errors='replace').read()
            if not oom:
                halt(item, f'冒烟失败(非OOM) rc={rc}; tail: {sh_out(f"tail -5 {smoke_log}")[0][:400]}')
            rep(f"## {item} smoke-OOM-retry ⏸→run {utc()}", '- 冒烟 OOM -> 按 §3.1 改每进程 4 卡 world 2 再冒烟一次')
            world, gpus_of = 2, (lambda r: [4*r+i for i in range(4)])
            smoke_log = f'{PROJH}/logs/rt/{tag}_smoke2.out'
            sm = (f"{env} && CUDA_VISIBLE_DEVICES=0,1,2,3 python3 -m rt.deltas run --config {cfg} --model-path {M32} "
                  f"--model-parallel --rank 0 --world 2 --device 0 --limit 2 > {smoke_log} 2>&1; echo rc=$?")
            r = sh(sm, 14400)
            rc = r.stdout.strip().split('rc=')[-1]
            if rc != '0':
                halt(item, f'4卡 world2 冒烟仍失败 rc={rc}; tail: {sh_out(f"tail -5 {smoke_log}")[0][:400]}')
        sub0 = deltas_subdir(tag)
        s0, _ = sh_out(f"{env} && python3 -m rt.deltas summarize \"results/rt/deltas_logs/{sub0}/r1qwen32b_ROME_cf_r*.jsonl\"", 3600)
        d = parse_summarize(s0)
        if not d:
            halt(item, f'冒烟 summarize 无法解析: {s0[:400]}')
        if not (fnum(d, 'ok') == 2 and fnum(d, 'editor_nan') == 0 and fnum(d, 'max_rel_err') is not None
                and fnum(d, 'max_rel_err') < 1e-4 and fnum(d, 'median_p_target_after') is not None
                and fnum(d, 'median_p_target_after') >= 0.9):
            halt(item, f'冒烟通过条件未满足: {json.dumps(d)[:400]}')
        rep(f"## {item} smoke ✓ {utc()}", f"- summarize: {json.dumps(d)[:300]}")
    entries = []
    for rr in range(world):
        gs = gpus_of(rr)
        gpu_s = ','.join(map(str, gs))
        assert_gpus_free(gs, item)
        cmd = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; "
               f"unset WHYAAAI_DTYPE WHYAAAI_MODEL && CUDA_VISIBLE_DEVICES={gpu_s} nohup python3 -m rt.deltas run "
               f"--config {cfg} --model-path {M32} --model-parallel --rank {rr} --world {world} --device 0 "
               f"> logs/rt/{tag}_r{rr}.out 2>&1 & echo NEWPID=$!")
        out, _ = sh_out(cmd)
        pid = None
        for line in out.splitlines():
            if line.startswith('NEWPID='):
                pid = int(line.split('=', 1)[1])
        if not pid:
            halt(item, f'正式 rank {rr} 启动失败 {out[:200]}')
        entries.append({"rank": rr, "pid": pid, "gpus": gs, "cmd": cmd,
                        "log": f'{PROJH}/logs/rt/{tag}_r{rr}.out', "outglob": '', "world": world})
    update_watchdog(item, entries)
    if not wait_all_exit(entries, item, stale_hours=12):
        halt(item, '正式编辑 12 小时未结束')

    sub = deltas_subdir(tag)
    def summarize():
        s, _ = sh_out(f"{env} && python3 -m rt.deltas summarize \"results/rt/deltas_logs/{sub}/r1qwen32b_ROME_cf_r*.jsonl\"", 3600)
        return s
    def passed(d):
        return bool(d) and fnum(d, 'cases') == expect_n and fnum(d, 'ok') == expect_n and \
            fnum(d, 'editor_nan') == 0 and fnum(d, 'max_rank') == 1 and \
            fnum(d, 'max_rel_err') is not None and fnum(d, 'max_rel_err') < 1e-4
    s = summarize()
    d = parse_summarize(s)
    if not passed(d):
        rep(f"## {item} retry-errors ⏸→run {utc()}", f"- summarize 未过: {json.dumps(d or {})[:400]}\n- 按单原命令加 --retry-errors 重跑一次")
        entries2 = []
        for rr in range(world):
            gs = gpus_of(rr)
            gpu_s = ','.join(map(str, gs))
            cmd = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src:source/EasyEdit WHYAAAI_DEVICE_MAP=balanced; "
                   f"unset WHYAAAI_DTYPE WHYAAAI_MODEL && CUDA_VISIBLE_DEVICES={gpu_s} nohup python3 -m rt.deltas run "
                   f"--config {cfg} --model-path {M32} --model-parallel --rank {rr} --world {world} --device 0 --retry-errors "
                   f"> logs/rt/{tag}_r{rr}_retry.out 2>&1 & echo NEWPID=$!")
            out, _ = sh_out(cmd)
            pid = None
            for line in out.splitlines():
                if line.startswith('NEWPID='):
                    pid = int(line.split('=', 1)[1])
            entries2.append({"rank": rr, "pid": pid, "gpus": gs, "cmd": cmd,
                             "log": f'{PROJH}/logs/rt/{tag}_r{rr}_retry.out', "outglob": '', "world": world})
        update_watchdog(item + '-retry', entries2)
        if not wait_all_exit(entries2, item, stale_hours=12):
            halt(item, 'retry-errors 12 小时未结束')
        s = summarize()
        d = parse_summarize(s)
        if not passed(d):
            halt(item, f'retry-errors 后仍未过: {json.dumps(d or {})[:400]}')
    with open(f'{POUTH}/summarize_S3_{"fresh" if tag=="s3fresh" else "ext"}.json', 'w') as f:
        f.write(s)
    return True

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
        if not mp:
            halt('S3H-§4', f'{t} model path 读取失败')
        models.append((t, mp))
        rep(f"## S3H-§4 model-path {utc()}", f"- {t} {mp}")
    for t, mp in models:
        CUR['phase'] = f'S4 screen {t}'; save_cur()
        assert_gpus_free(list(range(8)), 'S3H-§4')
        entries = []
        for r in range(8):
            cmd = (f"cd {PROJH} && {ENV_OFF} && CUDA_VISIBLE_DEVICES={r} WHYAAAI_MODEL={mp} PYTHONPATH=src "
                   f"nohup python3 -m rt.pool screen --config experiments/rt/pool_screen_s3.yaml --model-tag {t} "
                   f"--rank {r} --world 8 > logs/rt/s3screen_{t}_r{r}.out 2>&1 & echo NEWPID=$!")
            out, _ = sh_out(cmd)
            pid = None
            for line in out.splitlines():
                if line.startswith('NEWPID='):
                    pid = int(line.split('=', 1)[1])
            if not pid:
                halt('S3H-§4', f'{t} rank {r} 启动失败 {out[:200]}')
            entries.append({"rank": r, "pid": pid, "gpus": [r], "cmd": cmd,
                            "log": f'{PROJH}/logs/rt/s3screen_{t}_r{r}.out', "outglob": '', "world": 8})
        update_watchdog(f'S4-{t}', entries)
        if not wait_all_exit(entries, f'S4-{t}', stale_hours=10):
            halt('S3H-§4', f'{t} screen 10 小时未结束')
        for e in entries:
            if not exit_ok(e['log']):
                rep(f"## S3H-§4 {t} r{e['rank']} rerun ⏸→run {utc()}", '- rank 无 done 行 -> 原命令重跑一次')
                out, _ = sh_out(e['cmd'])
                for line in out.splitlines():
                    if line.startswith('NEWPID='):
                        e['pid'] = int(line.split('=', 1)[1])
                update_watchdog(f'S4-{t}', entries)
        wait_all_exit(entries, f'S4-{t}', stale_hours=6)
        for e in entries:
            if not exit_ok(e['log']):
                halt('S3H-§4', f"{t} rank {e['rank']} 重跑后仍无 done 行")
        out, _ = sh_out(f"{env} python3 -m rt.pool qualify --config experiments/rt/pool_screen_s3.yaml --model-tag {t}", 3600)
        rep(f"## S3H-§4 qualify {t} ✓ {utc()}", f"- {out[:300]}")
    out, _ = sh_out(f"{env} python3 -m study3.ext_manifest", 3600)
    rep(f"## S3H-§4 ext_manifest ✓ {utc()}", f"- {out[:400]}")
    mf = f'{PROJH}/experiments/rt/pools/study3/manifest_r1qwen32b_ext.jsonl'
    if not os.path.exists(mf):
        halt('S3H-§4', 'manifest_r1qwen32b_ext.jsonl 未生成')
    sh(f"echo \"$(sha256sum {mf}) n=$(wc -l < {mf}) $(date -u +%FT%TZ)\" > {SHARE}/S3_EXT_MANIFEST.txt")
    sh(f"cp -a {PROJH}/experiments/rt/pools/study3 {POUTH}/pools_study3")
    sh_out(f'touch {SHARE}/S3_EXT_MANIFEST_DONE')
    n, _ = sh_out(f'wc -l < {mf}')
    rep(f"## S3H-§4 ✓ {utc()}", f"- manifest n={n.strip()}; S3_EXT_MANIFEST.txt 已写; pools_study3 已拷; touch S3_EXT_MANIFEST_DONE")
    return int(n.strip())

# ---------------- smoke heuristics ----------------

EN_BAN = re.compile(r'[^\x09\x0a\x0d\x20-\x7e]')

def heuristic_english(paths, item, min_words=4):
    checked = 0
    for p in paths:
        with open(p, errors='replace') as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get('error'):
                    continue
                def walk(o):
                    if isinstance(o, str):
                        yield o
                    elif isinstance(o, dict):
                        for v in o.values():
                            yield from walk(v)
                    elif isinstance(o, list):
                        for v in o:
                            yield from walk(v)
                texts = [v for v in walk(d) if len(v) > 20]
                if not texts:
                    continue
                t = max(texts, key=len)
                checked += 1
                words = re.findall(r'[A-Za-z]+', t)
                bad = len(EN_BAN.findall(t)) / max(len(t), 1)
                if len(words) < min_words or bad > 0.05:
                    halt(item, f'冒烟启发检查未过: {p} words={len(words)} bad={bad:.3f} head={t[:120]!r}')
    if checked == 0:
        halt(item, f'冒烟启发未找到响应文本: {paths}')
    return checked

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
    nchk = heuristic_english(files, 'S3H-§6')
    rep(f"## S3H-§6 ✓ {utc()}",
        f"- 退出码 0; base=8 行, rome_N=8 行, 0 error\n"
        f"- 连贯性: 自动启发通过（{nchk} 条响应文本；夜间无人值守，**待 leader 早上肉眼复核** results/rt/s3smoke/）")

# ---------------- §7 generation ----------------

def s3_progress():
    out, rc = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -m study3.end_entry --stopped-at progress --out /tmp/s3_progress.json", 600)
    try:
        d = json.load(open('/tmp/s3_progress.json'))
    except Exception:
        halt('S3H-§7', f'end_entry progress 解析失败 rc={rc}: {out[:300]}')
    keys = {k: d.get(k) for k in ('n_complete_efficacy', 'valid_rows', 'error_rows')}
    log(f"progress: {json.dumps(keys)[:300]}")
    return keys

def gen_phase(kind, expect_n, item, share_flag):
    CUR['phase'] = item; save_cur()
    assert_gpus_free(list(range(8)), item)
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study3_r1qwen32b_{kind}.yaml "
           f"--conditions base,rome_N --rank {{rank}} --world 8 --device cuda --batch-size 16 "
           f"--max-batch-tokens {{tokens}}")
    pids, entries = start_rt_ranks(item, 8, tpl, f'{PROJH}/logs/rt/s3g_{kind}_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s3/{{cond}}_r{{rank}}of8.jsonl')
    if not wait_all_exit(entries, item, stale_hours=14):
        halt(item, '生成 14 小时未结束')
    li = 0
    while True:
        keys = s3_progress()
        nc = keys.get('n_complete_efficacy')
        ok = (nc == expect_n)
        if ok and isinstance(keys.get('valid_rows'), dict):
            ok = all(v == expect_n for v in keys['valid_rows'].values())
        if ok:
            break
        bad = rank_incomplete(entries, [f'{PROJH}/results/rt/s3/*_r{{rank}}of8.jsonl'])
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt(item, f'18000 档续跑后仍未齐: {json.dumps(keys)[:300]} bad={bad}')
        rep(f"## {item} ladder{tok} ⏸→run {utc()}",
            f"- progress={json.dumps(keys)[:300]}\n- 未齐 rank: {bad}\n- 按 §1.2 阶梯以 {tok} 对未齐 rank 续跑")
        for e in entries:
            if any(b[0] == e['rank'] for b in bad):
                relaunch_rank(item, e, tok)
        if not wait_all_exit(entries, item, stale_hours=10):
            halt(item, f'阶梯续跑({tok}) 10 小时未结束')
        li += 1
    sh_out(f'touch {share_flag}')
    rep(f"## {item} ✓ {utc()}", f"- n_complete_efficacy={expect_n}; 各组合 valid 行={expect_n}; touch {share_flag}")

def s3_finalize():
    CUR['phase'] = 'S7 finalize'; save_cur()
    ts = sh_out("TZ='Asia/Shanghai' date '+%F %T'")[0]
    out, rc = sh_out(f"cd {PROJH} && {ENV_OFF} && PYTHONPATH=src python3 -m study3.end_entry --stopped-at \"{ts}\"", 1800)
    if not os.path.exists(f'{PROJH}/experiments/rt/s3_end_of_generation.json'):
        halt('S3H-§7收尾', f'end_entry 未生成 json rc={rc} out={out[:300]}')
    sh(f'cp -a {PROJH}/results/rt/s3 {POUTH}/results/rt/')
    sh(f'cp {PROJH}/experiments/rt/s3_end_of_generation.json {POUTH}/')
    sh_out(f'touch {SHARE}/S3_END')
    rep(f"## S3H-§7 END ✓ {utc()}",
        f"- end_entry stopped-at {ts}; results/rt/s3 与 s3_end_of_generation.json 已拷 POUTH; touch S3_END\n- 未运行 study3.confirm（按单留给 leader）")

# ---------------- §8 parent queue ----------------

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
    files = sorted(glob.glob(f'{PROJH}/results/rt/s2smoke/*.jsonl'))
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
    nchk = heuristic_english(files, 'S3H-§8 G3冒烟', min_words=3)
    rep(f"## S3H-§8 G3'' smoke ✓ {utc()}",
        f"- 退出码 0; base=4 行, rome_N=4 行\n- 连贯性: 自动启发通过（{nchk} 条；待 leader 复核 results/rt/s2smoke/）")

def g3_formal():
    CUR['phase'] = 'S8 G3 formal'; save_cur()
    cfg = 'experiments/rt/study2_r1llama70b_eff.yaml'
    cfg_txt = open(f'{PROJH}/{cfg}').read()
    dev_flag = '' if 'device_map' in cfg_txt else '--device auto'
    slots = {0: [0, 1], 1: [2, 3], 2: [4, 5], 3: [6, 7]}
    for batch in ([0, 1, 2, 3], [4, 5, 6, 7]):
        entries = []
        for k in batch:
            gs = slots[k % 4]
            gpu_s = ','.join(map(str, gs))
            assert_gpus_free(gs, 'S3H-§8 G3 formal')
            cmd = (f"cd {PROJH} && {ENV_OFF} && export PYTHONPATH=src; unset WHYAAAI_DEVICE_MAP && "
                   f"CUDA_VISIBLE_DEVICES={gpu_s} WHYAAAI_MODEL={M70} nohup python3 -m rt.run --config {cfg} "
                   f"--rank {k} --world 8 --max-batch-tokens 34000 {dev_flag} "
                   f"> logs/rt/g70_r{k}.log 2>&1 & echo NEWPID=$!")
            out, _ = sh_out(cmd)
            pid = None
            for line in out.splitlines():
                if line.startswith('NEWPID='):
                    pid = int(line.split('=', 1)[1])
            if not pid:
                halt('S3H-§8 G3 formal', f'rank {k} 启动失败 {out[:200]}')
            entries.append({"rank": k, "pid": pid, "gpus": gs, "cmd": cmd,
                            "log": f'{PROJH}/logs/rt/g70_r{k}.log',
                            "outglob": f'{PROJH}/results/rt/s2/r1llama70b_s2_{{cond}}_r{k}of8.jsonl', "world": 8})
        update_watchdog("G3p", entries)
        if not wait_all_exit(entries, "G3p", stale_hours=20):
            halt('S3H-§8 G3 formal', f'batch {batch} 20 小时未结束')
        li = 0
        while True:
            bad = []
            for e in entries:
                if not exit_ok(e['log']):
                    bad.append(e['rank']); continue
                rows, tot_only = {}, 0
                for cond in ('base', 'rome_N'):
                    files = glob.glob(f"{PROJH}/results/rt/s2/r1llama70b_*_{cond}_r{e['rank']}of8.jsonl")
                    okc, errc, v = set(), set(), 0
                    for f in files:
                        with open(f, errors='replace') as fh:
                            for line in fh:
                                d = json.loads(line)
                                if d.get('error'):
                                    errc.add(d.get('case_id'))
                                elif d.get('case_id') and d.get('probe'):
                                    okc.add(d.get('case_id')); v += 1
                    rows[cond] = v
                    tot_only += len(errc - okc)
                if rows.get('base', 0) < 100 or rows.get('rome_N', 0) < 100 or tot_only > 0:
                    bad.append(e['rank'])
            if not bad:
                break
            tok = ladder_tokens(RT70_LADDER, li)
            if tok is None:
                halt('S3H-§8 G3 formal', f'18000 档后仍未齐: bad={bad}')
            rep(f"## S3H-§8 G3'' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
            for e in entries:
                if e['rank'] in bad:
                    relaunch_rank("G3p", e, tok)
            if not wait_all_exit(entries, "G3p", stale_hours=20):
                halt('S3H-§8 G3 formal', f'阶梯续跑({tok}) 20 小时未结束')
            li += 1
    rep(f"## S3H-§8 G3'' ✓ {utc()}", "- 8 rank 全部: base/rome_N 各 100 valid 行、未重做 error case=0（§0 按意图）")

def g10_resume():
    CUR['phase'] = 'S8 G10 resume'; save_cur()
    conds = ['rome_B0P', 'rome_B1', 'rome_a0.5', 'rome_a2', 'rome_a3', 'ike', 'rome_samp']
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml "
           f"--rank {{rank}} --world 8 --device cuda --batch-size 16 --max-batch-tokens {{tokens}} "
           f"--conditions {','.join(conds)} --stage 1")
    pids, entries = start_rt_ranks("G10r", 8, tpl, f'{PROJH}/logs/rt/s2_32_sec1_resume_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s2/r1qwen32b_s2_{{cond}}_r{{rank}}of8.jsonl')
    li = 0
    while True:
        if not wait_all_exit(entries, "G10r", stale_hours=8):
            halt("S3H-§8 G10'", '续跑 8 小时未结束')
        bad = rank_incomplete(entries, [f'{PROJH}/results/rt/s2/r1qwen32b_s2_*_r{{rank}}of8.jsonl'])
        if not bad:
            break
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt("S3H-§8 G10'", f'18000 档后仍未齐: {bad}')
        rep(f"## S3H-§8 G10' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
        for e in entries:
            if any(b[0] == e['rank'] for b in bad):
                relaunch_rank("G10r", e, tok)
        li += 1
    rep(f"## S3H-§8 G10' ✓ {utc()}", "- 全部 rank 分片齐（每 case 有 valid 行，§0 按意图）")

def g11_run():
    CUR['phase'] = 'S8 G11'; save_cur()
    tpl = (f"WHYAAAI_MODEL={M32} PYTHONPATH=src python3 -m rt.run --config experiments/rt/study2_r1qwen32b.yaml "
           f"--rank {{rank}} --world 8 --device cuda --batch-size 16 --max-batch-tokens {{tokens}} --stage 2")
    pids, entries = start_rt_ranks("G11r", 8, tpl, f'{PROJH}/logs/rt/s2_32_sec2_r{{rank}}.log',
                                   f'{PROJH}/results/rt/s2/r1qwen32b_s2_{{cond}}_r{{rank}}of8.jsonl')
    li = 0
    while True:
        if not wait_all_exit(entries, "G11r", stale_hours=10):
            halt("S3H-§8 G11", '10 小时未结束')
        bad = rank_incomplete(entries, [f'{PROJH}/results/rt/s2/r1qwen32b_s2_*_r{{rank}}of8.jsonl'])
        if not bad:
            break
        tok = ladder_tokens(RT_LADDER, li)
        if tok is None:
            halt("S3H-§8 G11", f'18000 档后仍未齐: {bad}')
        rep(f"## S3H-§8 G11' ladder{tok} ⏸→run {utc()}", f"- 未齐 rank: {bad}; 以 {tok} 续跑")
        for e in entries:
            if any(b[0] == e['rank'] for b in bad):
                relaunch_rank("G11r", e, tok)
        li += 1
    rep(f"## S3H-§8 G11' ✓ {utc()}", "- 全部 rank 分片齐（每 case 有 valid 行，§0 按意图）")

def parent_end():
    CUR['phase'] = 'S8 parent end'; save_cur()
    out, _ = sh_out(f'cd {PROJH} && sha256sum results/rt/s2/*.jsonl > {POUTH}/parent_end_of_generation.txt && '
                    f'date -u +%FT%TZ >> {POUTH}/parent_end_of_generation.txt && echo OK')
    if 'OK' not in out:
        halt('S3H-§8 收尾', 'sha256sum results/rt/s2 失败')
    sh(f'cp -a {PROJH}/results/rt/s2 {POUTH}/results/rt/')
    sh_out(f'touch {SHARE}/PARENT_END')
    rep(f"## S3H-§8 PARENT_END ✓ {utc()}",
        "- parent_end_of_generation.txt 已写（sha256+时间戳）; results/rt/s2 已拷 POUTH; touch PARENT_END\n- 父研究与 Study 3 全队列完成")

# ---------------- hourly reporter ----------------

def hourly():
    while True:
        time.sleep(3600)
        try:
            alive = 0
            try:
                out, _ = sh_out('pgrep -cf "rt[.](run|pool|deltas)" || true')
                alive = int(out) if out.strip().isdigit() else 0
            except Exception:
                pass
            out, _ = sh_out('nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader | tr "\\n" " "')
            rep(f"## ORCH ⏸ {utc()}",
                f"- 阶段: {CUR.get('phase')} | {CUR.get('detail')} | rt 进程 {alive} | {out[:200]}")
        except Exception:
            pass

# ---------------- main ----------------

def main():
    t = threading.Thread(target=hourly, daemon=True)
    t.start()
    log('orchestrator started (S3-H)')
    rep(f"## S3H-ORCH start ⏸ {utc()}",
        "- 夜间自动执行已启动（nohup setsid 等价 tmux detached）：等待 $SHARE/s3_code_full.bundle → §2…§8；任何校验失败写 ⏸ 停止；补跑阶梯 40k→26k→18k（70B 34k→26k→18k）；看门狗 v3 长驻")
    skip_s3 = False
    try:
        skip_s3 = phase_s2()
    except SystemExit:
        raise
    except Exception as e:
        halt('S3H-§2', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    if not skip_s3:
        try:
            deltas_phase('s3fresh', 'experiments/rt/deltas_s3_r1qwen32b_fresh.yaml', 309, 'S3H-§3')
            sh_out(f'touch {SHARE}/S3_D_FRESH_DONE')
            rep(f"## S3H-§3 ✓ {utc()}", "- cases=309 ok=309 errors 空 editor_nan=0 max_rank=1 max_rel_err<1e-4; summarize 已存 POUTH; touch S3_D_FRESH_DONE")
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§3', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            ext_n = phase_s4()
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§4', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            deltas_phase('s3ext', 'experiments/rt/deltas_s3_r1qwen32b_ext.yaml', ext_n, 'S3H-§5', smoke=False)
            sh_out(f'touch {SHARE}/S3_D_EXT_DONE')
            rep(f"## S3H-§5 ✓ {utc()}", f"- cases={ext_n} ok={ext_n} 其余条件同 §3; touch S3_D_EXT_DONE")
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§5', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
        try:
            phase_s6()
            gen_phase('fresh', 309, 'S3H-§7 fresh', f'{SHARE}/S3_G_FRESH_DONE')
            gen_phase('ext', ext_n, 'S3H-§7 ext', f'{SHARE}/S3_G_EXT_DONE')
            s3_finalize()
        except SystemExit:
            raise
        except Exception as e:
            halt('S3H-§6/7', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    else:
        rep(f"## S3H skip-note ⏸ {utc()}", "- EasyEdit 不可用：按 §2.9 跳过 §3–§7（Study 3 编辑与生成本节点不做）")
    try:
        g3_smoke()
        g3_formal()
        g10_resume()
        g11_run()
        parent_end()
    except SystemExit:
        raise
    except Exception as e:
        halt('S3H-§8', f'异常 {type(e).__name__}: {e}', traceback.format_exc())
    rep(f"## S3H-ALL ✓ {utc()}", "- S3-H 全部项完成")
    CUR['phase'] = 'DONE'
    save_cur()
    log('orchestrator DONE')

if __name__ == '__main__':
    main()
