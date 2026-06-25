#!/usr/bin/env python3
"""Temporarily expose a local loopback proxy to A800 and clone official sources.

This script intentionally does not download third-party source to the local
machine. It opens a Paramiko two-hop SSH connection, requests a loopback-only
remote port forward on A800, relays that port to the local loopback proxy, and
then runs git/curl commands on A800 with per-command proxy configuration.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import queue
import re
import select
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import paramiko


ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "pazhou_ssh_guide.md"
REMOTE_REPO = Path("/wuqingyaoa800/qiuziyan/LoReflection")
SOURCE_ROOT = Path("/wuqingyaoa800/qiuziyan/third_party_sources")
MIRROR_ROOT = SOURCE_ROOT / "git_mirrors"
CHECKOUT_ROOT = SOURCE_ROOT / "checkouts"

SEMLAYOUTDIFF_URL = "https://github.com/3dlg-hcvc/SemLayoutDiff.git"
BLENDERPROC_COMPANION_URL = "https://github.com/3dlg-hcvc/BlenderProc-3DFront.git"
BLENDERPROC_UPSTREAM_URL = "https://github.com/yinyunie/BlenderProc-3DFront.git"


def mask_proxy(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "loopback": parsed.hostname in {"127.0.0.1", "localhost"},
        "port": parsed.port,
    }


def run_local(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def detect_local_proxy(explicit: str | None) -> tuple[str, dict[str, Any]]:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    else:
        for port in [7890, 7891, 7897, 1080, 10808, 10809]:
            candidates.append(f"http://127.0.0.1:{port}")
            candidates.append(f"socks5h://127.0.0.1:{port}")

    attempts = []
    for url in candidates:
        info = mask_proxy(url)
        if not info["loopback"]:
            raise SystemExit(f"Proxy must be loopback-only, got host={info['host']!r}")
        rc, out, err = run_local(
            [
                "curl.exe",
                "--silent",
                "--show-error",
                "--max-time",
                "12",
                "--proxy",
                url,
                "--head",
                "https://github.com/3dlg-hcvc/SemLayoutDiff",
            ],
            timeout=20,
        )
        status_lines = [line for line in out.splitlines() if line.startswith("HTTP/")]
        status = status_lines[-1] if status_lines else ""
        ok = rc == 0 and re.search(r"HTTP/\S+\s+[23]\d\d", status)
        attempts.append({**info, "ok": bool(ok), "status": status, "error": err.strip()[:300]})
        if ok:
            return url, {"selected": info, "attempts": attempts, "github_reachable_locally": True}
    return "", {"selected": None, "attempts": attempts, "github_reachable_locally": False}


def read_credentials() -> tuple[str, str, str]:
    text = GUIDE.read_text(encoding="utf-8", errors="ignore")
    user = "qiuziyan" if "qiuziyan" in text else os.environ.get("PAZHOU_USER", "")
    jump_password = os.environ.get("PAZHOU_JUMP_PASSWORD", "")
    server_password = os.environ.get("PAZHOU_SERVER_PASSWORD", "")

    def backtick_value(line: str) -> str:
        parts = line.split("`")
        return parts[1].strip() if len(parts) >= 3 else ""

    for line in text.splitlines():
        low = line.lower()
        if not jump_password and ("209" in line or "跳板" in line) and ("密码" in line or "password" in low):
            jump_password = backtick_value(line)
        if not server_password and ("琶洲服务器" in line or "a800" in low) and ("密码" in line or "password" in low):
            server_password = backtick_value(line)
    if not (user and jump_password and server_password):
        raise SystemExit("Could not discover two-hop SSH credentials from guide/env.")
    return user, jump_password, server_password


class Forwarder:
    def __init__(self, transport: paramiko.Transport, remote_port: int, local_host: str, local_port: int):
        self.transport = transport
        self.remote_port = remote_port
        self.local_host = local_host
        self.local_port = local_port
        self.stop_event = threading.Event()
        self.threads: list[threading.Thread] = []
        self.accept_thread: threading.Thread | None = None
        self.connection_count = 0
        self.errors: list[str] = []

    def start(self) -> None:
        self.transport.request_port_forward("127.0.0.1", self.remote_port)
        self.accept_thread = threading.Thread(target=self._accept_loop, name="a800-rpf-accept", daemon=True)
        self.accept_thread.start()

    def _accept_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                chan = self.transport.accept(1.0)
            except Exception as exc:  # pragma: no cover - defensive cleanup
                if not self.stop_event.is_set():
                    self.errors.append(f"accept: {type(exc).__name__}: {exc}")
                continue
            if chan is None:
                continue
            self.connection_count += 1
            thread = threading.Thread(target=self._relay, args=(chan,), name=f"a800-rpf-relay-{self.connection_count}", daemon=True)
            self.threads.append(thread)
            thread.start()

    def _relay(self, chan: paramiko.Channel) -> None:
        sock: socket.socket | None = None
        try:
            sock = socket.create_connection((self.local_host, self.local_port), timeout=15)
            sock.settimeout(None)
            sock.setblocking(False)
            chan.setblocking(False)
            sockets: list[Any] = [sock, chan]
            while sockets and not self.stop_event.is_set():
                readable, _, _ = select.select(sockets, [], [], 1.0)
                for src in readable:
                    try:
                        data = src.recv(65536)
                    except (BlockingIOError, TimeoutError, socket.timeout):
                        continue
                    except Exception:
                        data = b""
                    if not data:
                        sockets = []
                        break
                    dst = chan if src is sock else sock
                    dst.sendall(data)
        except Exception as exc:
            if not self.stop_event.is_set():
                self.errors.append(f"relay: {type(exc).__name__}: {exc}")
        finally:
            try:
                chan.close()
            except Exception:
                pass
            if sock is not None:
                try:
                    sock.close()
                except Exception:
                    pass

    def close(self) -> None:
        self.stop_event.set()
        try:
            self.transport.cancel_port_forward("127.0.0.1", self.remote_port)
        except Exception as exc:
            self.errors.append(f"cancel: {type(exc).__name__}: {exc}")
        if self.accept_thread is not None:
            self.accept_thread.join(timeout=5)
        for thread in self.threads:
            thread.join(timeout=2)


def connect_a800() -> tuple[paramiko.SSHClient, paramiko.SSHClient]:
    user, jump_password, server_password = read_credentials()
    outer = paramiko.SSHClient()
    outer.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    outer.connect(
        "222.201.187.180",
        port=22,
        username=user,
        password=jump_password,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    assert outer.get_transport() is not None
    outer.get_transport().set_keepalive(25)
    chan = outer.get_transport().open_channel("direct-tcpip", ("127.0.0.1", 24800), ("127.0.0.1", 0))
    inner = paramiko.SSHClient()
    inner.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    inner.connect(
        "127.0.0.1",
        port=24800,
        username=user,
        password=server_password,
        sock=chan,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    assert inner.get_transport() is not None
    inner.get_transport().set_keepalive(25)
    return outer, inner


def remote_run(client: paramiko.SSHClient, cmd: str, timeout: int = 600) -> tuple[int, str, str]:
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    rc = stdout.channel.recv_exit_status()
    return rc, out, err


def choose_remote_port(client: paramiko.SSHClient, preferred: int) -> int:
    rc, out, _ = remote_run(client, "ss -ltn 2>/dev/null || true", timeout=30)
    used = set(int(m.group(1)) for m in re.finditer(r"127\.0\.0\.1:(17(?:89[0-9]|9[0-9]{2})|1789[0-9]|179[0-2][0-9])", out))
    for port in [preferred, *range(17892, 17921)]:
        if port not in used:
            return port
    raise RuntimeError("No free loopback remote proxy port found in 17890/17892-17920.")


REMOTE_SCRIPT = r'''
set -euo pipefail
cd /wuqingyaoa800/qiuziyan/LoReflection
REMOTE_PROXY_URL='__REMOTE_PROXY_URL__'
SOURCE_ROOT=/wuqingyaoa800/qiuziyan/third_party_sources
MIRROR_ROOT="$SOURCE_ROOT/git_mirrors"
CHECKOUT_ROOT="$SOURCE_ROOT/checkouts"
mkdir -p "$MIRROR_ROOT" "$CHECKOUT_ROOT" reports docs

python3 - <<'PY'
import json, os, subprocess, textwrap
from pathlib import Path

REMOTE_PROXY_URL = os.environ.get("REMOTE_PROXY_URL_PLACEHOLDER", "")
PY

export GIT_TERMINAL_PROMPT=0
export GIT_LFS_SKIP_SMUDGE=1

run_json() {
  local name="$1"; shift
  python3 - "$name" "$@" <<'PY'
import json, subprocess, sys
name = sys.argv[1]
cmd = sys.argv[2:]
p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print(json.dumps({"name": name, "cmd": cmd, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}, ensure_ascii=False))
PY
}

python3 - <<'PY'
import csv, json, os, subprocess, sys
from pathlib import Path

proxy = "__REMOTE_PROXY_URL__"
root = Path("/wuqingyaoa800/qiuziyan/LoReflection")
reports = root / "reports"
docs = root / "docs"
source_root = Path("/wuqingyaoa800/qiuziyan/third_party_sources")
mirror_root = source_root / "git_mirrors"
checkout_root = source_root / "checkouts"
reports.mkdir(exist_ok=True)
docs.mkdir(exist_ok=True)
mirror_root.mkdir(parents=True, exist_ok=True)
checkout_root.mkdir(parents=True, exist_ok=True)

def run(cmd, cwd=None, timeout=1200):
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    return {"cmd": cmd, "returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}

def git_base():
    return ["git", "-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}", "-c", "http.version=HTTP/1.1"]

def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_mirror(url, path):
    path = Path(path)
    rec = {"url": url, "mirror_path": str(path), "existed": path.exists(), "action": None, "result": None}
    if path.exists():
        valid = run(["git", f"--git-dir={path}", "rev-parse", "--git-dir"])
        rec["existing_valid_git_dir"] = valid
        if valid["returncode"] != 0:
            backup = path.with_name(path.name + ".failed_" + __import__("time").strftime("%Y%m%d_%H%M%S"))
            mv = run(["mv", str(path), str(backup)])
            rec["invalid_mirror_backup"] = {"backup_path": str(backup), "move": mv}
            if mv["returncode"] != 0:
                rec["action"] = "skipped_invalid_mirror_backup_failed"
                rec["result"] = "failed"
                return rec
            path = Path(path)
            rec["existed"] = False
        else:
            remote = run(["git", f"--git-dir={path}", "remote", "get-url", "origin"])
            rec["existing_remote"] = remote
            if remote["returncode"] != 0 or remote["stdout"].strip() != url:
                rec["action"] = "skipped_existing_remote_mismatch"
                rec["result"] = "failed"
                return rec
            upd = run(["git", f"--git-dir={path}", "-c", f"http.proxy={proxy}", "-c", f"https.proxy={proxy}", "-c", "http.version=HTTP/1.1", "remote", "update", "--prune"], timeout=1800)
            rec["action"] = "remote_update_prune"
            rec["update"] = upd
            rec["result"] = "ok" if upd["returncode"] == 0 else "failed"
    if not path.exists():
        clone = run(git_base() + ["clone", "--mirror", url, str(path)], timeout=2400)
        rec["action"] = "clone_mirror"
        rec["clone"] = clone
        rec["result"] = "ok" if clone["returncode"] == 0 else "failed"
    if path.exists():
        rec["head"] = run(["git", f"--git-dir={path}", "rev-parse", "HEAD"])
        rec["branches"] = run(["git", f"--git-dir={path}", "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes"])
        rec["tags"] = run(["git", f"--git-dir={path}", "tag", "--list"])
        rec["remote_head"] = run(["git", f"--git-dir={path}", "symbolic-ref", "refs/remotes/origin/HEAD"])
    return rec

def list_refs(mirror):
    res = run(["git", f"--git-dir={mirror}", "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes", "refs/tags"])
    refs = [x.strip() for x in res["stdout"].splitlines() if x.strip()]
    # Avoid duplicate local/remotes by keeping all; searches are cheap enough.
    return refs

def search_repo(mirror, patterns):
    found = {pat: [] for pat in patterns}
    history = {pat: [] for pat in patterns}
    mirror = Path(mirror)
    if not mirror.exists():
        return {"found": found, "history": history, "refs_checked": 0}
    refs = list_refs(mirror)
    for ref in refs:
        tree = run(["git", f"--git-dir={mirror}", "ls-tree", "-r", "--name-only", ref], timeout=300)
        if tree["returncode"] != 0:
            continue
        names = tree["stdout"].splitlines()
        for pat in patterns:
            for name in names:
                if pat.lower() in name.lower():
                    found[pat].append({"ref": ref, "path": name})
    for pat in patterns:
        hist = run(["git", f"--git-dir={mirror}", "log", "--all", "--full-history", "--name-status", "--", f"*{pat}*"], timeout=300)
        if hist["stdout"]:
            history[pat].append({"returncode": hist["returncode"], "output_head": hist["stdout"][:5000]})
    return {"found": found, "history": history, "refs_checked": len(refs)}

def checkout_default(mirror, prefix):
    mirror = Path(mirror)
    if not mirror.exists():
        return {"result": "missing_mirror"}
    head = run(["git", f"--git-dir={mirror}", "rev-parse", "HEAD"])
    short = head["stdout"][:12] if head["returncode"] == 0 else "unknown"
    dest = checkout_root / f"{prefix}_{short}"
    rec = {"mirror": str(mirror), "checkout": str(dest), "head": head}
    if dest.exists():
        rec["result"] = "exists"
    else:
        clone = run(["git", "clone", str(mirror), str(dest)], timeout=900)
        rec["clone"] = clone
        rec["result"] = "ok" if clone["returncode"] == 0 else "failed"
    if dest.exists():
        rec["status"] = run(["git", "status", "--short"], cwd=dest)
        rec["branch"] = run(["git", "branch", "--show-current"], cwd=dest)
        rec["remote"] = run(["git", "remote", "-v"], cwd=dest)
    return rec

def checkout_branch(mirror, branch, prefix):
    mirror = Path(mirror)
    head = run(["git", f"--git-dir={mirror}", "rev-parse", branch])
    if head["returncode"] != 0:
        return {"result": "missing_branch", "branch": branch, "head": head}
    short = head["stdout"][:12]
    dest = checkout_root / f"{prefix}_{branch.replace('/', '_')}_{short}"
    rec = {"mirror": str(mirror), "branch": branch, "checkout": str(dest), "head": head}
    if dest.exists():
        rec["result"] = "exists"
    else:
        clone = run(["git", "clone", str(mirror), str(dest)], timeout=900)
        rec["clone"] = clone
        if clone["returncode"] == 0:
            co = run(["git", "checkout", branch], cwd=dest)
            rec["checkout_branch"] = co
            rec["result"] = "ok" if co["returncode"] == 0 else "failed"
        else:
            rec["result"] = "failed"
    return rec

curl_verify = run(["curl", "--silent", "--show-error", "--max-time", "20", "--proxy", proxy, "--head", "https://github.com/3dlg-hcvc/SemLayoutDiff"])
git_head = run(git_base() + ["ls-remote", "--symref", "https://github.com/3dlg-hcvc/SemLayoutDiff.git", "HEAD"])
git_blender_heads = run(git_base() + ["ls-remote", "--heads", "https://github.com/3dlg-hcvc/BlenderProc-3DFront.git"])

sem_mirror = mirror_root / "SemLayoutDiff.git"
bp_mirror = mirror_root / "BlenderProc-3DFront-3dlg-hcvc.git"
bp_up_mirror = mirror_root / "BlenderProc-3DFront-yinyunie.git"
sem_clone = ensure_mirror("https://github.com/3dlg-hcvc/SemLayoutDiff.git", sem_mirror)
bp_clone = ensure_mirror("https://github.com/3dlg-hcvc/BlenderProc-3DFront.git", bp_mirror)

bp_branches = bp_clone.get("branches", {}).get("stdout", "")
need_upstream = bp_clone.get("result") != "ok" or not any(x in bp_branches for x in ["3dfront_2d_layout", "3dfront_vis", "layout", "render"])
up_clone = None
if need_upstream:
    up_clone = ensure_mirror("https://github.com/yinyunie/BlenderProc-3DFront.git", bp_up_mirror)

sem_checkout = checkout_default(sem_mirror, "SemLayoutDiff_official")
selected_bp_mirror = bp_mirror if bp_mirror.exists() else bp_up_mirror
selected_bp_branches = (bp_clone if bp_mirror.exists() else (up_clone or {})).get("branches", {}).get("stdout", "")
selected_branch = None
for cand in ["3dfront_2d_layout", "3dfront_vis", "main", "master"]:
    if cand in selected_bp_branches:
        selected_branch = cand
        break
bp_checkout = checkout_branch(selected_bp_mirror, selected_branch, "BlenderProc-3DFront") if selected_branch else {"result": "no_relevant_branch"}

patterns = [
    "preprocess/semlayout",
    "render_dataset_improved_mat.py",
    "multi_render.py",
    "data_process_front3d.py",
    "Bottom_label_map",
    "Bottom_color",
    "Bottom_inst_anno",
    "Updated_Bottom",
    "orthographic",
]
sem_search = search_repo(sem_mirror, patterns)
bp_search = search_repo(bp_mirror, patterns)
up_search = search_repo(bp_up_mirror, patterns) if up_clone else None

required = {}
for item in ["preprocess/semlayout", "render_dataset_improved_mat.py", "multi_render.py", "data_process_front3d.py", "Bottom_label_map", "Bottom_inst_anno"]:
    hits = []
    for repo_name, search in [("SemLayoutDiff", sem_search), ("BlenderProc-3DFront-3dlg-hcvc", bp_search), ("BlenderProc-3DFront-yinyunie", up_search)]:
        if not search:
            continue
        for hit in search["found"].get(item, []):
            hits.append({"repository": repo_name, **hit})
    required[item] = {"found": bool(hits), "hits": hits[:50]}

def license_file(checkout):
    p = Path(checkout)
    if not p.exists():
        return None
    for name in ["LICENSE", "LICENSE.md", "COPYING"]:
        f = p / name
        if f.exists():
            return {"path": str(f), "head": f.read_text(encoding="utf-8", errors="ignore")[:2000]}
    return None

licenses = {
    "SemLayoutDiff": license_file(sem_checkout.get("checkout", "")),
    "BlenderProc_companion": license_file(bp_checkout.get("checkout", "")),
    "BlenderProc_upstream": None,
}

env = {
    "which": {
        "blender": run(["bash", "-lc", "which blender || true"]),
        "blenderproc": run(["bash", "-lc", "which blenderproc || true"]),
        "python3": run(["bash", "-lc", "which python3 || true"]),
        "conda": run(["bash", "-lc", "which conda || true"]),
    },
    "conda_env_list": run(["bash", "-lc", "conda env list || true"]),
    "python_imports": {},
}
for name in ["PIL", "cv2", "numpy", "scipy", "h5py", "bpy", "blenderproc"]:
    env["python_imports"][name] = run(["python3", "-c", f"import importlib.util; spec=importlib.util.find_spec('{name}'); print(spec.origin if spec else 'NOT_FOUND')"])

source_complete = all(required[k]["found"] for k in ["render_dataset_improved_mat.py", "multi_render.py", "data_process_front3d.py"])
runtime_complete = bool(env["which"]["blender"]["stdout"] and env["which"]["blenderproc"]["stdout"]) and all(
    env["python_imports"][n]["stdout"] != "NOT_FOUND" for n in ["PIL", "cv2", "numpy", "scipy"]
)
if source_complete and runtime_complete:
    recommendation = "proceed_to_R8A_one_scene_reconstruction"
elif source_complete and not runtime_complete:
    recommendation = "request_environment_install_approval"
elif not source_complete:
    recommendation = "publicly_available_source_not_found_or_not_yet_resolved"
else:
    recommendation = "external_wrapper"

summary = {
    "proxy": {"remote_proxy_url_sanitized": proxy.replace("127.0.0.1", "loopback")},
    "verification": {"curl": curl_verify, "git_sem_head": git_head, "git_blender_heads": git_blender_heads},
    "semlayoutdiff_clone": sem_clone,
    "blenderproc_companion_clone": bp_clone,
    "blenderproc_upstream_clone": up_clone,
    "checkouts": {"semlayoutdiff": sem_checkout, "blenderproc": bp_checkout},
    "required_source_resolution": required,
    "source_complete": source_complete,
    "runtime_complete": runtime_complete,
    "recommendation": recommendation,
}
write_json(reports / "official_source_resolution_summary.json", summary)
write_json(reports / "semlayoutdiff_complete_source_inventory.json", sem_search)
write_json(reports / "blenderproc_complete_source_inventory.json", {"companion": bp_search, "upstream": up_search})
write_json(reports / "third_party_bottommap_license_audit.json", {"licenses": licenses, "copy_modify_safe": "pending_manual_license_review", "external_wrapper_only": [], "unresolved": [] if licenses["SemLayoutDiff"] else ["SemLayoutDiff license not found in checkout"]})
write_json(reports / "a800_bottommap_environment_inventory.json", env)
missing = []
if not env["which"]["blender"]["stdout"]:
    missing.append("blender command")
if not env["which"]["blenderproc"]["stdout"]:
    missing.append("blenderproc command")
for n in ["PIL", "cv2", "numpy", "scipy", "h5py", "bpy", "blenderproc"]:
    if env["python_imports"][n]["stdout"] == "NOT_FOUND":
        missing.append(f"python module {n}")
write_json(reports / "bottommap_environment_gap.json", {"runtime_complete": runtime_complete, "missing_components": missing})

with (reports / "bottommap_cross_repo_source_map.csv").open("w", newline="", encoding="utf-8") as f:
    fields = ["required_item", "found", "repository", "ref", "path"]
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for item, rec in required.items():
        if rec["hits"]:
            for hit in rec["hits"]:
                w.writerow({"required_item": item, "found": True, "repository": hit["repository"], "ref": hit["ref"], "path": hit["path"]})
        else:
            w.writerow({"required_item": item, "found": False, "repository": "", "ref": "", "path": ""})

(docs / "THIRD_PARTY_BOTTOMMAP_SOURCE_PROVENANCE.md").write_text(
    "# Third-party Bottom-map Source Provenance\\n\\n"
    + json.dumps(summary, ensure_ascii=False, indent=2)[:20000]
    + "\\n",
    encoding="utf-8",
)

print(json.dumps({
    "source_complete": source_complete,
    "runtime_complete": runtime_complete,
    "recommendation": recommendation,
    "required_source_resolution": required,
    "missing_runtime": missing,
}, ensure_ascii=False, indent=2))
PY
'''


def build_remote_script(remote_proxy_url: str) -> str:
    return REMOTE_SCRIPT.replace("__REMOTE_PROXY_URL__", remote_proxy_url)


def sftp_get_files(client: paramiko.SSHClient, files: list[str], local_dir: Path) -> list[str]:
    local_dir = local_dir.resolve()
    local_dir.mkdir(parents=True, exist_ok=True)
    sftp = client.open_sftp()
    downloaded = []
    try:
        for remote_path in files:
            dest = local_dir / Path(remote_path).name
            try:
                sftp.get(remote_path, str(dest))
                downloaded.append(str(dest.relative_to(ROOT.resolve())))
            except FileNotFoundError:
                pass
    finally:
        sftp.close()
    return downloaded


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-proxy-url", default=os.environ.get("LOREFLECTION_LOCAL_PROXY_URL"))
    parser.add_argument("--output", default=str(ROOT / "reports" / "reverse_proxy_source_clone_sanitized.json"))
    parser.add_argument("--download-dir", default=str(ROOT / "outputs" / "manual_review" / "r8a_source_resolution"))
    args = parser.parse_args()

    local_proxy_url, proxy_report = detect_local_proxy(args.local_proxy_url)
    if not local_proxy_url:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps({"local_proxy": proxy_report, "result": "failed"}, ensure_ascii=False, indent=2), encoding="utf-8")
        print("No working local loopback proxy detected. Set LOREFLECTION_LOCAL_PROXY_URL.", file=sys.stderr)
        return 2

    parsed = urlparse(local_proxy_url)
    preferred_remote_port = 17890 if parsed.scheme.startswith("http") else 17891
    outer = inner = None
    forwarder: Forwarder | None = None
    summary: dict[str, Any] = {
        "local_proxy": proxy_report,
        "outer_hop": "222.201.187.180",
        "inner_endpoint": "127.0.0.1:24800",
        "remote_bind_address": "127.0.0.1",
        "public_exposure": False,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    try:
        outer, inner = connect_a800()
        remote_port = choose_remote_port(inner, preferred_remote_port)
        summary["remote_port"] = remote_port
        assert inner.get_transport() is not None
        forwarder = Forwarder(inner.get_transport(), remote_port, parsed.hostname or "127.0.0.1", parsed.port or preferred_remote_port)
        forwarder.start()
        remote_proxy_url = f"{parsed.scheme}://127.0.0.1:{remote_port}"
        time.sleep(1.0)

        rc, out, err = remote_run(inner, build_remote_script(remote_proxy_url), timeout=7200)
        summary["remote_run"] = {"returncode": rc, "stdout_tail": out[-8000:], "stderr_tail": err[-8000:]}

        report_files = [
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/official_source_resolution_summary.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/semlayoutdiff_complete_source_inventory.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/blenderproc_complete_source_inventory.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/bottommap_cross_repo_source_map.csv",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/third_party_bottommap_license_audit.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/a800_bottommap_environment_inventory.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/reports/bottommap_environment_gap.json",
            "/wuqingyaoa800/qiuziyan/LoReflection/docs/THIRD_PARTY_BOTTOMMAP_SOURCE_PROVENANCE.md",
        ]
        downloaded = sftp_get_files(inner, report_files, Path(args.download_dir))
        summary["downloaded_reports"] = downloaded

        cleanup_checks = {}
        if forwarder is not None:
            forwarder.close()
            cleanup_checks["relay_connection_count"] = forwarder.connection_count
            cleanup_checks["relay_errors"] = forwarder.errors[-10:]
        rc2, out2, err2 = remote_run(inner, f"ss -ltn | grep '127.0.0.1:{remote_port}' || true", timeout=30)
        cleanup_checks["server_listener_after_cancel"] = out2.strip()
        rc3, out3, _ = remote_run(inner, "git config --global --get http.proxy || true; git config --global --get https.proxy || true", timeout=30)
        cleanup_checks["global_git_proxy_after"] = out3.strip()
        summary["cleanup"] = cleanup_checks
        summary["result"] = "ok" if rc == 0 else "remote_failed"
        return 0 if rc == 0 else rc
    finally:
        if forwarder is not None and not forwarder.stop_event.is_set():
            forwarder.close()
        if inner is not None:
            inner.close()
        if outer is not None:
            outer.close()
        summary["finished_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
