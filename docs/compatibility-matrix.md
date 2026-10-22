# 兼容性矩阵

当前为 **DEVELOPMENT PREVIEW**，没有 Windows + Magic Keyboard 真机证据。实现受阻与硬件未测分开记录；release.yaml 的 BLOCKED 不代表已执行硬件测试。

| 环境/功能 | 实现状态 | 硬件状态 | 当前处理 |
| --- | --- | --- | --- |
| Windows、键盘、USB/蓝牙 | 待发现 | NOT TESTED | 不从 macOS 推断 |
| Chrome 编辑/浏览器（除 ⌘L） | 已有代码 | NOT TESTED | 精确 US HKL |
| Notepad / Option 导航 | 已有代码 | NOT TESTED | 中英文本/换行/长按待测 |
| VS Code Editor / Terminal | 人工集成方案 | NOT TESTED | 每次确认前整个 Code.exe 透传；四象限待测 |
| Windows Terminal + PowerShell | BLOCKED | NOT TESTED | 整窗透传；阻止原型验收 |
| Chrome ⌘L | BLOCKED | NOT TESTED | 不注册；仍可能原生锁屏，Ctrl+L 退路 |
| Explorer 剪贴板/新文件夹 | 已有代码 | NOT TESTED | 临时样本实测 |
| Explorer ⌘Backspace | BLOCKED | NOT TESTED | 缺少回收能力判断，关闭 |
| 中文 IME / 非 US 布局 | 整窗 bypass 方案 | NOT TESTED | 输入、候选、切换与键状态待测 |
| 物理 Ctrl / 右 Command | 保留原生方案 | NOT TESTED | 与原生基线对比 |
| Native/Quit/崩溃/睡眠/断连 | 清理路径已有代码 | NOT TESTED | 2 秒恢复是目标，尚无实测结论 |
| RDP/VM/游戏/密码管理器/管理员窗口 | 白名单外透传 | NOT TESTED | 部分进程显式 bypass；不识别浏览器内容 |
| UAC/登录/锁屏安全桌面 | 不提供映射 | NOT TESTED | 返回桌面仍须验收 |
| 多键盘隔离 | BLOCKED | NOT TESTED | 映射影响所有键盘 |
| Kanata / 双引擎 | 未采用 | NOT TESTED | ahk-only；T07c 不适用，不算 PASS |

逐环境记录 Windows build/架构、键盘/连接、其他键盘、HKL/IME、应用/shell/配置、AHK、模式、commit、日期、操作者、步骤、预期/实际、证据及状态。环境或配置改变后重测受影响项。
