"""A2 加载诊断(快,不加载模型):查 env / config / hparams override 到底有没有生效。
跑(项目根,带与 run_a2_h100.sh 同样的 export):
  export WHYAAAI_MODEL=$W/models/DeepSeek-R1-Distill-Qwen-32B
  export WHYAAAI_DTYPE=float32 ; export WHYAAAI_DEVICE_MAP=balanced_low_0
  PYTHONPATH=src:source/EasyEdit python diag_a2.py
"""
import os, sys, yaml
sys.path.insert(0, "src"); sys.path.insert(0, "source/EasyEdit")

print("== ENV(进程里到底有没有这些)==")
for k in ("WHYAAAI_MODEL", "WHYAAAI_DTYPE", "WHYAAAI_DEVICE_MAP", "CUDA_VISIBLE_DEVICES"):
    print(f"  {k} = {os.environ.get(k, '<未设>')}")

print("== CONFIG(平台上这份 yaml 有没有 model_parallel)==")
cfg = yaml.safe_load(open("experiments/probe32b_a2_th_p2.yaml"))
ov = cfg.get("hparams_overrides", {})
print(f"  hparams_overrides.model_parallel = {ov.get('model_parallel', '<缺失!>')}")

print("== 加载补丁 dtype 会设成 ==")
print(f"  patch dtype = {os.environ.get('WHYAAAI_DTYPE', 'bfloat16')}  (须 float32;否则 Hopper 上 compute_v NaN)")

print("== HPARAMS override 链 ==")
try:
    from easyeditor import ROMEHyperParams
    hp = ROMEHyperParams.from_hparams("source/EasyEdit/hparams/ROME/qwen2.5-7b.yaml")
    print(f"  yaml 默认 model_parallel = {getattr(hp, 'model_parallel', '<无此属性>')}")
    for k, v in ov.items():
        setattr(hp, k, v)
    mp = getattr(hp, "model_parallel", None)
    print(f"  override 后 hp.model_parallel = {mp}")
    print(f"  => editor.py 会用 device_map = {'auto(再被 WHYAAAI_DEVICE_MAP 覆盖)' if mp else 'None=单卡!'}")
except Exception as e:
    print(f"  [加载 easyeditor 失败] {e!r}")

print("\n判读:① 三个 ENV 必须都有值;② config model_parallel=True;③ override 后 hp.model_parallel=True。"
      "\n任一不满足 = 找到病因。全满足却仍单卡 = device_map/accelerate 层问题,告诉我。")
