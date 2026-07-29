$ErrorActionPreference = "Stop"

python -m pip install -e ".[build]"
python scripts/build_assets.py
pyinstaller --noconfirm --clean --windowed `
  --name "PDF-SmartForms-Studio" `
  --icon "assets/app-icon.ico" `
  "src/pdf_smartforms/__main__.py"

$packageRoot = "dist\\PDF-SmartForms-Studio"
New-Item -ItemType Directory -Force "$packageRoot\\docs" | Out-Null
Copy-Item "README.md", "LICENSE.md", "PRIVACY.md", "SECURITY.md" $packageRoot
Copy-Item -Recurse "docs\\user-guide" "$packageRoot\\docs\\user-guide"
Copy-Item -Recurse "docs\\screenshots" "$packageRoot\\docs\\screenshots"
python scripts/package_release.py

Write-Host "Releasepaket erstellt: release\\"
