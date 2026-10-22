# MacFlow — 开发预览

用 AutoHotkey v2 尝试在 Windows 上保留 Magic Keyboard 的部分 macOS 快捷键。**当前为 DEVELOPMENT PREVIEW，尚未通过 AHK 原型或 v1.0 验收。** 开发主机为 macOS，Windows 语法、运行及真机结果均未确认。

代码包含普通编辑、Option 单词导航、应用切换、Chrome 和部分 Explorer 动作，以及手动配置的 VS Code 桥接。仅允许前台精确 US English 布局 HKL 04090409；中文 IME 等其他布局整窗透传。启用后影响全部键盘，不能仅选 Magic Keyboard。

明确关闭：Windows Terminal 整个宿主、⌘L、Explorer ⌘Backspace。物理左⌘L 仍可能锁屏，地址栏使用原生 Ctrl+L。Windows Terminal 的无选区复制适配受阻，因此当前不能通过完整原型验收。

## Windows 启动

使用完整项目目录。需要已安装的 **64 位 AutoHotkey v2.0.19+**；不以管理员运行。构建配置需要 Python 3，运行已生成配置不需要 Python。工具不会安装依赖、驱动或自启。

在项目根目录的普通 PowerShell 中执行：

~~~powershell
py -3 tools\validate-config.py
py -3 tools\generate-config.py
py -3 tools\generate-config.py --check
py -3 -m unittest discover -s tests -p "test_*.py"
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -SelfTest
& $ahk .\src\ahk\main.ahk
~~~

根据实际位置修改 $ahk；任一检查失败先停止。无需管理员权限或执行策略绕过。smoke 只检验语法/Native 初始化，**不替代按键验收**。

首次启动为 **Native Mode**。鼠标查看托盘 **Status...**，释放全部修饰键后选择 **Enable mappings**。配置错误时不应启用。白名单不识别浏览器内部游戏、远程网页或密码输入场景；不确定时手动 Native。

VS Code 每次启动默认不映射。先阅读[集成说明](integrations/vscode/README.md)，备份并合并快捷键/设置、检查专用组合冲突；再选择 **Confirm VS Code setup for this run...**，最后手动 Enable。不要覆盖已有配置或在未安装桥接时确认。

## 停用与恢复

鼠标选择托盘 **Native Mode (disable mappings)** 或 **Quit MacFlow**。Ctrl+Alt+F12 是补充停用入口。无响应时在任务管理器按 PID、路径和命令行仅结束本次 MacFlow 进程，不结束其他 AHK 脚本。必要时使用独立原生设备/鼠标重启。

检查 Ctrl+C、Win+E/L、Alt+Tab。无法恢复或卡键时停止试用，按[恢复说明](docs/rollback.md)处理并记 FAIL。VS Code 持久配置仅响应专用组合；卸载按集成说明只撤销自身增量，保留个人后续修改。默认没有自启、驱动或注册表映射。

## 配置与验收

config/*.yaml 是严格 JSON 子集，修改后重新校验生成；不要手改 build/generated/。SHA256 仅检查损坏/陈旧，不是安全签名。

- [验收步骤](tests/manual-checklist.md)和[规则对应](tests/mapping-spec.yaml)
- [兼容性矩阵](docs/compatibility-matrix.md)和[测试报告](docs/test-report.md)
- [接口契约](docs/contracts.md)和[协作规则](AGENTS.md)

py -3 tools\validate-config.py --gate prototype 或 --gate v1 在必需结果未全部 PASS 时返回非零。普通配置检查成功仅表示配置有效；工具不会自动提升交付状态或生成硬件 PASS。单元测试的模拟 PASS 仅验证判定逻辑。真机证据必须含设备、环境、commit、操作者和实际结果。
