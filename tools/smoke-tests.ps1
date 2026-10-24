[CmdletBinding()]
param(
    [string] $AutoHotkeyPath,
    [switch] $SelfTest,
    [switch] $RegistrationTest
)
$ErrorActionPreference = "Stop"
if ($SelfTest -and $RegistrationTest) {
    [Console]::Error.WriteLine("Choose only one optional check: -SelfTest or -RegistrationTest.")
    exit 2
}
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$MainScript = Join-Path $ProjectRoot "src\ahk\main.ahk"
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    [Console]::Error.WriteLine("This check requires Windows. No runtime/hardware test was performed.")
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
    [Console]::Error.WriteLine("Supply an installed AHK v2.0.19+ 64-bit runtime with -AutoHotkeyPath. Nothing was installed.")
    exit 2
}
$AutoHotkeyPath = (Resolve-Path -LiteralPath $AutoHotkeyPath).Path
if (-not (Test-Path -LiteralPath $MainScript -PathType Leaf)) {
    [Console]::Error.WriteLine("Missing main.ahk.")
    exit 1
}

function Invoke-AhkCheck([string[]] $RuntimeArgs, [string] $Label) {
    # /validate exists in v2.0.19's ParseCmdLineArgs and is documented at:
    # https://www.autohotkey.com/docs/v2/Scripts.htm#validate
    # It loads the original main.ahk then exits without executing its startup.
    # All switches precede the script path; quoted paths stay single arguments.
    $StartInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $StartInfo.FileName = $AutoHotkeyPath
    $StartInfo.Arguments = (@("/ErrorStdOut=UTF-8") + $RuntimeArgs) -join " "
    $StartInfo.WorkingDirectory = $ProjectRoot
    $StartInfo.UseShellExecute = $false
    $StartInfo.CreateNoWindow = $true
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError = $true
    $StartInfo.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)
    $StartInfo.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)

    $Child = [System.Diagnostics.Process]::new()
    $Child.StartInfo = $StartInfo
    $Started = $false
    try {
        $Started = $Child.Start()
        if (-not $Started) { throw "$Label could not start the supplied runtime." }

        # Drain both pipes concurrently, so a long parser diagnostic cannot fill
        # one pipe and deadlock while the parent waits on the other.
        $StdoutTask = $Child.StandardOutput.ReadToEndAsync()
        $StderrTask = $Child.StandardError.ReadToEndAsync()
        $TimedOut = -not $Child.WaitForExit(15000)
        if ($TimedOut) {
            $Child.Kill()
            if (-not $Child.WaitForExit(2000)) {
                throw "$Label exceeded 15 seconds; termination of this check's child could not be confirmed."
            }
        }
        $StreamsClosed = [System.Threading.Tasks.Task]::WaitAll(
            [System.Threading.Tasks.Task[]]@($StdoutTask, $StderrTask), 2000)
        if (-not $StreamsClosed) {
            throw "$Label output capture did not close after the runtime exited."
        }
        $StdoutText = $StdoutTask.GetAwaiter().GetResult()
        $StderrText = $StderrTask.GetAwaiter().GetResult()
        if ($StdoutText) { [Console]::Out.Write($StdoutText) }
        if ($StderrText) { [Console]::Error.Write($StderrText) }
        if ($TimedOut) {
            throw "$Label exceeded 15 seconds; only this check's child process was stopped."
        }
        if ($Child.ExitCode -ne 0) {
            throw "$Label failed with exit code $($Child.ExitCode); see captured diagnostics above."
        }
        # main.ahk reports #Warn findings on stdout, where /validate still exits 0.
        # A warning is a source defect, so it fails the check instead of passing.
        if (($StdoutText + $StderrText) -match '==> Warning:') {
            throw "$Label reported AHK warnings; see captured diagnostics above."
        }
        Write-Output "$Label passed. This is not a keyboard compatibility test."
    }
    finally {
        if ($Started) {
            try {
                if (-not $Child.HasExited) { $Child.Kill() }
            }
            catch {
                [Console]::Error.WriteLine("Could not confirm cleanup of this check's child process.")
            }
        }
        $Child.Dispose()
    }
}

try {
    Invoke-AhkCheck -RuntimeArgs @("/validate", ('"' + $MainScript + '"')) -Label "AHK syntax validation"
    if (($SelfTest -or $RegistrationTest) -and -not (Test-Path -LiteralPath (Join-Path $ProjectRoot "build\generated\macflow.ini"))) {
        throw "Missing generated configuration. Run Python config validation/generation first."
    }
    if ($SelfTest) {
        # This application-defined argument loads configuration in Native Mode
        # and exits before hooks or mappings are installed.
        Invoke-AhkCheck -RuntimeArgs @(('"' + $MainScript + '"'), "--self-test") -Label "AHK Native Mode initialization"
    }
    if ($RegistrationTest) {
        # Registration follows the normal HotIf/Hotkey/emergency paths while
        # Native remains enforced. This does not test physical input or send keys.
        Invoke-AhkCheck -RuntimeArgs @(('"' + $MainScript + '"'), "--registration-test") -Label "AHK Native Mode hotkey registration"
    }
    Write-Output "No mapping was enabled; hardware results remain NOT TESTED."
    exit 0
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
