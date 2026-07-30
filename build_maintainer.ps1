$ErrorActionPreference = "Stop"

python -m pip install -e ".[build]"
python scripts/build_assets.py
pyinstaller --noconfirm --clean --windowed `
  --name "PDF-SmartForms-Studio-Maintainer" `
  --runtime-hook "scripts/maintainer_runtime_hook.py" `
  --icon "assets/app-icon.ico" `
  "src/pdf_smartforms/__main__.py"

Write-Host "Maintainer-Version erstellt: dist\\PDF-SmartForms-Studio-Maintainer\\"
