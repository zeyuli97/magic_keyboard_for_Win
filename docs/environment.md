# 环境与验证边界

状态：**DEVELOPMENT PREVIEW**，2026-10-22。实现工作在 macOS 上进行；没有在此环境运行 AHK、PowerShell Windows API 或 Magic Keyboard 测试。不能把 Python 检查等同于 Windows 运行成功。

| 项目 | 原型要求 / 当前状态 |
| --- | --- |
| Windows | Windows 11 x64，普通交互式用户会话；实际版本/build 待真机填写 |
| AHK | AutoHotkey v2.0.19+，64-bit；用户自行安装，版本待填写；AHK v1 不支持 |
| 权限 | 标准用户运行；高权限 AHK 拒绝启动，高权限/无法判定的前台应用旁路 |
| 键盘 | Magic Keyboard 型号、硬件布局、连接方式待填写；USB 和蓝牙分开验收 |
| 作用范围 | 不能识别设备：启用后匹配规则影响所有键盘；device_id=null / origin=unknown |
| 输入布局 | 仅允许前台线程精确 HKL `04090409`；其他布局和中文 IME 整体旁路 |
| 输入法 | 中文 IME 的英文模式也旁路；候选、组合输入、切换兼容性仍为 NOT TESTED |
| 应用 | 仅配置白名单；未知应用旁路；具体应用版本与测试记录待填写 |
| VS Code | 原生绑定手动配置，每次运行在托盘确认；确认不是测试 PASS |
| Windows Terminal | 整个宿主旁路；安全复制语义 BLOCKED，不以 Ctrl+Shift+C 猜测 |
| 后端 | 仅单个 AHK 进程；Kanata、驱动、管理员权限、控制器、自动启动均未启用 |
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

该检查只加载配置并确认初始 Native 状态，然后退出，不安装输入 hook、不注册映射，也不改变已经运行的实例。成功不代表 hook、托盘、焦点判断、输出按键或硬件行为通过。完整 Windows 语法及 smoke 检查见 `tools/smoke-tests.ps1`，真实验收见 `docs/compatibility-matrix.md` 和 `docs/test-report.md`。

真机记录至少填写 Windows build、AHK 精确版本/路径、应用版本、键盘型号/ANSI-ISO-JIS、USB 或蓝牙、前台 HKL、普通/高权限环境、提交与配置 hash。不要收集窗口标题、输入文本、密码、剪贴板内容。原型没有设备身份或注入来源保证；来源未知是保留限制，不是假定物理输入。
