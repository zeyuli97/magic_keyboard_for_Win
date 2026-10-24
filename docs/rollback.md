# 停用、退出与恢复

状态：**IMPLEMENTED / NOT TESTED on Windows + Magic Keyboard**。当前只有 AHK 单进程，无 Kanata、控制器、驱动或服务。开机启动默认关闭，只有用户在托盘开启后，当前用户的“启动”文件夹里才会有一个 `MacFlow.lnk`。托盘停用覆盖当前全部运行映射；手动合入的 VS Code 配置需要按下文恢复。

1. 用鼠标打开 MacFlow 托盘，选择 **Native Mode (disable mappings)**。路由先关闭，再释放内部跟踪的合成按键；不盲目发送物理 Ctrl、Shift、Win 的 key-up。
2. 如需彻底退出，选择 **Quit MacFlow**。正常退出再次尝试释放合成按键，停止定时器并注销会话通知。Quit 不会取消开机启动：如果开过，先在托盘取消，或删除 `shell:startup` 里的 `MacFlow.lnk`。回退到没有这个选项的旧版本之前，也要先这样做，否则旧版本仍会在登录时启动。
3. 键盘应急选项是 **Ctrl+Alt+F12**，只会停用，不会启用；组合键本身仍透传原应用。Hook 无响应时，此路径不保证可用，优先鼠标托盘。
4. 如果 AHK 无响应，用鼠标打开任务管理器，核对命令行是本项目 `src\ahk\main.ahk`，只结束对应 AHK 进程，不批量结束其他自动化脚本。
5. 强制结束不会运行正常退出回调。若修饰状态异常，先松开所有物理修饰键，再按下并松开相应的 Alt/Command/Control/Shift；必要时断开重连键盘。仍异常时使用 Windows 的正常注销/重启恢复。以上强杀与断连恢复仍需真机验证。

运行中挂起、唤醒、会话切换、锁定/解锁会停用映射，返回 Native Mode，要求手动再次启用。运行错误也会关闭路由并尝试释放合成键；错误保留在状态界面，修正后重启。无法注册会话通知时保持 Native，不允许启用。启动时已按住的修饰键以及启用前按住的修饰键都应拒绝启用，但这一行为尚待真机测试。

`Command+Tab` 的合成 Alt 由输入状态机负责，在左 Command 松开、Esc、超时、失去安全上下文、停用或正常退出时释放。单纯结束进程不等于已验证无卡键；崩溃、强杀、切换窗口中的松键、蓝牙断连和睡眠边界必须分别记录证据。不要通过模拟按键、修改注册表或安装驱动“修复”未确认的问题。

## 恢复手动 VS Code 集成

先停用/退出 MacFlow，再按 `integrations/vscode/README.md` 恢复合入前备份的 `keybindings.json` 和相关 settings；如果之后另有个人修改，只移除 MacFlow 专用条目并恢复该次修改过的设置。不要用旧备份覆盖未保存的新配置。运行时不自动写入或恢复这些文件。检查普通 Ctrl+C/D/Z、编辑器快捷键与终端行为恢复到用户原来的配置。

原型不改键盘/安全注册表、不安装驱动，默认也不开机启动，因此不提供 registry 导入、提权或驱动卸载步骤。如果在托盘开过开机启动：卸载前在托盘取消，或按 Win+R 输入 `shell:startup`，删除其中的 `MacFlow.lnk`。若用户原来已有其他映射软件，单独按其官方方法处理，不由 MacFlow 自动关闭或卸载。

## 必须手工验收的恢复情景

| 情景 | 期望 | 当前状态 |
| --- | --- | --- |
| 普通托盘停用 / 退出 | 路由立即关闭，仅释放自有合成键 | NOT TESTED |
| 按住 Command/Option/Shift 时停用 | 无后续映射，松键后无残留 | NOT TESTED |
| Command+Tab 期间停用 / Esc / 超时 | 无孤立合成 Alt | NOT TESTED |
| 映射中切到未知 / 高权限 / 其他布局窗口 | 旁路并清理自有状态 | NOT TESTED |
| 锁定、切换会话、睡眠唤醒 | Native Mode，手动重新启用 | NOT TESTED |
| 蓝牙断连重连 / USB 拔插 | 无卡键，行为可恢复 | NOT TESTED |
| AHK 强杀 / 崩溃 | 验证残留与人工恢复；没有退出回调保证 | NOT TESTED |
| VS Code 配置恢复 | 保留非 MacFlow 用户设置 | NOT TESTED |

依据：[AHK OnExit](https://www.autohotkey.com/docs/v2/lib/OnExit.htm) 说明强制结束不调用退出处理；[Windows session notifications](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsregistersessionnotification) 与 [power broadcasts](https://learn.microsoft.com/en-us/windows/win32/power/wm-powerbroadcast-messages) 用于正常会话/电源事件处理，不构成崩溃恢复保证。
