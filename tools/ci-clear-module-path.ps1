# CI setup only; dot-sourced by the launcher and its PowerShell regression test.
# Use the environment provider: in PowerShell 7.5+, the .NET setter converts
# $null to an empty string instead of removing the process environment variable.
# https://learn.microsoft.com/powershell/module/microsoft.powershell.core/about/about_environment_variables#use-the-systemenvironment-methods
$env:PSModulePath = $null
if ($null -ne [Environment]::GetEnvironmentVariable('PSModulePath', 'Process')) {
    throw 'Could not clear the inherited PowerShell 7 module path for the Windows PowerShell child.'
}
