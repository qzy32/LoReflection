@echo off
setlocal
cd /d "%~dp0\..\.."

if "%P0_NUM_SAMPLES%"=="" set P0_NUM_SAMPLES=60
if "%P0_IMAGE_SIZE%"=="" set P0_IMAGE_SIZE=256
if "%P0_SEED%"=="" set P0_SEED=4411
if "%QWEN_SOURCE_MODE%"=="" set QWEN_SOURCE_MODE=procedural_contract
if "%QWEN_3DFRONT_ROOT%"=="" set QWEN_3DFRONT_ROOT=C:\path\to\3D-Front
if "%QWEN_OUTPUT_ROOT%"=="" set QWEN_OUTPUT_ROOT=data\loreflection_qwen_arch_control

python -m loreflection.qwen_arch_control.build_qwen_arch_control_dataset ^
  --source-mode %QWEN_SOURCE_MODE% ^
  --data-root "%QWEN_3DFRONT_ROOT%" ^
  --output-root "%QWEN_OUTPUT_ROOT%" ^
  --num-samples %P0_NUM_SAMPLES% ^
  --image-size %P0_IMAGE_SIZE% ^
  --seed %P0_SEED%
if errorlevel 1 exit /b %errorlevel%

python tools\validate_arch_incontext_training_metadata.py ^
  "%QWEN_OUTPUT_ROOT%\metadata.csv" ^
  --dataset-base "%QWEN_OUTPUT_ROOT%" ^
  --output "%QWEN_OUTPUT_ROOT%\audits\metadata_validator_report.json"
if errorlevel 1 exit /b %errorlevel%

python -m loreflection.qwen_arch_control.audit_palette_exact "%QWEN_OUTPUT_ROOT%"
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.audit_prompt_no_coordinate_leakage "%QWEN_OUTPUT_ROOT%"
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.audit_qwen_arch_control_dataset "%QWEN_OUTPUT_ROOT%"
if errorlevel 1 exit /b %errorlevel%
python -m loreflection.qwen_arch_control.preview_qwen_arch_dataset "%QWEN_OUTPUT_ROOT%"
exit /b %errorlevel%
