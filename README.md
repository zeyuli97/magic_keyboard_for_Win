# MacFlow — 开发预览

用 AutoHotkey v2 尝试在 Windows 上保留 Magic Keyboard 的部分 macOS 快捷键。**当前为 DEVELOPMENT PREVIEW，尚未通过 AHK 原型或 v1.0 验收。** 初始开发在 macOS 上完成；2026-10-23 已在一台 Windows 主机通过 AHK 语法、Native 配置加载和热键注册清理自检。物理按键、应用效果和输入法兼容性仍未验收。

代码包含普通编辑、Option 单词导航、应用切换、Chrome 和部分 Explorer 动作，以及手动配置的 VS Code 桥接。前台窗口中接收按键的焦点控件，布局须为 US English（HKL 04090409）或简体中文（08040804，本机为微软拼音）才映射；拼音的“中”“英”两种模式都映射，其他布局整窗透传。映射只在按住左 ⌘ 或左 ⌥ 时生效，所以打拼音、选词、用 Shift 切中/英都不受影响。拼音还没上屏时按到映射组合，效果等于按了对应的 Windows 快捷键：这几个拼音字母可能原样上屏或被取消，然后执行快捷键。启用后影响全部键盘，不能仅选 Magic Keyboard。

明确关闭：Windows Terminal 整个宿主、⌘L、Explorer ⌘Backspace。物理左⌘L 仍可能锁屏，地址栏使用原生 Ctrl+L。Windows Terminal 的无选区复制适配受阻，因此当前不能通过完整原型验收。

## Windows 启动

使用完整项目目录或解压后的预览包。需要已安装的 **64 位 AutoHotkey v2.0.19+**；不以管理员运行。构建配置需要 Python 3.9+，运行预览包内已生成配置不需要 Python。工具不会安装依赖、驱动或自启。

从源码修改配置后，在项目根目录的普通 PowerShell 中先执行（预览包未修改时可跳过这组 Python 命令）。`py` 启动器不一定存在，`python`/`python3` 也可能只是 Microsoft Store 占位程序；先用 `python --version` 确认，不行就换成实际解释器的完整路径，例如 `C:\ProgramData\anaconda3\python.exe`：

~~~powershell
$py = 'python'   # 或 'py'（Python 启动器），或解释器完整路径
& $py tools\validate-config.py
& $py tools\generate-config.py
& $py tools\generate-config.py --check
& $py -m unittest discover -s tests -p "test_*.py"
~~~

完整单测需要已安装 Git（打包测试会在临时目录建 Git 仓库），但不要求项目目录本身是 Git checkout；解压后的预览包也能跑完整套件。

检查 AHK 后启动：

~~~powershell
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'   # 便携版示例：.\.local\autohotkey\2.0.19\AutoHotkey64.exe
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -SelfTest
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -RegistrationTest
& $ahk .\src\ahk\main.ahk
~~~

根据实际位置修改 $ahk；任一检查失败先停止。无需管理员权限。从网上下载的副本，脚本带“来自 Internet”的标记；在 RemoteSigned 下会被拒绝，Windows 客户端默认的 Restricted 策略则拒绝所有脚本。审阅后可对要运行的脚本执行 `Unblock-File .\tools\smoke-tests.ps1`（不需管理员，也不改策略）；或者只对这一次调用加 `-ExecutionPolicy Bypass`，它只影响该进程。不要修改全局执行策略。-SelfTest 检查配置加载；-RegistrationTest 在 Native 状态注册并清理实际热键路径，不发送输入。两种模式分开调用，都会先检查语法；AHK 报出任何 `#Warn` 警告也判失败。这些都**不替代按键验收**。

首次启动为 **Native Mode**。鼠标查看托盘 **Status...**，释放全部修饰键后选择 **Enable mappings**。配置错误时不应启用。白名单不识别浏览器内部游戏、远程网页或密码输入场景；不确定时手动 Native。

映射“不生效”时先打开 **Status...**，看 **Last mapped-chord decision**：它只在内存里保留最近一次判定的固定原因，例如“keyboard layout … is not allowed”或“VS Code setup not confirmed”，不记录按键、窗口标题或剪贴板。要测映射，前台窗口需处于“英语(美国) - 美式键盘”（ENG）或微软拼音（“中”“英”均可）。如果想让中文输入恢复整窗透传，从 `config/apps.yaml` 的 `allowed_hkls` 删掉 `08040804`，再重新生成配置。

