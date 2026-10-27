# CI launcher regression: a restricted child must be able to launch a child
# with redirected output, just as smoke-tests.ps1 launches AHK. No AHK or input.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true' -or $PSVersionTable.PSEdition -ne 'Desktop') {
    throw 'This probe requires the CI launcher and Windows PowerShell.'
}
Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class MacFlowCiChildTokenProbe
{
    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool CreatePipe(out IntPtr read, out IntPtr write, IntPtr attributes, uint size);
    [DllImport("advapi32.dll", SetLastError = true)]
    static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    public static void Check()
    {
        IntPtr token;
        if (!OpenProcessToken(GetCurrentProcess(), 0x000A, out token)) // query + duplicate
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Restricted child cannot query/duplicate its own token.");
        CloseHandle(token);
        Console.WriteLine("PASS: restricted child can query and duplicate its own token.");
        IntPtr read, write;
        if (!CreatePipe(out read, out write, IntPtr.Zero, 0))
            throw new Win32Exception(Marshal.GetLastWin32Error(), "Restricted child cannot create a pipe with its default DACL.");
        CloseHandle(read); CloseHandle(write);
        Console.WriteLine("PASS: restricted default DACL permits anonymous output pipes.");
    }
}
'@
[MacFlowCiChildTokenProbe]::Check()
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
