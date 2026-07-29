$ErrorActionPreference = "Stop"

python -m pip install -e ".[build]"
pyinstaller --noconfirm --clean --windowed `
  --name "PDF-SmartForms-Studio" `
  "src/pdf_smartforms/__main__.py"

Write-Host "Build erstellt: dist\\PDF-SmartForms-Studio"

