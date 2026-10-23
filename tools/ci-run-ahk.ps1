[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $AutoHotkeyPath
)
# CI helper only. It lowers a new process token; it never changes UAC, accounts,
# registry, security policy, autorun, or the runtime's administrator rejection.
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -cne 'true') {
    [Console]::Error.WriteLine('This launcher is restricted to GitHub Actions CI. Use smoke-tests.ps1 from a standard user session.')
    exit 2
}
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    [Console]::Error.WriteLine('This CI helper requires Windows; no runtime or hardware check ran.')
    exit 2
}
if (-not [Environment]::Is64BitProcess) {
    [Console]::Error.WriteLine('Run this helper from 64-bit PowerShell.')
    exit 2
}
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$SmokeScript = Join-Path $PSScriptRoot 'smoke-tests.ps1'
try {
    if (-not (Test-Path -LiteralPath $AutoHotkeyPath -PathType Leaf)) {
        throw 'Supply the existing 64-bit AutoHotkey executable; this helper installs nothing.'
    }
    if (-not (Test-Path -LiteralPath $SmokeScript -PathType Leaf)) {
        throw 'Missing tools/smoke-tests.ps1.'
    }
    $AutoHotkeyPath = (Resolve-Path -LiteralPath $AutoHotkeyPath).Path
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try {
        $Principal = [Security.Principal.WindowsPrincipal]::new($Identity)
        $IsAdministrator = $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    }
    finally { $Identity.Dispose() }
    if (-not $IsAdministrator) {
        # The existing smoke script owns the 15-second timeout for each AHK run.
        & $SmokeScript -AutoHotkeyPath $AutoHotkeyPath -RegistrationTest
        exit $LASTEXITCODE
    }

    # GitHub-hosted Windows runners are administrators with UAC disabled.
    # Keep that environment outside the AHK process instead of bypassing its guard.
    # Official API contracts:
    # https://learn.microsoft.com/windows/win32/api/winsafer/nf-winsafer-safercreatelevel
    # https://learn.microsoft.com/windows/win32/api/winsafer/nf-winsafer-safercomputetokenfromlevel
    # https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-createprocessasuserw
    # https://learn.microsoft.com/windows/win32/api/securitybaseapi/nf-securitybaseapi-checktokenmembership
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

public static class MacFlowCiRestrictedRunner
{
    const uint TokenQuery = 0x0008, TokenDuplicate = 0x0002;
    const uint PrimaryAccess = 0x008B; // query, duplicate, assign-primary, adjust-default
    const uint WaitObject0 = 0, WaitTimeout = 258;
    const uint CreateSuspended = 4, StartfUseStdHandles = 0x100;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct StartupInfo
    {
        public uint cb;
        public string lpReserved, lpDesktop, lpTitle;
        public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars;
        public uint dwFillAttribute, dwFlags;
        public ushort wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct SecurityAttributes
    {
        public uint Length;
        public IntPtr Descriptor;
        [MarshalAs(UnmanagedType.Bool)] public bool Inherit;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct ProcessInfo { public IntPtr Process, Thread; public uint ProcessId, ThreadId; }
    [StructLayout(LayoutKind.Sequential)]
    struct SidAndAttributes { public IntPtr Sid; public uint Attributes; }
    [StructLayout(LayoutKind.Sequential)]
    struct BasicJobLimits
    {
        public long PerProcessTime, PerJobTime;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSet, MaximumWorkingSet;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass, SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)]
    struct IoCounters { public ulong ReadOperations, WriteOperations, OtherOperations, ReadBytes, WriteBytes, OtherBytes; }
    [StructLayout(LayoutKind.Sequential)]
    struct ExtendedJobLimits
    {
        public BasicJobLimits Basic;
        public IoCounters Io;
        public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
    }

    [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", SetLastError = true)] static extern IntPtr GetStdHandle(int handle);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr CreateFileW(string name, uint access, uint share, ref SecurityAttributes attributes, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool DuplicateHandle(IntPtr sourceProcess, IntPtr source, IntPtr targetProcess, out IntPtr target, uint access, bool inherit, uint options);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll", SetLastError = true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool TerminateProcess(IntPtr process, uint exitCode);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool GetExitCodeProcess(IntPtr process, out uint exitCode);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern IntPtr CreateJobObjectW(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedJobLimits limits, uint size);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError = true)] static extern bool TerminateJobObject(IntPtr job, uint exitCode);
    [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr memory);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool OpenProcessToken(IntPtr process, uint access, out IntPtr token);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferCreateLevel(uint scope, uint level, uint flags, out IntPtr handle, IntPtr reserved);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferComputeTokenFromLevel(IntPtr level, IntPtr input, out IntPtr output, uint flags, IntPtr reserved);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SaferCloseLevel(IntPtr level);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool DuplicateTokenEx(IntPtr token, uint access, IntPtr attributes, int impersonationLevel, int tokenType, out IntPtr duplicate);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool GetTokenInformation(IntPtr token, int infoClass, IntPtr info, uint size, out uint needed);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool SetTokenInformation(IntPtr token, int infoClass, ref SidAndAttributes info, uint size);
    [DllImport("advapi32.dll", SetLastError = true)] static extern bool CheckTokenMembership(IntPtr token, IntPtr sid, out bool member);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)] static extern bool ConvertStringSidToSidW(string value, out IntPtr sid);
    [DllImport("advapi32.dll")] static extern bool IsValidSid(IntPtr sid);
    [DllImport("advapi32.dll")] static extern uint GetLengthSid(IntPtr sid);
    [DllImport("advapi32.dll")] static extern IntPtr GetSidSubAuthorityCount(IntPtr sid);
    [DllImport("advapi32.dll")] static extern IntPtr GetSidSubAuthority(IntPtr sid, uint index);
    [DllImport("advapi32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool CreateProcessAsUserW(IntPtr token, string application, StringBuilder commandLine,
        IntPtr processAttributes, IntPtr threadAttributes, bool inheritHandles, uint flags,
        IntPtr environment, string directory, ref StartupInfo startup, out ProcessInfo process);

    static void Check(bool success, string operation)
    {
        if (!success)
        {
            int error = Marshal.GetLastWin32Error();
            throw new Win32Exception(error, operation + " failed; code=" + error);
        }
    }
    static void Close(ref IntPtr handle)
    {
        if (handle != IntPtr.Zero) { CloseHandle(handle); handle = IntPtr.Zero; }
    }
    static IntPtr ReadTokenInfo(IntPtr token, int infoClass)
    {
        uint size;
        GetTokenInformation(token, infoClass, IntPtr.Zero, 0, out size);
        if (size == 0 || size > 65536) throw new InvalidOperationException("Invalid token information size.");
        IntPtr buffer = Marshal.AllocHGlobal((int)size);
        try { Check(GetTokenInformation(token, infoClass, buffer, size, out size), "GetTokenInformation"); return buffer; }
        catch { Marshal.FreeHGlobal(buffer); throw; }
    }
    static uint IntegrityRid(IntPtr token)
    {
        IntPtr buffer = ReadTokenInfo(token, 25); // TokenIntegrityLevel
        try
        {
            IntPtr sid = Marshal.ReadIntPtr(buffer);
            if (sid == IntPtr.Zero || !IsValidSid(sid)) throw new InvalidOperationException("Invalid integrity SID.");
            IntPtr countPointer = GetSidSubAuthorityCount(sid);
            if (countPointer == IntPtr.Zero) throw new InvalidOperationException("Missing integrity SID count.");
            byte count = Marshal.ReadByte(countPointer);
            if (count == 0) throw new InvalidOperationException("Empty integrity SID.");
            IntPtr rid = GetSidSubAuthority(sid, (uint)(count - 1));
            if (rid == IntPtr.Zero) throw new InvalidOperationException("Missing integrity RID.");
            return unchecked((uint)Marshal.ReadInt32(rid));
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }
    static void LowerToMedium(IntPtr token)
    {
        uint rid = IntegrityRid(token);
        if (rid < 0x2000) throw new InvalidOperationException("Refusing to raise a token's integrity level.");
        if (rid == 0x2000) return;
        IntPtr sid = IntPtr.Zero;
        try
        {
            Check(ConvertStringSidToSidW("S-1-16-8192", out sid), "Create medium integrity SID");
            SidAndAttributes label = new SidAndAttributes { Sid = sid, Attributes = 0x20 };
            uint size = (uint)Marshal.SizeOf(typeof(SidAndAttributes)) + GetLengthSid(sid);
            Check(SetTokenInformation(token, 25, ref label, size), "Lower copied token to medium integrity");
        }
        finally { if (sid != IntPtr.Zero) LocalFree(sid); }
    }
    static void VerifyStandardToken(IntPtr token)
    {
        IntPtr elevation = ReadTokenInfo(token, 20); // TokenElevation
        try
        {
            if (Marshal.ReadInt32(elevation) != 0) throw new InvalidOperationException("Child token is still elevated; refusing to launch AHK.");
        }
        finally { Marshal.FreeHGlobal(elevation); }
        if (IntegrityRid(token) != 0x2000) throw new InvalidOperationException("Child token is not medium integrity.");
        IntPtr impersonation = IntPtr.Zero, adminSid = IntPtr.Zero;
        try
        {
            // CheckTokenMembership requires an impersonation token, not primary.
            Check(DuplicateTokenEx(token, TokenQuery, IntPtr.Zero, 2, 2, out impersonation), "Duplicate token for membership check");
            Check(ConvertStringSidToSidW("S-1-5-32-544", out adminSid), "Create Administrators SID");
            bool admin;
            Check(CheckTokenMembership(impersonation, adminSid, out admin), "Check Administrators membership");
            if (admin) throw new InvalidOperationException("Child token still has enabled administrator membership.");
        }
        finally { Close(ref impersonation); if (adminSid != IntPtr.Zero) LocalFree(adminSid); }
    }
    static IntPtr NullInput()
    {
        SecurityAttributes attributes = new SecurityAttributes();
        attributes.Length = (uint)Marshal.SizeOf(typeof(SecurityAttributes));
        attributes.Inherit = true;
        IntPtr handle = CreateFileW("NUL", 0x80000000, 3, ref attributes, 3, 0, IntPtr.Zero);
        Check(handle != new IntPtr(-1), "Open null CI stdin");
        return handle;
    }
    static IntPtr InheritStandardHandle(int kind)
    {
        IntPtr source = GetStdHandle(kind), copy;
        if (source == IntPtr.Zero || source == new IntPtr(-1))
            throw new InvalidOperationException("CI console standard handle is unavailable: " + kind);
        Check(DuplicateHandle(GetCurrentProcess(), source, GetCurrentProcess(), out copy, 0, true, 2), "Duplicate CI standard handle");
        return copy;
    }
    public static int Run(string executable, string arguments, string directory)
    {
        IntPtr original = IntPtr.Zero, level = IntPtr.Zero, safer = IntPtr.Zero;
        IntPtr primary = IntPtr.Zero, childToken = IntPtr.Zero, job = IntPtr.Zero;
        StartupInfo startup = new StartupInfo();
        ProcessInfo child = new ProcessInfo();
        try
        {
            Check(OpenProcessToken(GetCurrentProcess(), TokenQuery | TokenDuplicate, out original), "Open caller primary token");
            Check(SaferCreateLevel(2, 0x20000, 1, out level, IntPtr.Zero), "Create SAFER normal-user level");
            Check(SaferComputeTokenFromLevel(level, original, out safer, 0, IntPtr.Zero), "Compute SAFER restricted token");
            if (safer == IntPtr.Zero) throw new InvalidOperationException("SAFER returned no restricted token.");
            Check(DuplicateTokenEx(safer, PrimaryAccess, IntPtr.Zero, 2, 1, out primary), "Duplicate restricted primary token");
            LowerToMedium(primary);
            VerifyStandardToken(primary);

            job = CreateJobObjectW(IntPtr.Zero, null);
            Check(job != IntPtr.Zero, "Create isolated CI process job");
            ExtendedJobLimits limits = new ExtendedJobLimits();
            limits.Basic.LimitFlags = 0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            Check(SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(typeof(ExtendedJobLimits))), "Set CI job cleanup policy");
            startup.cb = (uint)Marshal.SizeOf(typeof(StartupInfo));
            startup.dwFlags = StartfUseStdHandles;
            startup.hStdInput = NullInput(); // No keyboard/console input is read.
            startup.hStdOutput = InheritStandardHandle(-11);
            startup.hStdError = InheritStandardHandle(-12);
            StringBuilder command = new StringBuilder("\"" + executable + "\" " + arguments);
            Check(CreateProcessAsUserW(primary, executable, command, IntPtr.Zero, IntPtr.Zero,
                true, CreateSuspended, IntPtr.Zero, directory, ref startup, out child), "Create restricted smoke process");
            Check(AssignProcessToJobObject(job, child.Process), "Assign restricted smoke process to cleanup job");
            Check(OpenProcessToken(child.Process, TokenQuery | TokenDuplicate, out childToken), "Inspect suspended child token");
            VerifyStandardToken(childToken);
            Console.WriteLine("CI smoke pid=" + child.ProcessId + ": non-admin, non-elevated, medium integrity verified. Hardware NOT TESTED.");
            if (ResumeThread(child.Thread) == UInt32.MaxValue) Check(false, "Resume restricted smoke process");
            uint wait = WaitForSingleObject(child.Process, 60000);
            if (wait == WaitTimeout)
            {
                Check(TerminateJobObject(job, 124), "Terminate timed-out CI process tree");
                if (WaitForSingleObject(child.Process, 2000) != WaitObject0)
                    throw new TimeoutException("CI smoke timed out; child termination was not confirmed.");
                throw new TimeoutException("CI smoke exceeded 60 seconds; its process tree was stopped.");
            }
            if (wait != WaitObject0) Check(false, "Wait for restricted smoke process");
            uint exitCode;
            Check(GetExitCodeProcess(child.Process, out exitCode), "Read actual smoke process exit code");
            return unchecked((int)exitCode);
        }
        finally
        {
            // This also covers failures before the suspended child joins the job.
            if (child.Process != IntPtr.Zero && WaitForSingleObject(child.Process, 0) != WaitObject0)
            {
                if (!TerminateProcess(child.Process, 1))
                    Console.Error.WriteLine("CI child cleanup termination failed; code=" + Marshal.GetLastWin32Error());
                if (WaitForSingleObject(child.Process, 2000) != WaitObject0)
                    Console.Error.WriteLine("CI child cleanup could not confirm process exit.");
            }
            Close(ref job); // All descendants belong to this job; never kills other AHK instances.
            Close(ref child.Thread); Close(ref child.Process); Close(ref childToken);
            Close(ref startup.hStdInput); Close(ref startup.hStdOutput); Close(ref startup.hStdError);
            Close(ref primary); Close(ref safer); Close(ref original);
            if (level != IntPtr.Zero) SaferCloseLevel(level);
        }
    }
}
'@
    $WindowsPowerShell = Join-Path ([Environment]::SystemDirectory) 'WindowsPowerShell\v1.0\powershell.exe'
    if (-not (Test-Path -LiteralPath $WindowsPowerShell -PathType Leaf)) {
        throw 'System Windows PowerShell is unavailable.'
    }
    # File-system paths cannot contain a quote on Windows. No shell expansion,
    # execution-policy override, alternate account or elevation verb is involved.
    $ChildArguments = '-NoLogo -NoProfile -NonInteractive -File "' + $SmokeScript +
        '" -AutoHotkeyPath "' + $AutoHotkeyPath + '" -RegistrationTest'
    # The raw CreateProcessAsUserW child inherits this pwsh environment, whose
    # PSModulePath puts PowerShell 7 modules first. Windows PowerShell would then
    # fail to autoload Microsoft.PowerShell.Management/Utility. Without the
    # variable it rebuilds its own default path at startup:
    # https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_psmodulepath
    [Environment]::SetEnvironmentVariable('PSModulePath', $null, 'Process')
    if ($null -ne [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')) {
        throw 'Could not clear the inherited PowerShell 7 module path for the Windows PowerShell child.'
    }
    $ExitCode = [MacFlowCiRestrictedRunner]::Run($WindowsPowerShell, $ChildArguments, $ProjectRoot)
    exit $ExitCode
}
catch {
    [Console]::Error.WriteLine('CI smoke launcher failed: ' + $_.Exception.Message)
    [Console]::Error.WriteLine('No elevated fallback was attempted. Windows hardware remains NOT TESTED.')
    exit 1
}
