# CI launcher regression: a restricted child must be able to launch a child
# with redirected output, just as smoke-tests.ps1 launches AHK. No AHK or input.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $PSVersionTable.PSEdition -ne 'Desktop') {
    throw 'This probe requires the CI launcher and Windows PowerShell.'
}
$Info = [Diagnostics.ProcessStartInfo]::new()
$Info.FileName = Join-Path $PSHOME 'powershell.exe'
$Info.Arguments = '-NoLogo -NoProfile -NonInteractive -Command "[Console]::Out.WriteLine(''CI_NESTED_OUT''); [Console]::Error.WriteLine(''CI_NESTED_ERR''); exit 19"'
$Info.UseShellExecute = $false
$Info.CreateNoWindow = $true
$Info.RedirectStandardOutput = $true
$Info.RedirectStandardError = $true
$Child = [Diagnostics.Process]::new()
$Child.StartInfo = $Info
$Started = $false
try {
    $Started = $Child.Start()
    if (-not $Started) { throw 'Nested CI child did not start.' }
    $OutputTask = $Child.StandardOutput.ReadToEndAsync()
    $ErrorTask = $Child.StandardError.ReadToEndAsync()
    if (-not $Child.WaitForExit(15000)) { throw 'Nested CI child exceeded 15 seconds.' }
    if (-not [Threading.Tasks.Task]::WaitAll([Threading.Tasks.Task[]]@($OutputTask, $ErrorTask), 2000)) {
        throw 'Nested CI child output did not close.'
    }
    if ($Child.ExitCode -ne 19 -or $OutputTask.Result.Trim() -cne 'CI_NESTED_OUT' -or
        $ErrorTask.Result.Trim() -cne 'CI_NESTED_ERR') {
        throw 'Nested child exit code or redirected output was lost.'
    }
    [Console]::Out.WriteLine('PASS: restricted child can launch a nested process and capture both output streams and exit code 19.')
}
catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}
finally {
    if ($Started -and -not $Child.HasExited) {
        $Child.Kill()
        if (-not $Child.WaitForExit(2000)) { throw 'Nested CI child cleanup was not confirmed.' }
    }
    $Child.Dispose()
}
# Deliberately nonzero: the outer CI launcher must preserve this exact value.
exit 37
