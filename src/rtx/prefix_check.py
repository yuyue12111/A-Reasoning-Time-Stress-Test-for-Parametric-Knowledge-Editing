"""Append-only check for registered shards (ruling (b), deviation D14).

    python3 src/rtx/prefix_check.py record <registry_hash_list> <shard>... > sizes.tsv
    python3 src/rtx/prefix_check.py verify <registry_hash_list> sizes.tsv

record: each shard's whole-file sha256 must equal its line in the registered list (``sha256  path``);
prints ``path<TAB>size<TAB>sha256``.  verify: the first ``size`` bytes of each file must still hash
to the registered sha256 (rows may only have been appended).  Exit code 1 on any mismatch.
"""
import hashlib
import os
import sys


def registered(path_list):
    out = {}
    for line in open(path_list):
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and len(parts[0]) == 64:
            out[os.path.realpath(parts[1])] = parts[0]
    return out


def sha_prefix(path, n=None):
    h = hashlib.sha256()
    left = n
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(1 << 20 if left is None else min(1 << 20, left))
            if not chunk:
                break
            h.update(chunk)
            if left is not None:
                left -= len(chunk)
                if left == 0:
                    break
    return h.hexdigest()


def main():
    mode, reg = sys.argv[1], registered(sys.argv[2])
    bad = 0
    if mode == "record":
        for p in sys.argv[3:]:
            rp = os.path.realpath(p)
            want, got = reg.get(rp), sha_prefix(rp)
            if want != got:
                bad += 1
                print(f"# MISMATCH {rp} registered {want} now {got}", file=sys.stderr)
            print(f"{rp}\t{os.path.getsize(rp)}\t{got}")
    elif mode == "verify":
        for line in open(sys.argv[3]):
            rp, size, sha = line.rstrip("\n").split("\t")
            got = sha_prefix(rp, int(size))
            ok = got == sha == reg.get(rp)
            bad += not ok
            print(f"{'OK  ' if ok else 'FAIL'} {rp} prefix {size} bytes, now {os.path.getsize(rp)} bytes")
    else:
        raise SystemExit("mode must be record or verify")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
