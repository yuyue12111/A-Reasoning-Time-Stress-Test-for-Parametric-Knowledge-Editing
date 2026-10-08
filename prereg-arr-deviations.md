# Deviations from the frozen pre-registration (Study 2)

Frozen text: `prereg-arr.md` at commit `a9b4139` (registry entry 1, GitHub push 2026-10-08T03:39:43Z).
Each entry: when, what, why, and whether any Study-2 outcome had been seen.

| # | date (UTC+8) | deviation | reason | outcomes seen? |
|---|---|---|---|---|
| D1 | 2026-10-08 15:00 | R1-Distill-Qwen-32B generation on the H100 node runs one process per GPU (8 processes, `--world 8 --device cuda`) instead of two 4-GPU processes. The partial 4-GPU rows of `base` and `rome_N` (about 50 of 400 cases) are moved to `results/rt/s2_archive_world2/` and never analysed; all 32B conditions are generated in the new layout. The stage-2 given-chain source in `study2_r1qwen32b.yaml` changes from `r*of2` to `r*of8` accordingly (stage-1 condition specs unchanged). | 4-GPU pipeline processes stalled or ran too slowly (generation is CPU-bound; four stalls in ~3 h). | No: only row counts were inspected. |
| D2 | 2026-10-08 15:00 | Llama-70B ROME edits run on the 8×4090 node (one fp32 process over 8 cards, as in the capacity smoke) instead of the H100 node. | Keeps the H100 node for generation, the bottleneck. Edits are fp32 with TF32 off on both nodes. | No. |
| D3 | 2026-10-08 15:00 | Llama-70B, 14B, 8B, 7B and 1.5B: base and N are generated for the efficacy probe only (`study2_<model>_eff.yaml`); paraphrase and neighbourhood probes are not run for these models. 14B, 8B, 7B and 1.5B are generated on the 4090 node (each model entirely on one node). | Platform time (one day). H1, H2 and H2b use the efficacy probe only; locality is reported for 32B. | No. |
| D4 | 2026-10-08 15:00 | MEMIT (32B) runs only if the H100 node mounts the Wikipedia dump and time remains after the 32B and 70B items; AlphaEdit is not run. | Platform time; the statistics need ~1 h on H100, ~4 h on 4090. | No. |
| D5 | 2026-10-08 15:35 | 14B, 8B, 7B and 1.5B generation (efficacy only, D3) runs on whichever node is free first; each model is claimed with an atomic lock (`mkdir xfer/LOCK_GS_<tag>`) and generated entirely on that node. | The 70B edits keep the 4090 busy for ~4.5 h while the H100 node idles between its 32B items and the 70B generation. | No. |
