# 兼容性矩阵

当前为 **DEVELOPMENT PREVIEW**，没有任何用例的真机验收证据；2026-10-23 只做了部分冒烟。实现受阻与硬件未测分开记录；release.yaml 的 BLOCKED 不代表已执行硬件测试。

| 环境/功能 | 实现状态 | 硬件状态 | 当前处理 |
| --- | --- | --- | --- |
| Windows、键盘、USB/蓝牙 | Windows 11 25H2 build 26200.9711；USB 下左/右 Command = LWin/RWin，左 Option = LAlt | NOT TESTED | 型号/布局、其他修饰键和蓝牙待记录 |
| Chrome 编辑/浏览器（除 ⌘L） | 已有代码；文本导航无用例覆盖 | NOT TESTED | US 或拼音 HKL；门槛报 UNCOVERED，待 Lead 决定 |
| Notepad / Option 导航 | 候选修复（vkE8 防护）待复测 | NOT TESTED | 2026-10-23 冒烟：⌥← 只出现访问键、光标不动；⌘A/C/V 单次通过 |
| VS Code Editor / Terminal | 人工集成方案 | NOT TESTED | 每次确认前整个 Code.exe 透传；四象限待测 |
| Windows Terminal + PowerShell | BLOCKED | NOT TESTED | 整窗透传；阻止原型验收 |
| Chrome ⌘L | BLOCKED | NOT TESTED | 不注册；仍可能原生锁屏，Ctrl+L 退路 |
| Explorer 剪贴板/新文件夹 | 已有代码 | NOT TESTED | 临时样本实测 |
| Explorer ⌘Backspace | BLOCKED | NOT TESTED | 缺少回收能力判断，关闭 |
| 中文 IME / 其他布局 | 微软拼音（08040804）“中”“英”两种模式都按 US 映射（候选），不读输入法状态、不检测组字；其他布局整窗 bypass | NOT TESTED | 组字中误触、候选、⌘⇧Z 与 Shift 切换、键状态待测；Chrome/VS Code 待测；其他使用 08040804 的中文输入法未测 |
| 物理 Ctrl / 右 Command | 保留原生方案 | NOT TESTED | 与原生基线对比 |
| Native/Quit/崩溃/睡眠/断连 | 清理路径已有代码 | NOT TESTED | 2 秒恢复是目标，尚无实测结论 |
| RDP/VM/游戏/密码管理器/管理员窗口 | 白名单外透传 | NOT TESTED | 部分进程显式 bypass；不识别浏览器内容 |
| UAC/登录/锁屏安全桌面 | 不提供映射 | NOT TESTED | 返回桌面仍须验收 |
| 多键盘隔离 | BLOCKED | NOT TESTED | 映射影响所有键盘 |
| Kanata / 双引擎 | 未采用 | NOT TESTED | ahk-only；T07c 不适用，不算 PASS |

逐环境记录 Windows build/架构、键盘/连接、其他键盘、HKL/IME、应用/shell/配置、AHK、模式、commit、日期、操作者、步骤、预期/实际、证据及状态。环境或配置改变后重测受影响项。