VS Code 每次启动默认不映射。先阅读[集成说明](integrations/vscode/README.md)，备份并合并快捷键/设置、检查专用组合冲突；再选择 **Confirm VS Code setup for this run...**，最后手动 Enable。不要覆盖已有配置或在未安装桥接时确认。

## 停用与恢复

鼠标选择托盘 **Native Mode (disable mappings)** 或 **Quit MacFlow**。Ctrl+Alt+F12 是补充停用入口。无响应时在任务管理器按 PID、路径和命令行仅结束本次 MacFlow 进程，不结束其他 AHK 脚本。必要时使用独立原生设备/鼠标重启。

检查 Ctrl+C、Win+E/L、Alt+Tab。无法恢复或卡键时停止试用，按[恢复说明](docs/rollback.md)处理并记 FAIL。VS Code 持久配置仅响应专用组合；卸载按集成说明只撤销自身增量，保留个人后续修改。默认没有自启、驱动或注册表映射。

## 配置与验收

| 目录 | 内容 |
| --- | --- |
| src/ahk/ | 入口、托盘生命周期、输入状态、应用路由与映射 |
| config/ → build/generated/ | 规则与验收状态 → 确定性运行配置和校验和 |
| integrations/ | VS Code 人工集成及 Windows Terminal 限制 |
| tools/ | 配置校验/生成、Windows 发现/smoke、预览包构建 |
| tests/、docs/ | 静态测试、真机清单、兼容矩阵、原规格与实现决策 |

macOS/Linux 开发检查：python3 -B tools/validate-config.py、python3 -B tools/generate-config.py --check、python3 -B -m unittest discover -s tests -p 'test_*.py'。先将准备发布的文件加入 Git 索引，再运行 python3 -B tools/package-preview.py 生成 dist/MacFlow-development-preview.zip 和 dist/manifest.json；不包含 AHK 运行时。打包仅收集索引中的指定目录/文件和显式列出的 `.github/workflows/static-checks.yml`（预览包内的测试套件要检查它），内容取自已暂存的索引版本；发布文件有未暂存修改时拒绝打包。拒绝符号链接，未跟踪的私人文件不会进入 ZIP。打包需要 Git checkout；解压后的运行包不需要 Git。

python3 -B tools/package-preview.py --check 在内存中重建 ZIP 并核对已提交的 dist/manifest.json，不改写文件。Linux 与 Windows CI 都执行该检查。固定 ZIP 元数据和不压缩存储用于跨平台复现。

Windows CI 另外下载固定 AHK 2.0.19，验证压缩包与 exe 的 SHA256，再通过 CI 专用降权启动器执行语法和 Native 注册检查。AHK 的管理员拒绝条件不变；降权失败就令 CI 失败。该下载仅属于 CI 测试准备，MacFlow 本身不会联网。CI 流程已配置但本次尚未在 Windows 执行；即使 CI 通过，也不能提升真机验收状态。

config/*.yaml 是严格 JSON 子集，修改后重新校验生成；不要手改 build/generated/。SHA256 仅检查损坏/陈旧，不是安全签名。

- [验收步骤](tests/manual-checklist.md)和[规则对应](tests/mapping-spec.yaml)
- [兼容性矩阵](docs/compatibility-matrix.md)和[测试报告](docs/test-report.md)
- [接口契约](docs/contracts.md)和[协作规则](AGENTS.md)

`tools\validate-config.py --gate prototype` 或 `--gate v1` 在以下任一情况下返回非零：
- 必需结果未全部 PASS；
- 某条已启用映射在它生效的应用里没有合格用例覆盖。覆盖关系由 [tests/mapping-spec.yaml](tests/mapping-spec.yaml) 中每个用例的 `rules` 和 `profiles` 给出。按规格第 9 节，原型阶段只依赖 P1 用例的映射必须 PASS 或关闭；没有任何用例覆盖的映射对两个门槛都算阻塞。

普通配置检查成功仅表示配置有效；工具不会自动提升交付状态或生成硬件 PASS。单元测试的模拟 PASS 仅验证判定逻辑。真机证据必须含设备、环境、commit、操作者和实际结果。

真机结果先记到 `tests/evidence/`，不要在测试机上直接改 `config/release.yaml`：运行时会校验它的哈希，改动后在重新生成之前会拒绝启用。只在开发机上集成时更新它，并立即重新生成。
