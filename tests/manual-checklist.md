# Windows 真机验收

硬件初始全部 NOT TESTED。T03、T01b 的 ⌘L、T09 的删除另有实现 BLOCKED；不要启用关闭规则绕过限制。

记录 commit、配置/hash、Windows build、AHK、键盘/连接、布局/IME、应用/shell/配置、日期和真实操作者。先取得 Native 原生基线；准备鼠标、独立原生入口及无敏感信息的临时文本/文件/剪贴板哨兵。每项短按至少 10 次，相关项补长按、焦点切换、额外修饰键；偶发错误也为 FAIL。

PASS 必须全部预期实测符合。BLOCKED 有明确障碍；NOT TESTED 未执行。基线必需项未通过均阻止发布；额外环境标 required=false，不能移出基线掩盖失败。证据写 tests/evidence/，含用例/规则、环境、模式、commit、操作者/日期、步骤、预期/实际、状态与恢复结果，不存真实输入/密码/剪贴板。

每一项开始前，以及每次失败后，都要立即记录两件事：
- 托盘 **Status...** 中的 Mode 和 Last mapped-chord decision；
- 任务栏的输入法指示（ENG，或者拼音的“中”/“英”）。

“Enabled 但没反应”若对应“layout … is not allowed”：如果任务栏显示的是 ENG 或微软拼音（中/英），这两种布局都应映射，记下 Status 里的布局代码并记 FAIL；只有确实切到了其他布局，才属于前提不满足。测试中只在测试机上记录证据，不改 `config/release.yaml`（见 README）。

