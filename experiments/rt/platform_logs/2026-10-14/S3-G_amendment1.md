# S3-G amendment 1 (2026-10-14, leader)

Cause: the executor stopped at §1.9. `import easyeditor` fails with `ModuleNotFoundError: No module named 'higher'`.

Ruling: the check was wrong, not the environment.
- `higher` is not in the 10-08 freeze of this node either (`xfer/freeze_4090.txt`, 312 packages), and every Study 2 edit
  (D1–D6) ran on this node without it.
- `rt.deltas` never does a bare `import easyeditor`. It first calls `ensure_easyedit_importable()`
  (`src/vendor_patches/easyedit_lean_import.py`), which stands in for optional extras such as `higher` that ROME never
  calls; a stand-in raises if anything does call it.
- The same correction was already ruled for S3-H (round-1 audit, `S3-H_v2_amendments.md`), and S3-G regressed it.
- Verified locally in an environment without `higher`: the check below prints `EASYEDIT_OK [...]`.

Changes:
1. §1.9 now reads: this must print a line starting with `EASYEDIT_OK`; otherwise ⏸.
   `PYTHONPATH=src:source/EasyEdit python3 -c "from rt.deltas import ensure_easyedit_importable as f; s=f(); import easyeditor; from easyeditor.models.rome import rome_main; print('EASYEDIT_OK', s)"`
2. §1.5: the pip remedy line is removed; `$SHARE/wheels` holds only zstandard. All five versions matched, so no package
   is installed. If any of the five ever differs: ⏸.
3. Nothing else changes. Resume at §1.9, then §1.12 (touch `S3G_CODE_OK`) and continue with §2.
