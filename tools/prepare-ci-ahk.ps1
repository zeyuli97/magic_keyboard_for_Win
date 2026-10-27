[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or [Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'This downloader is only for Windows GitHub Actions test setup, never the MacFlow runtime.'
}
if (-not $env:RUNNER_TEMP -or -not $env:GITHUB_OUTPUT) {
    throw 'Required GitHub Actions temporary/output paths are missing.'
}

# Pin the minimum supported AHK release for a reproducible compatibility check.
# Hashes were computed from this official release asset, not a third-party mirror.
# No installer is run. The ordinary, non-UIAccess 64-bit executable is extracted.
$Url = 'https://github.com/AutoHotkey/AutoHotkey/releases/download/v2.0.19/AutoHotkey_2.0.19.zip'
$ArchiveSha256 = '4e0d0e65655066a646a210951320feaef0729a3597177131adaec4066bef5869'
$RuntimeSha256 = '3880f9ec464dfe78c16bbd8b9f30560227154c292280337346a30c8fd92871fe'
$TaskDirectory = Join-Path $env:RUNNER_TEMP ('macflow-ahk-' + [Guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $TaskDirectory)
$ArchivePath = Join-Path $TaskDirectory 'AutoHotkey_2.0.19.zip'
$RuntimePath = Join-Path $TaskDirectory 'AutoHotkey64.exe'
Invoke-WebRequest -Uri $Url -OutFile $ArchivePath -TimeoutSec 60
if ((Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ArchiveSha256) {
    throw 'Official AHK archive checksum mismatch; no executable will run.'
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Archive = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $Entry = $Archive.GetEntry('AutoHotkey64.exe')
    if (-not $Entry) { throw 'Pinned archive is missing AutoHotkey64.exe.' }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($Entry, $RuntimePath, $false)
}
finally { $Archive.Dispose() }
if ((Get-FileHash -LiteralPath $RuntimePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $RuntimeSha256) {
    throw 'Extracted AHK runtime checksum mismatch; no executable will run.'
}
# The hosted runner downloads as an administrator, then tests with a filtered
# token. Give that same user explicit read/execute access to this unique test
# directory and its files, without relying on the Administrators group.
# This never changes the runner's parent directories or machine security policy.
$RuntimeAcl = Get-Acl -LiteralPath $TaskDirectory
$RuntimeReader = [Security.Principal.WindowsIdentity]::GetCurrent()
try {
    $ReadExecute = [Security.AccessControl.FileSystemAccessRule]::new(
        $RuntimeReader.User, [Security.AccessControl.FileSystemRights]::ReadAndExecute,
        [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
        [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Allow)
    [void]$RuntimeAcl.AddAccessRule($ReadExecute)
    Set-Acl -LiteralPath $TaskDirectory -AclObject $RuntimeAcl
}
finally { $RuntimeReader.Dispose() }
"path=$RuntimePath" | Out-File -FilePath $env:GITHUB_OUTPUT -Encoding utf8 -Append
Write-Output 'AHK 2.0.19 archive and executable hashes verified. No executable has been run by this setup step.'
