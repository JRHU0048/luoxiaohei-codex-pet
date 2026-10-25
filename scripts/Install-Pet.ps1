[CmdletBinding()]
param(
    [string]$CodexHome=$(if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}),
    [string]$PythonExecutable,
    [switch]$WhatIf
)
$ErrorActionPreference='Stop'
if(-not $PythonExecutable -and $env:PYTHON){$PythonExecutable=$env:PYTHON}
if(-not $PythonExecutable){
    $bundled=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if(Test-Path -LiteralPath $bundled){$PythonExecutable=$bundled}
}
if(-not $PythonExecutable){$command=Get-Command python -ErrorAction SilentlyContinue;if($command){$PythonExecutable=$command.Source}}
if(-not $PythonExecutable){throw 'Python 3.11+ is required. Supply -PythonExecutable or use the Codex bundled Python runtime.'}
& $PythonExecutable -c 'import sys; sys.exit(sys.version_info < (3, 11))'
if($LASTEXITCODE -ne 0){throw 'A working Python 3.11+ runtime is required.'}
$arguments=@("$PSScriptRoot\install_pet.py",'--codex-home',$CodexHome)
if($WhatIf){$arguments+='--dry-run'}
& $PythonExecutable @arguments
if($LASTEXITCODE -ne 0){throw 'Pet installation did not complete. See the error above.'}
