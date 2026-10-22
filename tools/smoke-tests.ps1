[CmdletBinding()]
param(
    [string] $AutoHotkeyPath,
    [switch] $SelfTest
)
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MainScript = Join-Path $ProjectRoot "src\ahk\main.ahk"
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    Write-Error "This check requires Windows. No runtime/hardware test was performed."
    exit 2
}
if (-not $AutoHotkeyPath) {
    $Found = Get-Command AutoHotkey64.exe -ErrorAction SilentlyContinue
    if ($Found) { $AutoHotkeyPath = $Found.Source }
}
if (-not $AutoHotkeyPath) {
    $Candidate = Join-Path $env:ProgramFiles "AutoHotkey\v2\AutoHotkey64.exe"
    if (Test-Path -LiteralPath $Candidate -PathType Leaf) { $AutoHotkeyPath = $Candidate }
}
if (-not $AutoHotkeyPath -or -not (Test-Path -LiteralPath $AutoHotkeyPath -PathType Leaf)) {
    Write-Error "Supply an already installed AHK v2.0.19+ 64-bit runtime with -AutoHotkeyPath. Nothing was installed."
    exit 2
}
$AutoHotkeyPath = (Resolve-Path -LiteralPath $AutoHotkeyPath).Path
if (-not (Test-Path -LiteralPath $MainScript -PathType Leaf)) {
    Write-Error "Missing main.ahk."
    exit 1
}
if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot "build\generated\macflow.ini"))) {
    Write-Error "Missing generated configuration. Run Python config validation/generation first."
    exit 1
}
function Invoke-AhkCheck([string[]] $RuntimeArgs, [string] $Label) {
    $Arguments = @("/ErrorStdOut=UTF-8") + $RuntimeArgs
    $Child = Start-Process -FilePath $AutoHotkeyPath -ArgumentList $Arguments -PassThru -NoNewWindow
    if (-not $Child.WaitForExit(15000)) {
        Stop-Process -Id $Child.Id -ErrorAction SilentlyContinue
        throw "$Label timed out; only the process started by this check was stopped."
    }
    $Child.Refresh()
    if ($Child.ExitCode -ne 0) {
        throw "$Label failed with exit code $($Child.ExitCode)."
    }
    Write-Output "$Label passed. This is not a keyboard compatibility test."
}
try {
    Invoke-AhkCheck -RuntimeArgs @("/validate", ('"' + $MainScript + '"')) -Label "AHK syntax validation"
    if ($SelfTest) {
        Invoke-AhkCheck -RuntimeArgs @(('"' + $MainScript + '"'), "--self-test") -Label "AHK Native Mode initialization"
    }
    Write-Output "No mapping was enabled; hardware results remain NOT TESTED."
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
