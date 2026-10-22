<#
.SYNOPSIS
Explicit, bounded, modifier-only Windows key discovery; never remaps input.
.DESCRIPTION
Prints only Shift/Control/Alt/Win modifier identity, VK, scan code, down/up and
injection flags to this console for 5-60 seconds. Ordinary keys are discarded
before their scan code is read. No event-output files, clipboard access, network access or registry changes.
This cannot attribute an event to a particular keyboard or prove Fn identity.
#>
[CmdletBinding()]
param(
    [ValidateRange(5, 60)]
    [int]$DurationSeconds = 15
)

$ErrorActionPreference = 'Stop'
if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
    throw 'inspect-keys.ps1 requires Windows; no discovery was performed.'
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
try {
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Run discovery in a standard, non-administrator PowerShell process.'
    }
} finally {
    $identity.Dispose()
}

Write-Host 'MacFlow DEVELOPMENT PREVIEW - modifier discovery is NOT a hardware PASS.'
Write-Host 'Quit MacFlow/other remappers first. This cannot select a particular keyboard.'
Write-Host 'For this short session, press and release ONLY left/right Command, Option, Control and Shift, one at a time.'
Write-Host 'Only modifier identity, VK, scan code, down/up and injected flag are displayed. No ordinary keys or clipboard are recorded.'
Write-Host "Capture stops automatically after $DurationSeconds seconds. No key event output is saved to a file."
$confirmation = Read-Host 'Type START to install the temporary observer, or anything else to cancel'
if ($confirmation -cne 'START') {
    Write-Host 'Cancelled. No observer was installed.'
    return
}

if (-not ('MacFlowModifierDiscovery' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading;

public static class MacFlowModifierDiscovery
{
    private const int WH_KEYBOARD_LL = 13;
    private const uint PM_REMOVE = 1;
    private static IntPtr hook = IntPtr.Zero;
    private static readonly HookProc callback = Observe;
    private static readonly Queue<string> pending = new Queue<string>();
    private static readonly HashSet<uint> down = new HashSet<uint>();
    private static readonly Dictionary<uint, string> names = new Dictionary<uint, string> {
        { 0x5B, "LWin/left Command" }, { 0x5C, "RWin/right Command" },
        { 0xA0, "LShift" }, { 0xA1, "RShift" },
        { 0xA2, "LControl" }, { 0xA3, "RControl" },
        { 0xA4, "LAlt/left Option" }, { 0xA5, "RAlt/right Option" },
        { 0x10, "Shift (side unknown)" }, { 0x11, "Control (side unknown)" },
        { 0x12, "Alt (side unknown)" }
    };

    [StructLayout(LayoutKind.Sequential)]
    private struct KeyboardData {
        public uint vkCode;
        public uint scanCode;
        public uint flags;
        public uint time;
        public UIntPtr dwExtraInfo;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Point { public int x; public int y; }
    [StructLayout(LayoutKind.Sequential)]
    private struct Message {
        public IntPtr hwnd;
        public uint message;
        public UIntPtr wParam;
        public IntPtr lParam;
        public uint time;
        public Point pt;
        public uint lPrivate;
    }
    private delegate IntPtr HookProc(int code, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll", SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook, HookProc proc, IntPtr module, uint thread);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(IntPtr hookHandle);
    [DllImport("user32.dll")]
    private static extern IntPtr CallNextHookEx(IntPtr hookHandle, int code, IntPtr wParam, IntPtr lParam);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PeekMessage(out Message message, IntPtr hwnd, uint min, uint max, uint remove);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool TranslateMessage(ref Message message);
    [DllImport("user32.dll")]
    private static extern IntPtr DispatchMessage(ref Message message);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string module);

    private static IntPtr Observe(int code, IntPtr wParam, IntPtr lParam) {
        if (code >= 0) {
            // Read only VK first. Never read/store the scan code for ordinary keys.
            uint vk = unchecked((uint)Marshal.ReadInt32(lParam));
            if (names.ContainsKey(vk)) {
                KeyboardData data = (KeyboardData)Marshal.PtrToStructure(lParam, typeof(KeyboardData));
                bool up = (data.flags & 0x80) != 0;
                bool changed = up ? down.Remove(vk) : down.Add(vk);
                if (changed && pending.Count < 128) {
                    pending.Enqueue(String.Format("{0,-23} VK=0x{1:X2} SC=0x{2:X3} {3} extended={4} injected={5}",
                        names[vk], vk, data.scanCode, up ? "up  " : "down",
                        (data.flags & 1) != 0, (data.flags & 0x10) != 0));
                }
            }
        }
        // Always pass every event through; this observer cannot suppress a key.
        return CallNextHookEx(hook, code, wParam, lParam);
    }

    public static void Run(int seconds) {
        if (seconds < 5 || seconds > 60) throw new ArgumentOutOfRangeException("seconds");
        if (hook != IntPtr.Zero) throw new InvalidOperationException("Observer already active.");
        pending.Clear();
        down.Clear();
        hook = SetWindowsHookEx(WH_KEYBOARD_LL, callback, GetModuleHandle(null), 0);
        if (hook == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        try {
            Stopwatch clock = Stopwatch.StartNew();
            bool quit = false;
            while (clock.Elapsed.TotalSeconds < seconds && !quit) {
                Message message;
                while (PeekMessage(out message, IntPtr.Zero, 0, 0, PM_REMOVE)) {
                    if (message.message == 0x0012) { quit = true; break; }
                    TranslateMessage(ref message);
                    DispatchMessage(ref message);
                }
                // Console output is outside the time-sensitive keyboard callback.
                while (pending.Count > 0) Console.WriteLine(pending.Dequeue());
                Thread.Sleep(10);
            }
        } finally {
            bool removed = UnhookWindowsHookEx(hook);
            hook = IntPtr.Zero;
            pending.Clear();
            down.Clear();
            if (!removed) throw new Win32Exception(Marshal.GetLastWin32Error());
        }
    }
}
'@
}

Write-Host 'Observer active now. Release each modifier before pressing the next one.'
try {
    [MacFlowModifierDiscovery]::Run($DurationSeconds)
} finally {
    Write-Host 'Discovery session ended. Close this PowerShell process if an observer error was reported.'
}
Write-Host 'Hardware interpretation remains manual. Fn, USB/Bluetooth identity and reconnect behavior are NOT TESTED.'
