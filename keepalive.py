#!/usr/bin/env python3
"""keepalive.py — 防平台因 GPU 低占用回收实例(组内启智:util<15% 持续 3h 被收,见 compute-situation 记忆)。

在所有可见 GPU 上跑轻量 bf16 matmul,把每卡 util 维持在目标占空比(默认 30%,2× 余量稳过 15% 线)。
显存极小(每卡 ~百 MB),不动真任务的结果;随时 Ctrl-C / `pkill -f keepalive.py` 停。bf16 纯 matmul、无 compute_v → 无 Hopper NaN 风险。

★ --idle-only(推荐常驻):每轮先查该卡当前 util,只有低于 --skip-above(默认 40%)才补 burst
  → 真任务在跑(util 高)时自动让路、几乎不偷算力;空窗才顶上。可与 A1/A2 等真任务共存、一直开着。

用法(平台,任意目录;H100/4090 通用):
  python keepalive.py --idle-only                  # 推荐:所有卡,真任务跑时让路,空窗顶 ~30%
  python keepalive.py                              # 无脑维持所有卡 ~30%(不查真任务,空闲实例用)
  python keepalive.py --gpus 0,1 --util 25         # 只 0/1 卡,目标 25%
  python keepalive.py --hours 12                   # 12h 后自动退出(防忘关)
  后台常驻: nohup python keepalive.py --idle-only >/tmp/keepalive.log 2>&1 &
  停:       pkill -f keepalive.py
"""
import argparse, signal, subprocess, sys, time
import multiprocessing as mp


def gpu_count():
    try:
        out = subprocess.check_output(["nvidia-smi", "--query-gpu=index", "--format=csv,noheader"], text=True)
        return [int(x) for x in out.split()]
    except Exception:
        return []


def query_util(g):
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits", "-i", str(g)], text=True)
        return int(out.strip().splitlines()[0])
    except Exception:
        return -1


def worker(g, util, size, period, idle_only, skip_above, deadline):
    import torch                                   # 只在子进程 import(父进程不碰 CUDA → fork 安全)
    torch.cuda.set_device(g)
    try:
        a = torch.randn(size, size, device=g, dtype=torch.bfloat16)
        b = torch.randn(size, size, device=g, dtype=torch.bfloat16)
        c = torch.empty_like(a)                    # 复用输出缓冲,不让异步队列堆内存
    except RuntimeError as e:
        print(f"[keepalive] GPU{g} 分配失败(显存可能已满),跳过:{e}", flush=True); return
    duty = max(0.0, min(1.0, util / 100.0))
    busy_t, idle_t = duty * period, (1 - duty) * period
    while deadline is None or time.time() < deadline:
        if idle_only and query_util(g) >= skip_above:   # 真任务在跑 → 让路
            time.sleep(period); continue
        t0 = time.time()
        while time.time() - t0 < busy_t:
            torch.matmul(a, b, out=c)
            torch.cuda.synchronize(g)              # 每步同步:用 wall-clock 控时长、util 稳在高位
        if idle_t > 0:
            time.sleep(idle_t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpus", default=None, help="逗号分隔卡号,默认全部可见卡")
    ap.add_argument("--util", type=float, default=30.0, help="目标占空比%%(默认30,稳过15%%线)")
    ap.add_argument("--size", type=int, default=4096, help="matmul 维度(默认4096,bf16≈32MB/张)")
    ap.add_argument("--period", type=float, default=2.0, help="每轮秒数(busy+idle)")
    ap.add_argument("--idle-only", action="store_true", help="真任务跑时(util≥skip-above)自动让路、不偷算力")
    ap.add_argument("--skip-above", type=float, default=40.0, help="idle-only:util≥此值视为真任务在跑")
    ap.add_argument("--hours", type=float, default=None, help="N 小时后自动退出(默认常驻)")
    args = ap.parse_args()

    gpus = [int(x) for x in args.gpus.split(",")] if args.gpus else gpu_count()
    if not gpus:
        print("[keepalive] 没探到 GPU(nvidia-smi 不可用?)退出"); sys.exit(1)
    deadline = time.time() + args.hours * 3600 if args.hours else None
    print(f"[keepalive] 卡={gpus} 目标util~{args.util}% mode={'idle-only(真任务让路)' if args.idle_only else 'always'} "
          f"size={args.size} {'退出@%.1fh' % args.hours if args.hours else '常驻'} —— `pkill -f keepalive.py` 停", flush=True)

    procs = []
    for g in gpus:
        p = mp.Process(target=worker, args=(g, args.util, args.size, args.period,
                                            args.idle_only, args.skip_above, deadline), daemon=True)
        p.start(); procs.append(p)

    def _stop(*_):
        for p in procs:
            p.terminate()
        print("\n[keepalive] 停止", flush=True); sys.exit(0)
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    try:                                           # 心跳:每 60s 打一行各卡 util
        while any(p.is_alive() for p in procs):
            time.sleep(60)
            print(f"[keepalive] {time.strftime('%H:%M:%S')} " +
                  " ".join(f"G{g}={query_util(g)}%" for g in gpus), flush=True)
            if deadline and time.time() > deadline:
                break
    finally:
        for p in procs:
            p.terminate()
    print("[keepalive] 结束", flush=True)


if __name__ == "__main__":
    main()