| ID | 操作与预期 |
| --- | --- |
| T01 P0 | Chrome、Notepad、VS Code Editor 支持上下文逐项测 ⌘C/V/X/A/Z/ShiftZ/S/F。每项 GLOBAL 每个声明应用均需实际结果；无误触系统动作。VS Code 确认前透传。2026-10-23 起还包括 Claude、Codex、Visual Studio、Unreal Editor：在各自的文字输入处（Claude/Codex 输入框、Visual Studio 编辑器、Unreal 的细节面板文本框或蓝图节点改名）逐项测，Unreal 另在关卡视口里对 Actor 测 ⌘C/V/X/A/Z/ShiftZ/S。自带终端面板里无选区 ⌘C 会中断命令、bash 里 ⌘Z/⌘S 会挂起或停住输出，这是已接受的限制：只用无害命令（如 `ping 127.0.0.1 -t`）观察并记录，不判 FAIL 也不算 PASS。 |
| T01b P1 | Chrome ⌘T/W/R/ShiftT/[ / ]；⌘L 关闭，记录 BLOCKED 和 Ctrl+L 退路。未来必须聚焦地址栏且不锁屏，替代键不算 PASS。 |
| T02 P0 | Notepad/VS Code 中英文/软换行/长按；Option 左右/Shift左右/Backspace，⌘左右/上下。选择/删词/定位正确，记录 Home/词边界差异，无卡键。每次 Option 组合后：不得出现 F/E 等菜单访问键提示或菜单获焦；带 Shift 的 Option 组合（先松 Option、先松 Shift 各测一次）后任务栏输入法不得切走。Chrome profile 也启用了这些文本映射，但本用例尚未覆盖 Chrome，门槛会报 UNCOVERED，需 Lead 决定是补测还是关闭。2026-10-23 起在 Claude、Codex、Visual Studio、Unreal Editor 的文字输入处重复本用例；Unreal 关卡视口里 ⌘→ 发送 End（默认把选中物体贴地），⌘↑/↓ 发送 Ctrl+Home/End，只记录视口里实际发生了什么并确认 ⌘Z 能撤销。 |
| T03 P0 | Windows Terminal 目前整窗 bypass，仅记原生退路和 BLOCKED。未来有/无选区 × 空闲/可中断任务：⌘C 有选区复制不中断，无选区不改哨兵、不输入、不中断；物理 Ctrl+C 无选区中断、选区按原生，Ctrl+D/Z 不变，⌘V 不额外 Enter。 |
| T04 P0 | VS Code 安装增量后先不确认，再确认 Enable。Editor 重复 T01/T02，Terminal 重复 T03 四象限，可用 ping 127.0.0.1 -t。切搜索框/命令面板，专用键为 noop，不泄露到 shell；保留多行粘贴确认。 |
| T05 P0 | 启用、Native、退出和结束本次进程后测右⌘E/R/L/V 或独立入口；与原生基线一致，不依赖 MacFlow。右键不可区分时明确替代。 |
| T06 P0 | 中文 IME 组字/候选/提交取消/导航删除/切换，切回 US：无丢字/重复/卡键，回 US 状态正确。微软拼音“中”“英”两种模式都映射：在 Notepad、Chrome、VS Code 的“中”模式下（未组字）逐项重复 T01/T02，结果应与 ENG 相同。组字中（拼音未上屏）⌘V、⌘Z、⌥⌫、⌘←、⌘A 各按 10 次，记录每次拼音的去向（字母上屏、汉字上屏、被取消或保留）以及快捷键是否执行。已上屏文字丢失或被改动且 ⌘Z 不能恢复、重复输入、卡键，都记 FAIL。“拼音被取消或原样上屏”目前只记录，不判 PASS：原规格要求无法判断组字状态时 bypass，这次的设计偏离了规格，需要 Lead 签字接受。⌘⇧Z 和带 Shift 的 Option 组合不得切换中/英或输入语言。其他布局整窗透传（Status 显示 layout not allowed）。 |
| T06b P0 | 基线已有游戏/RDP/VM/密码管理器空白界面/管理员窗口；不明确的浏览器内容先 Native；锁屏/UAC 返回。透传或明确手动保护，无残留；不额外安装/提权/输入秘密。 |
| T07 P0 | 鼠标 Native/Quit、按住 Command/Option/Shift 停用、切焦点松键、按 PID 结束本次进程、重复启动、注销重启。2 秒停止并恢复原生是目标；不遗留 Alt/Win、不杀其他脚本、拒绝重复实例、无默认自启。 |
| T07b P0 | 实际 USB/蓝牙按住修饰键断连重连、睡眠唤醒。无重复/卡键，检查 Ctrl+C、Win+E/L、Alt+Tab；睡眠/会话变化后 Native，手动再启用。未测连接不得声明支持。 |
| T07c 条件 | 当前 ahk-only 不适用。未来逐一结束引擎/监督进程并测按住键场景；当前结果不能转为双引擎 PASS。 |
| T07d P0 | 在 Chrome、Notepad、VS Code、Explorer，以及 2026-10-23 加入的 Claude、Codex、Visual Studio、Unreal Editor 中各发起一次切换（覆盖表把这八个应用都算作已覆盖）：按住⌘连续 Tab、Shift 逆序、松开确认、Esc 取消、切非白名单应用、中途停用；无 Alt/Win 残留，原生输入正常。注意只有 Esc 是原生取消：超时（10 秒）和中途按下物理 Ctrl/右 Win/右 Alt/左 Alt 都会释放合成 Alt，Windows 会确认当前高亮的窗口。切换器打开时另测按 Q、H、方向键，记录是否触发 Win+Alt 组合；不要测 R（Win+Alt+R 是 Game Bar 录屏）。 |
| T08 P0 | 独立副本坏配置/未知规则/过期产物、单实例、权限网络日志、应用增量恢复。错误 Native；无未授权驱动/提权/自启、运行时联网或明文日志，只撤销自身修改。 |
| T09 P1 | Explorer 临时样本复制/粘贴/剪切/全选/新文件夹逐项。删除仍 BLOCKED；未来能回收并还原，未知/网络/可移动位置不永久删除。 |

恢复后检查 Ctrl+C、Win+E/L、Alt+Tab 和中文输入。异常记 FAIL 并停止，按 docs/rollback.md 恢复。不能把重启恢复记成“2 秒恢复通过”。

T07/T07d 追加：切换器保持合成 Alt 时按下物理 Ctrl、右 Alt、右 Win 等额外修饰键，应退出切换并让原生组合透传；在动作触发与鼠标 Disable 同时发生、焦点改变与松键交错时重复验证，不能在 Disabled 后重新合成按住键。

T07 开机启动追加：
- 托盘的 Start at Windows sign-in 默认不勾选，注销或重启后不启动。
- 勾选后注销或重启：自动启动；Status 显示 Native、Error 为 none；手动 Enable 后映射正常。
- 取消勾选后，注销或重启不再启动。
- 从另一份副本运行时，这一项显示为未勾选；选择时先询问是否替换。
- 快捷方式不得设置“以管理员身份运行”。

T07/T07b 追加：在反复触发 ⌘Tab 的同时锁屏/解锁、睡眠/唤醒，覆盖合成 Alt-down 发送中到达的会话/电源消息。返回后必须 Native，Alt 不得残留；该路径有延迟清理实现但未经 Windows 验证。
