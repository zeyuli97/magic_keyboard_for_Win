#Requires -Version 7.5
# Real Windows CI regression; no AHK or keyboard action is executed.
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSEdition -ne 'Core' -or -not $IsWindows) {
    throw 'Run this regression with pwsh 7.5+ on Windows.'
}
$ModulePathHelper = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\tools\ci-clear-module-path.ps1'))
$WindowsPowerShell = [IO.Path]::Combine([Environment]::SystemDirectory, 'WindowsPowerShell\v1.0\powershell.exe')
if (-not [IO.File]::Exists($ModulePathHelper) -or -not [IO.File]::Exists($WindowsPowerShell)) {
    throw 'The shared CI helper and system Windows PowerShell must exist.'
}

# Remove preloaded copies, then invoke ordinary commands to prove autoloading.
$Probe = @'
$ErrorActionPreference = 'Stop'
try {
    if ($PSVersionTable.PSEdition -ne 'Desktop') { throw 'Expected Windows PowerShell.' }
    $DefaultModules = [IO.Path]::Combine($PSHOME, 'Modules')
    if (($env:PSModulePath -split ';') -notcontains $DefaultModules) {
        throw 'Windows PowerShell did not reconstruct its default module path.'
    }
    $PSModuleAutoLoadingPreference = 'All'
    Remove-Module Microsoft.PowerShell.Management, Microsoft.PowerShell.Utility -Force -ErrorAction SilentlyContinue
    if (@(Get-Module Microsoft.PowerShell.Management, Microsoft.PowerShell.Utility).Count -ne 0) {
        throw 'Core test modules could not be unloaded before the autoload check.'
    }
    $Item = Get-Item -LiteralPath $PSHOME
    $Json = ConvertTo-Json -InputObject @{ probe = 'ok' } -Compress
    if ($null -eq $Item -or $Json -cne '{"probe":"ok"}') { throw 'Default cmdlet results were incorrect.' }
    if (@(Get-Module Microsoft.PowerShell.Management, Microsoft.PowerShell.Utility).Count -ne 2) {
        throw 'Both default modules must have auto-loaded.'
    }
    [Console]::Out.WriteLine('MODULE_AUTOLOAD_OK')
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
'@

function Test-RawWindowsPowerShellAutoload {
    # Direct .NET launch deliberately avoids PowerShell's powershell.exe
    # invocation special case, which would rewrite PSModulePath for the child.
    $StartInfo = [Diagnostics.ProcessStartInfo]::new()
    $StartInfo.FileName = $WindowsPowerShell
    $StartInfo.Arguments = '-NoLogo -NoProfile -NonInteractive -EncodedCommand ' +
        [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Probe))
    $StartInfo.UseShellExecute = $false
    $StartInfo.CreateNoWindow = $true
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError = $true
    # Do not change StartInfo.Environment: the helper's actual environment is inherited.
    $Child = [Diagnostics.Process]::new()
    $Child.StartInfo = $StartInfo
    $Started = $false
    try {
        if ($null -ne [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')) {
            throw 'Raw child launch requires a genuinely absent parent PSModulePath.'
        }
        $Started = $Child.Start()
        if (-not $Started) { throw 'Could not start the raw Windows PowerShell probe.' }
        $OutputTask = $Child.StandardOutput.ReadToEndAsync()
        $ErrorTask = $Child.StandardError.ReadToEndAsync()
        if (-not $Child.WaitForExit(15000)) {
            $Child.Kill()
            if (-not $Child.WaitForExit(2000)) { throw 'Timed-out child termination was not confirmed.' }
            throw 'Windows PowerShell autoload exceeded 15 seconds.'
        }
        if (-not [Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($OutputTask, $ErrorTask), 2000)) {
            throw 'Windows PowerShell output capture did not complete.'
        }
        $OutputText = $OutputTask.GetAwaiter().GetResult()
        $ErrorText = $ErrorTask.GetAwaiter().GetResult()
        if ($ErrorText) { [Console]::Error.Write($ErrorText) }
        if ($Child.ExitCode -ne 0 -or $OutputText.Trim() -cne 'MODULE_AUTOLOAD_OK') {
            throw "Raw Windows PowerShell autoload failed (exit $($Child.ExitCode))."
        }
    } finally {
        if ($Started -and -not $Child.HasExited) {
            $Child.Kill()
            if (-not $Child.WaitForExit(2000)) { throw 'Probe process cleanup was not confirmed.' }
        }
        $Child.Dispose()
    }
}

$OriginalModulePath = [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')
$ExitCode = 0
try {
    $Cases = @(
        @{ Name = 'nonempty'; Value = [IO.Path]::Combine($PSHOME, 'Modules') },
        @{ Name = 'empty'; Value = '' },
        @{ Name = 'missing'; Value = $null }
    )
    foreach ($Case in $Cases) {
        $env:PSModulePath = $Case.Value
        if (-not [object]::Equals($Case.Value, [Environment]::GetEnvironmentVariable('PSModulePath', 'Process'))) {
            throw "Could not establish the $($Case.Name) precondition; null and empty must be distinct."
        }
        . $ModulePathHelper
        if ($null -ne [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')) {
            throw "Shared helper did not remove the $($Case.Name) environment value."
        }
        Test-RawWindowsPowerShellAutoload
        [Console]::Out.WriteLine("PASS: $($Case.Name) -> absent; raw Windows PowerShell default autoload.")
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    $ExitCode = 1
} finally {
    try {
        $env:PSModulePath = $OriginalModulePath
        if (-not [object]::Equals($OriginalModulePath, [Environment]::GetEnvironmentVariable('PSModulePath', 'Process'))) {
            throw 'Original PSModulePath was not restored exactly.'
        }
    } catch {
        [Console]::Error.WriteLine($_.Exception.Message)
        $ExitCode = 1
    }
}
exit $ExitCode
