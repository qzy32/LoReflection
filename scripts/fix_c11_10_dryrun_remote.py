#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a800_reverse_proxy_clone_sources as h  # noqa: E402

REMOTE = r'''
from pathlib import Path
import csv, json, shutil, subprocess, sys

ROOT = Path("/wuqingyaoa800/qiuziyan/LoReflection")
OUT = ROOT / "outputs/editroom_semantic_pair_conversion_v1"
REPORTS = ROOT / "outputs/c11_10_reports"
MANUAL = ROOT / "outputs/manual_review/c11_10_editroom_semantic_conversion"
metadata = OUT / "diffsynth_metadata.csv"

code = """
import csv, json, sys
sys.path.insert(0, '/wuqingyaoa800/qiuziyan/DiffSynth-Studio')
from diffsynth.core.data.unified_dataset import UnifiedDataset
base = '/wuqingyaoa800/qiuziyan/LoReflection/outputs/editroom_semantic_pair_conversion_v1'
md = base + '/diffsynth_metadata.csv'
keys = ('image', 'blockwise_controlnet_image', 'blockwise_controlnet_inpaint_mask')
op = UnifiedDataset.default_image_operator(base_path=base, height=512, width=512, max_pixels=1048576, interpolation='nearest')
ds = UnifiedDataset(base_path=base, metadata_path=md, repeat=1, data_file_keys=keys, main_data_operator=op, max_data_items=1)
item = ds[0]
out = {'rows': len(list(csv.DictReader(open(md, encoding='utf-8')))), 'keys': list(item.keys()), 'prompt': item.get('prompt', '')}
for k, v in item.items():
    if hasattr(v, 'size'):
        out[k + '_size'] = list(v.size)
        out[k + '_mode'] = getattr(v, 'mode', None)
        if k.endswith('mask'):
            import numpy as np
            out[k + '_unique_sample'] = sorted(np.unique(np.asarray(v)).tolist())[:20]
print(json.dumps(out))
"""

proc = subprocess.run([sys.executable, "-c", code], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
rows = list(csv.DictReader(open(metadata, encoding="utf-8")))
dry = {
    "returncode": proc.returncode,
    "stdout": proc.stdout.strip(),
    "stderr": proc.stderr.strip()[-2000:],
    "metadata_rows": len(rows),
    "actions_included": sorted({r["image"].split("_")[0].upper() for r in rows}),
    "parametric_only_actions": ["SCALE"],
}
(REPORTS / "c11_10_diffsynth_loader_dryrun_from_real_editroom_pairs.json").write_text(json.dumps(dry, indent=2, ensure_ascii=False), encoding="utf-8")
final_path = REPORTS / "c11_10_final_decision.json"
final = json.loads(final_path.read_text(encoding="utf-8"))
final["diffsynth_loader_returncode"] = proc.returncode
valid = final.get("valid_by_action", {})
if all(valid.get(a, 0) >= 1 for a in ["ADD", "REMOVE", "TRANSLATE", "REPLACE"]) and proc.returncode == 0:
    final["decision"] = "CONVERSION_PASS_TO_C12"
    final["blocking_reason"] = None
else:
    final["decision"] = "CONVERSION_PARTIAL_BLOCKED"
    final["blocking_reason"] = "Core action coverage or loader dry-run incomplete."
final["scale_status"] = "parametric_only_missing_real_pair"
final_path.write_text(json.dumps(final, indent=2, ensure_ascii=False), encoding="utf-8")
for p in [final_path, REPORTS / "c11_10_diffsynth_loader_dryrun_from_real_editroom_pairs.json"]:
    shutil.copy2(p, MANUAL / p.name)
zip_path = ROOT / "outputs/manual_review/c11_10_editroom_semantic_conversion.zip"
if zip_path.exists():
    zip_path.unlink()
shutil.make_archive(str(zip_path.with_suffix("")), "zip", MANUAL)
print(json.dumps({"dry": dry, "final": final}, ensure_ascii=False))
'''


def main() -> int:
    outer, inner = h.connect_a800()
    try:
        sftp = inner.open_sftp()
        remote_path = "/wuqingyaoa800/qiuziyan/LoReflection/.tmp_c11_10_fix_dryrun.py"
        with sftp.file(remote_path, "w") as f:
            f.write(REMOTE)
        sftp.close()
        rc, out, err = h.remote_run(inner, f"/wuqingyaoa800/qiuziyan/envs/diffsynth-qwen/bin/python {remote_path}", timeout=180)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if rc != 0:
            return rc
        sftp = inner.open_sftp()
        for remote, local in [
            ("outputs/c11_10_reports/c11_10_diffsynth_loader_dryrun_from_real_editroom_pairs.json", "reports/c11_10_diffsynth_loader_dryrun_from_real_editroom_pairs.json"),
            ("outputs/c11_10_reports/c11_10_final_decision.json", "reports/c11_10_final_decision.json"),
            ("outputs/manual_review/c11_10_editroom_semantic_conversion.zip", "outputs/manual_review/c11_10_editroom_semantic_conversion.zip"),
        ]:
            sftp.get(f"/wuqingyaoa800/qiuziyan/LoReflection/{remote}", local)
        sftp.close()
        return 0
    finally:
        inner.close()
        outer.close()


if __name__ == "__main__":
    raise SystemExit(main())
