# 环境与验证边界

状态：**DEVELOPMENT PREVIEW**。初始实现于 2026-10-22 在 macOS 上完成；2026-10-23 在 Windows x64 25H2 build 26200.9711 上完成 AHK 2.0.19 x64 的语法、Native 配置加载与注册清理自检，以及 PowerShell 模块路径行为回归。Magic Keyboard 真机用例仍未验收；Python、AHK 自检与硬件结果分别记录。

| 项目 | 原型要求 / 当前状态 |
| --- | --- |
| Windows | 本地自检：Windows x64 25H2，build 26200.9711；非管理员用户会话 |
| AHK | 本地自检：官方 AutoHotkey 2.0.19，64-bit，ZIP/EXE SHA256 已核对；位于项目 `.local/autohotkey/2.0.19/AutoHotkey64.exe`；AHK v1 不支持 |
| 权限 | 标准用户运行；高权限 AHK 拒绝启动，高权限/无法判定的前台应用旁路 |
| 键盘 | 用户报告 Magic Keyboard 经 USB 连接；型号、硬件布局和修饰键结果待填写；USB 和蓝牙分开验收 |
| 作用范围 | 不能识别设备：启用后匹配规则影响所有键盘；device_id=null / origin=unknown |
| 输入布局 | 以焦点窗口所在线程（真正接收按键的线程）的布局为准；查询成功但没有焦点窗口时，看前台窗口线程；查询本身失败则整体旁路。须为 HKL `04090409`（US English）或 `08040804`（简体中文，本机为微软拼音）；其他布局整体旁路。Windows 11 Notepad 的顶层线程可能停在旧布局，不作为依据 |
| 输入法 | 微软拼音“中”“英”两种模式都映射，不读输入法状态、不检测组字（候选，2026-10-23）；拼音未上屏时按到映射组合，预期与直接按对应的 Windows 快捷键相同（未实测）。这偏离了原规格“无法判断组字状态时 bypass”的要求，待 Lead 确认。组字、候选、切换兼容性仍为 NOT TESTED；其他使用 08040804 的中文输入法未测 |
| 应用 | 仅配置白名单；未知应用旁路；具体应用版本与测试记录待填写 |
| VS Code | 原生绑定手动配置，每次运行在托盘确认；确认不是测试 PASS |
| Windows Terminal | 整个宿主旁路；安全复制语义 BLOCKED，不以 Ctrl+Shift+C 猜测 |
| 后端 | 仅单个 AHK 进程；Kanata、驱动、管理员权限、控制器均未启用；开机启动默认关闭，只能在托盘开启（当前用户“启动”文件夹里的一个快捷方式） |
| 网络与隐私 | 运行时不访问网络、不读写剪贴板、不记录输入内容；AHK 键历史/执行行历史禁用 |

从仓库根目录使用已有的 Python 生成数据，再使用已有的 AHK：

```powershell
python tools/validate-config.py
python tools/generate-config.py
& 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' '.\src\ahk\main.ahk'
```

AHK 路径是示例，以实际安装位置为准。启动后显示 Native Mode；释放全部修饰键后，从鼠标托盘选择 **Enable mappings**。没有命令行自动启用开关。重启总是回到 Native Mode，VS Code 确认不会持久化。相同会话中的第二个普通运行实例会被拒绝，不强制终止已有进程。

可在 Windows 上单独执行不启用映射的初始化检查：

```powershell
& 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' /ErrorStdOut '.\src\ahk\main.ahk' --self-test
```

`--self-test` 只加载配置并确认初始 Native 状态，然后退出，不安装输入 hook、不注册映射，也不改变已经运行的实例。它成功不代表热键注册成功。

另外提供 **Native 注册自检**，验证正常启动使用的同一组 HotIf/Hotkey/应急键注册调用：

```powershell
.\tools\smoke-tests.ps1 -AutoHotkeyPath 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' -RegistrationTest
```

脚本先执行 AHK `/validate`，通过后再启动 `--registration-test`。注册期间 `Enabled=false`、`VscodeReady=false`，所有映射与应急处理条件不成立；不启用映射、不派发动作、不发送按键。该进程隐藏托盘，不建立常驻定时器、会话通知或正常运行互斥锁，不等待输入；完成后停用注册热键、卸载 hook 并立即退出。注册或清理异常返回非零退出码。

`-SelfTest` 和 `-RegistrationTest` 不能同时使用，AHK 的 `--self-test` 与 `--registration-test` 也互斥。每个有效 smoke 模式都先做 `/validate`；可选自检的每个 AHK 子进程限制 15 秒，超时只结束本次检查启动的子进程并报错。两个自检都要求非管理员 64-bit AHK，没有 CI 提权豁免。单独执行 `--registration-test` 时也遵守相同限制，建议使用 smoke 包装器获得超时和诊断捕获。

2026-10-23 本地 `/validate`、配置初始化和注册清理自检已通过。这些结果不能证明物理按键、焦点路由、托盘操作、合成输入、中文输入法或 Magic Keyboard 硬件行为正确；这些仍按 `docs/compatibility-matrix.md` 和 `docs/test-report.md` 分别验收。自检在沙箱外的非管理员进程中执行；AHK 自身的管理员拒绝条件保持生效。

真机记录至少填写 Windows build、AHK 精确版本/路径、应用版本、键盘型号/ANSI-ISO-JIS、USB 或蓝牙、焦点窗口线程的 HKL（Status 的判定原因会显示不被允许的布局）、普通/高权限环境、提交与配置 hash。不要收集窗口标题、输入文本、密码、剪贴板内容。原型没有设备身份或注入来源保证；来源未知是保留限制，不是假定物理输入。
