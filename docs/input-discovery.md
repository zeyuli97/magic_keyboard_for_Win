# 修饰键发现与设备边界

状态：**NOT TESTED**。实现不能证明左/右 Command 在任何具体 Magic Keyboard 上的真实映射，不能识别单独设备，也不能可靠识别 Fn。不得直接把普通 Windows 键盘的 VK/SC 表当作 Magic Keyboard 实测结果。

在 Windows 普通 PowerShell 中从仓库根目录运行：

```powershell
.\tools\inspect-keys.ps1 -DurationSeconds 15
```

工具只支持 5–60 秒，默认 15 秒。启动提示后必须输入大小写精确的 `START` 才安装临时观察 hook；其他输入取消。不要修改全局脚本执行策略来运行工具，按本机已有策略使用允许的脚本运行方式。退出 MacFlow 和其他重映射器，再在捕获期间只逐个按下/松开左/右 Command、Option、Control、Shift。不要输入正文、账户信息或密码。

控制台只显示这些修饰键的名称、VK、scan code、down/up、extended 与 injected 标志。普通键会在读取其 scan code 前丢弃；重复 down 不重复打印；全部事件原样交给系统。事件队列有界，不写事件文件，不访问剪贴板、网络或注册表。PowerShell `Add-Type` 编译观察器时，底层运行时可能使用编译缓存/临时文件；其中不含捕获的输入事件。倒计时结束自动卸载 hook。若报卸载错误，关闭该 PowerShell 进程；不得继续假定观察器已正常移除。

该 hook 的 injected 位仅供诊断，不能作为主运行时的可信来源标记。主运行时仍使用 `device_id=null`、`origin=unknown`。工具不能排除其他物理键盘输入：一次只操作待测键盘，并在报告中标明其他连接设备。Fn 没有输出不等于按键失效，也不证明可做软件映射；请标记 UNKNOWN / NOT TESTED。

先记录环境，不预填观察结果：

| 项目 | 待填内容 |
| --- | --- |
| Windows / AHK | 精确版本、build、64-bit、标准用户 |
| Magic Keyboard | 型号、是否 Touch ID、ANSI/ISO/JIS |
| 连接 | USB / Bluetooth；两种方式分别记录 |
| 左/右 Command | 每侧 VK、SC、extended、down/up 是否成对 |
| 左/右 Option | 每侧 VK、SC、extended、是否有 AltGr 差异 |
| Control / Shift | 左右侧（如存在）的 VK、SC、完整 down/up |
| Fn | 工具不可可靠发现，保留 UNKNOWN |
| HKL / IME | US English 与中文 IME 各自记录；输入法切换另测 |
| 重连 / 唤醒 | 是否重新枚举/映射不同；另作行为验收 |

### 2026-10-23 本地部分结果（PARTIAL，非验收）

来源：`tests/evidence/local/2026-10-23-windows-native/` 下的 `usb-command-discovery.json`、`enabled-bypass-diagnosis.json` 与 `usb-fn-globe-probe.json`。用户报告经 USB 连接，型号和 ANSI/ISO/JIS 未记录，其他连接设备未记录。

| 项目 | 观察 | 方法与限制 |
| --- | --- | --- |
| Windows | x64 25H2 build 26200.9711，标准用户 | 本地自检记录 |
| 左 Command | VK 0x5B（LWin），SC 0x05B，extended，down/up 成对 | inspect-keys 截图，无重映射器运行 |
| 右 Command | VK 0x5C（RWin），SC 0x05C，extended，down/up 成对 | 同上 |
| 左 Option | Windows 修饰键状态为 LAlt | 12 秒 GetAsyncKeyState 面板；非扫描码或设备归属证明 |
| 左 Shift | VK 0xA0（LShift），SC 0x02A，down/up 成对，来自 `VID_05AC PID_0320` | 2026-10-23 只读探测的对照键（低层钩子与 Raw Input 一致） |
| Fn/地球键（左下角） | **Windows 收不到任何信号**：低层钩子、Raw Input 键盘、Consumer 页、Apple 厂商页 0xFF00 都没有事件 | 同一次探测，Shift 对照正常；USB 连接。用户态程序（含 MacFlow）无法使用这个键，要识别只能装驱动，项目禁止 |
| 顶排音量加 🔊 | 发送 **F12**（VK 0x7B，SC 0x058），不是音量键 | 同一次探测；fn 加顶排键是否切换成媒体功能未测 |
| 右 Option、Control、右 Shift | 未探测 | 仍为 NOT TESTED / UNKNOWN |
| 输入法 | en-US `0409:00000409` 与微软拼音 zh-Hans-CN | 系统语言列表；未自定义切换热键，按 Windows 默认 Left Alt+Shift |

只将非文本的修饰键观察结果和环境元数据复制到测试报告。发现布局既不是 US English `04090409`，也不是简体中文 `08040804`（本机为微软拼音）时应旁路，不能为了“让测试通过”放宽布局白名单。若左右 Command 与合同假设不符，保持 Native 并向 Lead 提交接口变更建议，不临时更改物理 Ctrl/右 Command 行为。

发现结果仅用于下一步确定映射。它不能验证组合键语义、编辑器/终端焦点、中文候选安全、剪贴板动作、卡键恢复或正式发布门槛。
