# 兼容性矩阵

当前为 **DEVELOPMENT PREVIEW**，没有任何用例的真机验收证据；2026-10-23 只做了部分冒烟。实现受阻与硬件未测分开记录；release.yaml 的 BLOCKED 不代表已执行硬件测试。

| 环境/功能 | 实现状态 | 硬件状态 | 当前处理 |
| --- | --- | --- | --- |
| Windows、键盘、USB/蓝牙 | Windows 11 25H2 build 26200.9711；USB 下左/右 Command = LWin/RWin，左 Option = LAlt | NOT TESTED | 型号/布局、其他修饰键和蓝牙待记录 |
| Chrome 编辑/浏览器（除 ⌘L） | 已有代码；文本导航无用例覆盖 | NOT TESTED | US 或拼音 HKL；门槛报 UNCOVERED，待 Lead 决定 |
| Notepad / Option 导航 | 候选修复（vkE8 防护）待复测 | NOT TESTED | 2026-10-23 冒烟：修复前 ⌥← 只出现访问键、光标不动；⌘A/C/V 用户冒烟各成功一次（不是 PASS）；装上 Alt 防护后，用户报告 Option 导航可用（不是完整测试） |
| VS Code Editor / Terminal | 人工集成方案 | NOT TESTED | 每次确认前整个 Code.exe 透传；四象限待测 |
| Cursor Editor / Terminal | 独立桥接与每次运行确认 | NOT TESTED | 仅 Cursor.exe；编辑区原生命令，终端选区复制/无选区 noop/粘贴；聊天及其他非编辑区 noop；不共用 VS Code 确认 |
| Discord / Teams / WhatsApp / GitHub Desktop | basic_edit/text 与应用切换 | NOT TESTED | 固定 Discord.exe、ms-teams.exe、WhatsApp.Root.exe、GitHubDesktop.exe；不映射保存/段落导航，不增加发送/提交/推送；T01/T02/T07d |
| ⌥↑/↓ 段落跳转 | 2026-10-24 应用户要求加入：Notepad、Chrome、Claude、Codex 发送 Ctrl+↑/↓（加 ⇧ 选中） | NOT TESTED | 映射前 Notepad 里 ⌥↑/↓ 不动光标，⌥↑ 还会让光标消失（用户报告）；VS Code、Visual Studio 保持原生的移动行，Explorer 保持回上一级，Unreal 不映射；Chrome 未被 T02 覆盖（门槛报 UNCOVERED） |
| Claude / Codex / Visual Studio / Unreal Editor | 2026-10-23 应用户要求加入，与 Notepad 相同（edit/text） | NOT TESTED | 进程分别为 claude.exe、ChatGPT.exe、devenv.exe、UnrealEditor.exe；自带终端面板同样收到 Ctrl 输出（无选区 ⌘C 会中断命令）；Unreal 视口里 Home/End 是视口命令；超出规格首批范围，待 Lead 确认 |
| Windows Terminal + PowerShell | BLOCKED | NOT TESTED | 整窗透传；阻止原型验收 |
| Edge | edit/text/paragraph/browser 与应用切换 | NOT TESTED | 仅 msedge.exe，不包含共享 WebView2；T01/T01b/T02/T07d 覆盖；⌘L 仍关闭 |
| 微信 | edit/text 与应用切换 | NOT TESTED | 本机 WeChat.exe 3.9.12.1000；只在无敏感内容的未发送输入区测试，保存/重做等以原生命令为准；不包括企业微信和其他进程名 |
| Word / Excel / PowerPoint / OneNote | edit/text 与应用切换；Word/OneNote 另有 paragraph | NOT TESTED | Windows 桌面版各自固定进程；Excel 单元格编辑与表格导航、PowerPoint 文本与对象/幻灯片分开测；T01/T02/T07d |
| 经典版 Outlook | edit/text 与应用切换；⌘F 发送 F4 在打开的邮件内查找 | NOT TESTED | 仅 outlook.exe；主窗口邮箱搜索使用原生 Ctrl+E；不把正文 Ctrl+E 居中当作查找；测试草稿不发送 |
| 新版 Outlook（Windows） | edit/text 映射与应用切换；⌘F 单独发送 Ctrl+E 搜索邮件 | NOT TESTED | 仅 olk.exe；写信文字区与原生快捷键对照，邮件列表等区域使用 Outlook 的原生语义；⌘S 发送 Ctrl+S，不能用自动保存证明映射成功；⌥↑/↓ 未映射；经典 Outlook、旧 Mail、共享 WebView2 进程未加入 |
| Chrome ⌘L | BLOCKED | NOT TESTED | 不注册；仍可能原生锁屏，Ctrl+L 退路 |
| Explorer 剪贴板/新文件夹 | 已有代码 | NOT TESTED | 临时样本实测 |
| Explorer ⌘Backspace | BLOCKED | NOT TESTED | 缺少回收能力判断，关闭 |
| 中文 IME / 其他布局 | 微软拼音（08040804）“中”“英”两种模式都按 US 映射（候选），不读输入法状态、不检测组字；其他布局整窗 bypass | NOT TESTED | 组字中误触、候选、⌘⇧Z 与 Shift 切换、键状态待测；Chrome/VS Code 待测；其他使用 08040804 的中文输入法未测。组字期间仍映射，偏离原规格的 bypass 要求，待 Lead 确认 |
| 物理 Ctrl / 右 Command | 保留原生方案 | NOT TESTED | 与原生基线对比 |
| Native/Quit/崩溃/睡眠/断连 | 清理路径已有代码 | NOT TESTED | 2 秒恢复是目标，尚无实测结论 |
| 开机启动（可选） | 托盘开启后在当前用户“启动”文件夹建快捷方式；默认关闭 | NOT TESTED | 登录后应为 Native；文件夹移动后在托盘重选一次 |
| RDP/VM/游戏/密码管理器/管理员窗口 | 白名单外透传 | NOT TESTED | 部分进程显式 bypass；不识别浏览器内容 |
| UAC/登录/锁屏安全桌面 | 不提供映射 | NOT TESTED | 返回桌面仍须验收 |
| 多键盘隔离 | BLOCKED | NOT TESTED | 映射影响所有键盘 |
| Kanata / 双引擎 | 未采用 | NOT TESTED | ahk-only；T07c 不适用，不算 PASS |

逐环境记录 Windows build/架构、键盘/连接、其他键盘、HKL/IME、应用/shell/配置、AHK、模式、commit、日期、操作者、步骤、预期/实际、证据及状态。环境或配置改变后重测受影响项。
