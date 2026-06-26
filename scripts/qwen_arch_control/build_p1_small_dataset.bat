@echo off
setlocal
if "%QWEN_SOURCE_MODE%"=="" set QWEN_SOURCE_MODE=raw_3dfront
if "%QWEN_3DFRONT_ROOT%"=="" set QWEN_3DFRONT_ROOT=/wuqingyaoa800/chengjiajia_datas/dataset/JIAQI-CHEN/3D-Front
if "%QWEN_OUTPUT_ROOT%"=="" set QWEN_OUTPUT_ROOT=data/loreflection_qwen_arch_control_p1_small
if "%P1_NUM_SAMPLES%"=="" set P1_NUM_SAMPLES=200
if "%P1_IMAGE_SIZE%"=="" set P1_IMAGE_SIZE=256
if "%P1_SEED%"=="" set P1_SEED=5521
python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset --source-mode %QWEN_SOURCE_MODE% --data-root "%QWEN_3DFRONT_ROOT%" --output-root "%QWEN_OUTPUT_ROOT%" --num-samples %P1_NUM_SAMPLES% --image-size %P1_IMAGE_SIZE% --seed %P1_SEED%
python tools/validate_arch_incontext_training_metadata.py "%QWEN_OUTPUT_ROOT%/metadata.csv" --dataset-base "%QWEN_OUTPUT_ROOT%" --output "%QWEN_OUTPUT_ROOT%/audits/metadata_validator_report.json"
python -m loreflection.qwen_arch_control.audit_palette_exact "%QWEN_OUTPUT_ROOT%"
python -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage "%QWEN_OUTPUT_ROOT%"
python -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset "%QWEN_OUTPUT_ROOT%"
python -m loreflection.qwen_arch_control.preview_qwen_arch_dataset "%QWEN_OUTPUT_ROOT%"
