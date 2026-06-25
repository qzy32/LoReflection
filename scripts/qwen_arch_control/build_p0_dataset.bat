@echo off
setlocal
cd /d "%~dp0\..\.."

if "%P0_NUM_SAMPLES%"=="" set P0_NUM_SAMPLES=60
if "%P0_IMAGE_SIZE%"=="" set P0_IMAGE_SIZE=256
if "%P0_SEED%"=="" set P0_SEED=4411

python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset ^
  --output-root data/loreflection_qwen_arch_control ^
  --num-samples %P0_NUM_SAMPLES% ^
  --image-size %P0_IMAGE_SIZE% ^
  --seed %P0_SEED%
if errorlevel 1 exit /b %errorlevel%

python tools\validate_arch_incontext_training_metadata.py ^
  data\loreflection_qwen_arch_control\metadata.csv ^
  --dataset-base data\loreflection_qwen_arch_control ^
  --output data\loreflection_qwen_arch_control\audits\metadata_validator_report.json
if errorlevel 1 exit /b %errorlevel%

python -m loreflection.qwen_arch_control.audit_palette_exact data\loreflection_qwen_arch_control
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage data\loreflection_qwen_arch_control
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset data\loreflection_qwen_arch_control
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.preview_qwen_arch_dataset data\loreflection_qwen_arch_control
exit /b %errorlevel%
