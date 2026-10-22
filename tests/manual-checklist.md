# Windows 真机验收

硬件初始全部 NOT TESTED。T03、T01b 的 ⌘L、T09 的删除另有实现 BLOCKED；不要启用关闭规则绕过限制。

记录 commit、配置/hash、Windows build、AHK、键盘/连接、布局/IME、应用/shell/配置、日期和真实操作者。先取得 Native 原生基线；准备鼠标、独立原生入口及无敏感信息的临时文本/文件/剪贴板哨兵。每项短按至少 10 次，相关项补长按、焦点切换、额外修饰键；偶发错误也为 FAIL。

PASS 必须全部预期实测符合。BLOCKED 有明确障碍；NOT TESTED 未执行。基线必需项未通过均阻止发布；额外环境标 required=false，不能移出基线掩盖失败。证据写 tests/evidence/，含用例/规则、环境、模式、commit、操作者/日期、步骤、预期/实际、状态与恢复结果，不存真实输入/密码/剪贴板。

| ID | 操作与预期 |
| --- | --- |
| T01 P0 | Chrome、Notepad、VS Code Editor 支持上下文逐项测 ⌘C/V/X/A/Z/ShiftZ/S/F。每项 GLOBAL 每个声明应用均需实际结果；无误触系统动作。VS Code 确认前透传。 |
| T01b P1 | Chrome ⌘T/W/R/ShiftT/[ / ]；⌘L 关闭，记录 BLOCKED 和 Ctrl+L 退路。未来必须聚焦地址栏且不锁屏，替代键不算 PASS。 |
| T02 P0 | Notepad/VS Code 中英文/软换行/长按；Option 左右/Shift左右/Backspace，⌘左右/上下。选择/删词/定位正确，记录 Home/词边界差异，无卡键。 |
| T03 P0 | Windows Terminal 目前整窗 bypass，仅记原生退路和 BLOCKED。未来有/无选区 × 空闲/可中断任务：⌘C 有选区复制不中断，无选区不改哨兵、不输入、不中断；物理 Ctrl+C 无选区中断、选区按原生，Ctrl+D/Z 不变，⌘V 不额外 Enter。 |
| T04 P0 | VS Code 安装增量后先不确认，再确认 Enable。Editor 重复 T01/T02，Terminal 重复 T03 四象限，可用 ping 127.0.0.1 -t。切搜索框/命令面板，专用键为 noop，不泄露到 shell；保留多行粘贴确认。 |
| T05 P0 | 启用、Native、退出和结束本次进程后测右⌘E/R/L/V 或独立入口；与原生基线一致，不依赖 MacFlow。右键不可区分时明确替代。 |
| T06 P0 | 中文 IME 组字/候选/提交取消/导航删除/切换，含 IME 英文模式，切回 US。非 US 整窗透传，无丢字/重复/卡键，回 US 状态正确。 |
| T06b P0 | 基线已有游戏/RDP/VM/密码管理器空白界面/管理员窗口；不明确的浏览器内容先 Native；锁屏/UAC 返回。透传或明确手动保护，无残留；不额外安装/提权/输入秘密。 |
| T07 P0 | 鼠标 Native/Quit、按住 Command/Option/Shift 停用、切焦点松键、按 PID 结束本次进程、重复启动、注销重启。2 秒停止并恢复原生是目标；不遗留 Alt/Win、不杀其他脚本、拒绝重复实例、无默认自启。 |
| T07b P0 | 实际 USB/蓝牙按住修饰键断连重连、睡眠唤醒。无重复/卡键，检查 Ctrl+C、Win+E/L、Alt+Tab；睡眠/会话变化后 Native，手动再启用。未测连接不得声明支持。 |
| T07c 条件 | 当前 ahk-only 不适用。未来逐一结束引擎/监督进程并测按住键场景；当前结果不能转为双引擎 PASS。 |
| T07d P0 | 按住⌘连续 Tab、Shift 逆序、松开确认、Esc 取消、切非白名单应用、中途停用；无 Alt/Win 残留，原生输入正常。 |
| T08 P0 | 独立副本坏配置/未知规则/过期产物、单实例、权限网络日志、应用增量恢复。错误 Native；无未授权驱动/提权/自启、运行时联网或明文日志，只撤销自身修改。 |
| T09 P1 | Explorer 临时样本复制/粘贴/剪切/全选/新文件夹逐项。删除仍 BLOCKED；未来能回收并还原，未知/网络/可移动位置不永久删除。 |

恢复后检查 Ctrl+C、Win+E/L、Alt+Tab 和中文输入。异常记 FAIL 并停止，按 docs/rollback.md 恢复。不能把重启恢复记成“2 秒恢复通过”。

T07/T07d 追加：切换器保持合成 Alt 时按下物理 Ctrl、右 Alt、右 Win 等额外修饰键，应退出切换并让原生组合透传；在动作触发与鼠标 Disable 同时发生、焦点改变与松键交错时重复验证，不能在 Disabled 后重新合成按住键。
