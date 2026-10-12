"""Unit tests for study3.confirm (synthetic tables; no model, no GPU)."""
import json
import os
import tempfile
import unittest

from study3 import confirm as C


def o(new, old):
    return {"new": new, "old": old, "es": int(new and not old), "clr": 0, "words": 1}


class TestFamiliarity(unittest.TestCase):
    def test_excludes_evaluated_model_and_counts_missing_as_unknown(self):
        flags = {"r1qwen1_5b": {"a": True, "b": False}, "r1qwen7b": {"a": True, "b": True},
                 "r1qwen14b": {"a": True}, "r1llama8b": {"a": False, "b": True}}
        fam = C.familiarity(["a", "b"], "r1qwen32b", flags)
        self.assertEqual(fam["a"], (3, 4, True))
        self.assertEqual(fam["b"], (2, 4, False))          # r1qwen14b flag missing -> not known
        fam14 = C.familiarity(["a"], "r1qwen14b", flags)
        self.assertEqual(fam14["a"], (2, 3, False))         # 2/3 < .75


class TestRetention(unittest.TestCase):
    def setUp(self):
        self.E = {"x": {"B0": o(True, False), "B3": o(False, True)},     # edit lost, old only
                  "y": {"B0": o(True, False), "B3": o(True, True)},      # both values: lost (lexical), kept (strict)
                  "z": {"B0": o(False, True), "B3": o(True, False)}}     # edit failed at B0: not in retention set
        self.B = {"x": {"B0": o(False, True), "B3": o(False, True)},
                  "y": {"B0": o(False, True), "B3": o(False, False)},    # own answer lost
                  "z": {"B0": o(False, True), "B3": o(False, True)}}

    def test_retention_set_gates_on_base_old_and_edit_success(self):
        self.assertEqual(C.retention_set(self.E, self.B), ["x", "y"])

    def test_lexical_and_strict_values(self):
        lex, _ = C.retention_values(self.E, self.B, ["x", "y"])
        strict, _ = C.retention_values(self.E, self.B, ["x", "y"], strict=True)
        self.assertEqual(lex, [1, 0])        # x: 1-0 ; y: 1-1
        self.assertEqual(strict, [1, -1])    # y: new present -> kept (0) minus own lost (1)

    def test_paraphrase_after_rows(self):
        Ep = {"x": {"B0": o(False, False)}}
        Bp = {"x": {"B0": o(False, True)}}
        v, used = C.retention_values(self.E, self.B, ["x", "y"], Ea=Ep, Ba=Bp, after="B0")
        self.assertEqual((v, used), ([1], ["x"]))


class TestVerdictAndWording(unittest.TestCase):
    def test_primary(self):
        self.assertTrue(C.primary_verdict({"point": .2, "p": .05}))
        self.assertFalse(C.primary_verdict({"point": .2, "p": .0501}))
        self.assertFalse(C.primary_verdict({"point": -.2, "p": .001}))
        self.assertFalse(C.primary_verdict({"point": None, "p": None}))

    def test_wording_table(self):
        self.assertEqual(C.wording("incomplete", False, None)["abstract"], "not_run")
        self.assertEqual(C.wording("complete", False, None)["title"], "title3")
        self.assertEqual(C.wording("complete", True, {"ci95": [.01, .2]})["title"], "title1")
        self.assertEqual(C.wording("complete", True, {"ci95": [-.01, .2]})["title"], "title2")


class TestEndGate(unittest.TestCase):
    def test_refuses_without_entry_and_on_changed_shard(self):
        with tempfile.TemporaryDirectory(dir=C.REPO) as d:
            shard = os.path.join(d, "s.jsonl")
            with open(shard, "w") as fh:
                fh.write("{}\n")
            with self.assertRaises(SystemExit):
                C.check_end_entry(os.path.join(d, "missing.json"), [shard])
            entry = os.path.join(d, "end.json")
            rel = os.path.relpath(shard, C.REPO)
            with open(entry, "w") as fh:
                json.dump({"shards": {rel: C.sha256(shard)}}, fh)
            self.assertIn("shards", C.check_end_entry(entry, [shard]))
            with open(shard, "a") as fh:
                fh.write("{}\n")
            with self.assertRaises(SystemExit):
                C.check_end_entry(entry, [shard])


class TestAnalyseIncomplete(unittest.TestCase):
    def test_incomplete_world_is_not_tested(self):
        E = {"a": {"B0": o(True, False), "B3": o(False, True)}}
        B = {"a": {"B0": o(False, True), "B3": o(False, True)}}
        tabs = {("rome_N", "efficacy"): E, ("base", "efficacy"): B, ("rome_N", "para0"): {}, ("base", "para0"): {}}
        fam = {c: (4, 4, True) for c in ("a", "b")}
        out = C.analyse(tabs, ["a", "b"], fam)
        self.assertEqual(out["completeness"]["status"], "incomplete")
        self.assertFalse(out["H5"]["tested"])
        self.assertFalse(out["H5"]["pass"])
        self.assertEqual(out["wording"]["abstract"], "not_run")


class TestSlope(unittest.TestCase):
    def test_exact_line(self):
        b = C.bootstrap_slope([0, 1, 2, 3, 4] * 4, [0, .1, .2, .3, .4] * 4, n_boot=200)
        self.assertAlmostEqual(b["point"], .1)


if __name__ == "__main__":
    unittest.main()
