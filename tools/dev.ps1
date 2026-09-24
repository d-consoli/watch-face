param(
    [ValidateSet('Build', 'Install', 'Validate', 'Preview', 'Capture', 'Doctor')]
    [string]$Action = 'Build',
    [string]$Serial
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    switch ($Action) {
        'Build' { python tools/build_apk.py; if ($LASTEXITCODE) { throw 'Build failed.' } }
        'Install' {
            $installArgs = @('tools/build_apk.py', '--install')
            if ($Serial) { $installArgs += @('--serial', $Serial) }
            python @installArgs
            if ($LASTEXITCODE) { throw 'Build or installation failed.' }
        }
        'Validate' { python tools/validate.py; if ($LASTEXITCODE) { throw 'Validation failed.' } }
        'Preview' {
            python tools/generate_face.py
            if ($LASTEXITCODE) { throw 'Generation failed.' }
            python tools/render_preview.py
            if ($LASTEXITCODE) { throw 'Preview rendering failed. Install requirements-dev.txt.' }
            Start-Process (Join-Path $repoRoot 'docs/preview.html')
        }
        'Capture' {
            $captureArgs = @('tools/capture.py')
            if ($Serial) { $captureArgs += @('--serial', $Serial) }
            python @captureArgs
            if ($LASTEXITCODE) { throw 'Capture failed.' }
        }
        'Doctor' {
            python --version
            java -version
            python -c "import sys; sys.path.insert(0,'tools'); from build_apk import find_sdk; print('Android SDK:',find_sdk())"
            if ($LASTEXITCODE) { throw 'SDK not found.' }
            if (Get-Command adb -ErrorAction SilentlyContinue) { adb devices -l }
            else { Write-Host 'Add Android SDK platform-tools to PATH to use adb pairing commands.' }
        }
    }
} finally { Pop-Location }
