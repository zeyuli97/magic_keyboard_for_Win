# MacFlow

简体中文 | [English](README.en.md)

在 Windows 上使用 Magic Keyboard 时，保留熟悉的 macOS 快捷键。MacFlow 基于 AutoHotkey v2，将左 Command（⌘）和左 Option（⌥）的组合键映射为对应的 Windows 操作。

**当前为 DEVELOPMENT PREVIEW（开发预览版）。** 以下快捷键映射已实现，尚未完成完整的 Windows、键盘和输入法兼容性验证；使用前请查看[已知限制](#已知限制)。

物理 Control 和右 Command 保持 Windows 原生行为。启用映射后会影响所有连接的键盘，不能只指定 Magic Keyboard。

## 快捷键

下表中的 ⌘、⌥ 均指左侧按键，⇧ 表示 Shift。映射仅在下方列出的应用中生效。

| 快捷键 | 操作 |
| --- | --- |
| ⌘C / ⌘V / ⌘X / ⌘A | 复制、粘贴、剪切、全选 |
| ⌘Z / ⌘⇧Z | 撤销、重做；重做存在已知输入法问题，见下文 |
| ⌘S / ⌘F | 保存、查找 |
| ⌥← / ⌥→ | 按词移动光标，加 ⇧ 选词 |
| ⌥Backspace | 删除光标前的一个词 |
| ⌘← / ⌘→ | 移到行首、行尾 |
| ⌘↑ / ⌘↓ | 移到文档开头、末尾 |
| ⌥↑ / ⌥↓ | 按段落移动，加 ⇧ 扩展选区；仅适用于 Notepad、Chrome、Claude、Codex |
| ⌘Tab / ⌘⇧Tab | 向前、向后切换应用 |

行首、行尾和单词边界遵循目标应用的 Windows 行为。段落导航发送 Ctrl+↑/↓：⌥↓ 通常进入下一段，与 macOS 停在本段末尾的行为不同。

## 适用应用

| 应用 | 映射范围 |
| --- | --- |
| Notepad（记事本） | 常用编辑、单词和段落导航、应用切换 |
| Chrome | 常用编辑、文本导航、应用切换，以及下列浏览器快捷键 |
| VS Code | 编辑与文本导航、应用切换；需安装[按键桥接配置](integrations/vscode/README.md) |
| Explorer（文件资源管理器） | ⌘C/V/X/A、⌘⇧N 新建文件夹、应用切换 |
| Claude、Codex | 常用编辑、单词和段落导航、应用切换 |
| Visual Studio、Unreal Editor（UE5） | 常用编辑、单词导航、行首/行尾及文档导航、应用切换 |

Chrome 另提供 ⌘T 新建标签页、⌘W 关闭标签页、⌘R 刷新、⌘⇧T 恢复标签页，以及 ⌘[ / ⌘] 后退、前进。

VS Code 和 Visual Studio 的 ⌥↑/↓ 保留原生行为，Explorer 的 ⌥↑ 仍可返回上一级。未列出的应用、其他键盘布局及管理员权限窗口保持原生输入。

## 安装与启动

需要 Windows 和 **64 位 AutoHotkey v2.0.19 或更新版本**。下载完整项目并解压，保留目录结构；运行随项目提供的生成配置不需要 Python。

### 创建桌面快捷方式（无需终端）

1. 将解压后的项目放在准备长期保留的位置，例如 `C:\Tools\MacFlow`。确认其中有 `src\ahk\main.ahk`。
2. 在桌面空白处右键，选择 **新建 → 快捷方式**。
3. 在“请输入对象的位置”中填入 AutoHotkey 程序路径和 MacFlow 脚本路径，例如：

   ```text
   "C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe" "C:\Tools\MacFlow\src\ahk\main.ahk"
   ```

   将两条路径替换为电脑上的实际位置，保留两组双引号。使用便携版 AutoHotkey 时，第一条路径指向其 `AutoHotkey64.exe`。

4. 点击 **下一步**，将快捷方式命名为 **MacFlow**，再点击 **完成**。
5. 右键新建的快捷方式，打开 **属性 → 快捷方式**，将“起始位置”设为项目根目录，例如 `C:\Tools\MacFlow`。在 **高级** 中保持“用管理员身份运行”未勾选，保存设置。

以后**双击桌面的 MacFlow 图标即可启动，不需要打开 PowerShell 或 Windows Terminal**。启动后可在系统托盘找到 MacFlow；若图标隐藏，点击任务栏右下角的展开箭头查看。

快捷方式依赖原来的项目和 AutoHotkey 路径。移动项目或更换 AutoHotkey 位置后，需要更新快捷方式的“目标”和“起始位置”，或重新创建快捷方式。

### 启用映射

1. MacFlow 每次启动时处于 **Native Mode**，键盘保持原生行为。
2. 用鼠标打开托盘 **Status...**，确认 `Error: none`。如需使用 VS Code，先完成下方的桥接配置和本次运行确认。
3. 松开所有修饰键，再从托盘选择 **Enable mappings**。

不要以管理员身份运行。MacFlow 不安装驱动、不修改键盘注册表；运行时不联网，也不记录输入或剪贴板内容。

更新文件或修改配置后，需要从托盘 **Quit MacFlow**，再重新启动，才能加载新版本。

### 通过 PowerShell 启动（可选）

也可以在项目目录打开普通 PowerShell，按 AutoHotkey 的实际安装位置调整路径并运行：

```powershell
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
& $ahk .\src\ahk\main.ahk
```

### VS Code 配置

按[集成说明](integrations/vscode/README.md)备份并合并快捷键和设置。每次启动 MacFlow 后，先在托盘选择 **Confirm VS Code setup for this run...**，再选择 **Enable mappings**；确认前，VS Code 保持原生输入。

桥接配置区分编辑器与集成终端：终端有选区时 ⌘C 复制，无选区时不发送 Ctrl+C；⌘V 用于粘贴。请合并配置，不要覆盖已有的个人设置。

### 开机启动

默认关闭。在托盘选择 **Start at Windows sign-in (Native Mode)** 可开启，再选一次关闭。登录后仍从 Native Mode 启动，需要手动启用映射。

此选项在当前用户的“启动”文件夹创建 `MacFlow.lnk`。请从准备长期保留的项目副本开启；移动项目后，从新位置启动并重新选择该选项以更新路径。Windows 设置中的“启动应用”开关不会删除此快捷方式，也不会同步托盘勾选状态。

## 已知限制

### 输入法

当前允许美式英语（US English，`04090409`）和简体中文（`08040804`）布局。微软拼音的“中”“英”两种模式都会映射；其他中文输入法的兼容性尚未验证。

- **微软拼音下，⌘⇧Z 已出现意外切换中/英、偶发打开开始菜单的情况，尚未修复。** 可暂用应用原生的重做快捷键。
- MacFlow 不检测拼音组字状态。拼音尚未上屏时使用映射组合，可能提交或取消当前输入；建议先完成选词再使用快捷键。
- 普通文字输入和单独按 Shift 切换中/英不会触发 MacFlow 映射。

### 终端与编辑器面板

**Windows Terminal 整窗不映射。** Claude、Codex、Visual Studio 等应用内的终端面板则与编辑区共用映射，无法按焦点区分：⌘C 会发送 Ctrl+C，可能中断命令；⌘Z、⌘S 也可能触发 shell 的挂起或暂停输出。使用这些面板时，可切回 Native Mode 并使用终端原生快捷键。

Unreal Editor 的视口也会收到映射输出。例如 ⌘→ 发送 End，可能执行视口命令；文本导航映射应在文本输入位置使用。当前识别 UE5 的 `UnrealEditor.exe`。

Codex 的识别进程为 `ChatGPT.exe`，同名的 ChatGPT 桌面应用也会受映射影响。

### 暂未提供的功能

- **⌘L 未映射**，Windows 仍可能将它作为 Win+L 锁屏；地址栏请使用物理 Ctrl+L。
- Explorer 的 ⌘Backspace 删除映射未启用。
- 不能区分同一台电脑上的不同键盘。
- 应用匹配基于进程，不能识别浏览器里的游戏、远程桌面或其他特殊页面；需要原生键盘行为时可手动切换 Native Mode。

## 停用、排查与卸载

托盘选择 **Native Mode (disable mappings)** 可停用映射，**Quit MacFlow** 可退出。紧急停用快捷键为 **Ctrl+Alt+F12**。

映射没有生效时，重新打开 **Status...** 检查模式、错误和 **Last mapped-chord decision**。常见原因包括应用或布局不在允许范围、窗口以管理员运行、VS Code 桥接尚未确认。Status 是打开时的快照；最近一次判定不一定对应刚才的操作，请结合其时间查看。

出现卡键或无法退出时，按[恢复说明](docs/rollback.md)处理；若需使用任务管理器，只结束本次 MacFlow 进程，不要结束其他 AutoHotkey 脚本。

卸载时先退出 MacFlow。若开启了开机启动，先从托盘关闭或删除“启动”文件夹里的 `MacFlow.lnk`，再删除桌面快捷方式和项目副本。VS Code 的配置按[集成说明](integrations/vscode/README.md)撤销 MacFlow 增量，保留个人设置。

## 修改配置与开发

配置位于 `config/`，采用 JSON 兼容的 YAML 子集。可以在 `config/apps.yaml` 中将某个应用的 `enabled` 改为 `false`；从 `allowed_hkls` 移除 `08040804` 可让简体中文布局保持原生输入。修改后需重新生成配置并重启 MacFlow，不要直接编辑 `build/generated/`。

构建和测试需要 Python 3.9+，完整单测还需要 Git。在项目根目录执行：

```powershell
python tools\validate-config.py
python tools\generate-config.py
python tools\generate-config.py --check
python -m unittest discover -s tests -p "test_*.py"
```

如果 `python` 不可用，请换成已安装解释器的实际命令或完整路径。macOS/Linux 可使用 `python3`。

Windows 自检使用已安装的 AutoHotkey，分别检查配置加载与 Native 热键注册，不发送测试按键：

```powershell
$ahk = 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -SelfTest
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath $ahk -RegistrationTest
```

下载的 PowerShell 脚本若被执行策略阻止，可在审阅后使用 `Unblock-File .\tools\smoke-tests.ps1` 解除该文件的下载标记。若当前策略仍禁止执行，可只为该次调用添加 `-ExecutionPolicy Bypass`；无需修改全局执行策略。自检失败或出现 AHK 警告时先处理错误。

从 Git checkout 构建预览包：先将准备打包的文件加入 Git 索引，再执行：

```powershell
python tools\package-preview.py
python tools\package-preview.py --check
```

产物为 `dist/MacFlow-development-preview.zip` 和 `dist/manifest.json`，包含中英文 README，不包含 AutoHotkey。打包仅收录指定目录中的已跟踪、已暂存文件；本地证据和未跟踪文件不进入预览包。`--check` 检查可复现性，不写文件。解压运行预览包不需要 Git。

自动化检查验证配置、生成文件、打包和部分 AHK 初始化路径，**不代表真机兼容性通过**。发布门槛可通过 `tools/validate-config.py --gate prototype` 或 `--gate v1` 查询；配置有效与发布验收通过是两个独立结果。

真机测试记录写入 `tests/evidence/`。不要在正在试用的副本中直接修改 `config/release.yaml`；它参与启动时的配置校验，开发侧更新后须立即重新生成配置。

- [快捷键配置](config/mappings.yaml) · [应用配置](config/apps.yaml)
- [兼容性矩阵](docs/compatibility-matrix.md) · [测试报告](docs/test-report.md)
- [手动测试清单](tests/manual-checklist.md) · [VS Code 集成](integrations/vscode/README.md)
- [开发契约](docs/contracts.md) · [实现决策](docs/decisions.md)
