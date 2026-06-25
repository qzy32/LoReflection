import re
from pathlib import Path


SCAN_ROOTS = [
    Path("docs"),
    Path("reports"),
    Path("tools"),
    Path("scripts"),
    Path("configs"),
    Path("tests"),
    Path("runtime"),
    Path("loreflection"),
    Path("data_pipeline"),
    Path("outputs/current_vlm_planner_handoff"),
    Path("artifacts/current_interface"),
]
EXTRA_FILES = [Path("README.md"), Path("README_SERVER.md"), Path("PROGRESS.md")]


def _patterns():
    return {
        "old_exec_a": re.compile("semantic" + "_inpaint"),
        "old_exec_b": re.compile(r"\b" + "hy" + "brid" + r"\b"),
        "old_exec_c": re.compile("apm" + "_attribute_update"),
        "old_repair_count_a": re.compile("semantic[-_]repair" + "5"),
        "old_repair_count_b": re.compile("semantic[-_]repair" + "6"),
        "old_repair_count_c": re.compile(r"\brepair" + "6" + r"\b"),
        "old_adapter_phrase": re.compile(
            "EditRoom " + "toy adapter"
            + "|toy-level " + "EditRoom"
            + "|EditRoom-like " + "toy"
        ),
        "old_alias_a": re.compile(r'"action_type"\s*:\s*"' + "IN" + r'SERT"'),
        "old_alias_b": re.compile(r'"action_type"\s*:\s*"' + "DE" + r'LETE"'),
        "old_alias_c": re.compile(r'"action_type"\s*:\s*"' + "MO" + r'VE"'),
        "old_alias_d": re.compile(r'"action_type"\s*:\s*"' + "RE" + r'SIZE"'),
        "old_alias_e": re.compile(r'"action_type"\s*:\s*"' + "UPDATE" + r'_YAW"'),
        "old_alias_f": re.compile(r'"action_type"\s*:\s*"' + "UPDATE" + r'_SIZE"'),
    }


def _files():
    out = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        out.extend(
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix.lower() not in {".zip", ".png", ".jpg", ".jpeg", ".safetensors", ".pyc"}
            and "__pycache__" not in path.parts
        )
    out.extend(path for path in EXTRA_FILES if path.exists())
    return out


def test_no_deprecated_terms_in_current_repo_scope():
    hits = []
    patterns = _patterns()
    for path in _files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in patterns.items():
            if pattern.search(text):
                hits.append((str(path), label))
    assert hits == []
