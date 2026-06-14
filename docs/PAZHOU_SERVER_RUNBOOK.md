# Pazhou Server Runbook

## Purpose

This runbook describes the sanitized LoReflection server onboarding workflow for Pazhou machines. It is used to:

- clone the project;
- configure server paths;
- run dry-run checks;
- inspect real source locations;
- prepare val50 construction;
- avoid recording passwords or private SSH details.

It is not a place to store SSH credentials, passwords, private keys, tokens, or account/password combinations.

## Security Warning

- Do not commit passwords.
- Do not commit SSH guide files.
- Do not commit `paths.local.env`.
- Do not commit model weights or datasets.
- Do not store large outputs under `/home`.

## Recommended Work Roots

```text
A800 work root: /wuqingyaoa800/qiuziyan
3090 work root: /wuqingyao/custom_home/qiuziyan
```

Use these work roots for projects, model caches, datasets, logs, and outputs. Avoid `/home` for LoReflection repositories, datasets, checkpoints, model weights, and large experiment output.

## Execution Mode

The current A800 workflow is direct SSH. It is not treated as a Slurm workflow by default.

- Use SSH or VSCode Remote-SSH to log in.
- Activate conda or another Python environment after login.
- Run ordinary `bash`, `python`, `torchrun`, or `accelerate` commands in later training stages.
- Do not use `sbatch`, `salloc`, or `sinfo` as the default workflow for this server.

## Recommended Server Order

1. SSH / VSCode Remote-SSH login to the server.
2. Enter the recommended work directory.
3. Clone LoReflection.
4. Checkout `interface-freeze-v1` or latest `main`.
5. Create a conda environment or activate an existing environment.
6. Copy the paths template to `paths.local.env`.
7. Manually fill real paths.
8. Run `check_server_paths.py`.
9. Run `inspect_real_sources.py`.
10. Only then build the val50 manifest.
11. Do not train before val50 conversion and manual audit.

## Commands

These command templates intentionally contain no password, token, private key, or SSH host secret.

```bash
cd /wuqingyaoa800/qiuziyan
git clone https://github.com/qzy32/LoReflection.git
cd LoReflection
git checkout interface-freeze-v1
cp server_configs/paths.pazhou.template.env server_configs/paths.local.env
```

Edit `server_configs/paths.local.env` on the server and fill real local paths. Do not commit it.

```bash
python tools/check_server_paths.py \
  --env-file server_configs/paths.local.env \
  --report reports/server_path_check_report.json \
  --strict
```

```bash
python tools/inspect_real_sources.py \
  --env-file server_configs/paths.local.env \
  --output reports/real_source_inspection_report.json \
  --max-files 5 \
  --verbose
```

You can also run the wrapper:

```bash
bash scripts/server_step3_dryrun_pazhou.sh
```

The dry-run checks paths and source presence only. It does not download data, download models, run real conversion, load model weights, or start training.
