# Source specification snapshot

Source: https://docs.google.com/document/d/1GlBcn8PpgCiUHCXzl3kUaBjWpS909ThDqEknYTjjow4

Captured 2026-10-22; source revision: `AHj4eMSWbgAdKSTmXNFPWDxj_iPGvEES02Q-O8TRur_5u__yHAFC-bCclVfIZ2x1J5LpGmrrRZ-Bvg07DEYMflDfdq46ggoU5f1qY8gIkCk`.

This is the pre-implementation specification, not the current implementation status. See README.md, decisions.md and test-report.md for actual results.

# MacFlow v1.0 — Windows Magic Keyboard 适配执行手册

2026-10-22 · 执行规范修订版 · 当前状态：SPECIFICATION / NOT IMPLEMENTED

## 0. 项目目标与不可妥协规则

目标：在 Windows PC 上使用 Apple Magic Keyboard，尽可能保留 macOS 肌肉记忆：左 Command 执行常用操作，左 Option 用于单词导航，物理 Control 保留终端原生行为。重要 Windows 功能必须保留独立备用入口。候选平台为 Windows 11/10 用户桌面会话；实际支持范围只限兼容性矩阵中实测的版本、设备、连接方式及应用组合，不承诺登录界面或 UAC 安全桌面映射。

安全规则：可通过鼠标停用整套映射并恢复原生输入；不更改 Scancode Map 或系统锁屏安全策略；不自动安装驱动、不偷偷提权、不默认开机自启；不记录输入字符、密码或剪贴板明文；运行时不主动联网；严禁把静态检查、模拟测试或文档修订报告为硬件验证。安装驱动、提权、开机自启均须另有用户明确授权。

## 1. 技术路线与先决条件

### 1.1 分阶段路线与环境基线

Phase A：先实现无驱动的 AutoHotkey v2 原型，在明确的应用白名单中验证映射、终端行为和退出恢复。原型与 v1.0 使用第 9 节不同的验收门槛；原型通过不等于完整 v1.0 发布。

Phase B：Kanata 仅为候选增强方案，在独立实验分支验证后决定是否采用；不预先锁定双引擎架构。必须记录准确版本、二进制变体、输入后端、权限要求和事件路径。Windows hook 后端与 Interception 驱动后端分别评估，不能把“使用 Kanata”当作已绕过 Win+L 或已支持设备隔离的证据。

两引擎协作须先确定单一输入入口及事件传递协议，再验证注入事件是否会重复处理、hook 顺序、连续按键及故障恢复。可评估官方 AHK passthrough 集成方式，但不得把示例存在当作本机兼容性证明。只有全部双引擎专属测试通过后才允许作为交付模式。

环境基线：记录 Windows 版本/build/架构、Magic Keyboard 型号、USB/蓝牙、左右修饰键 VK/scan code、其他键盘、布局、中文 IME、AHK/Kanata 版本，以及应用版本和自定义快捷键。首个验收基线包含 Chrome、Notepad、VS Code、Windows Terminal + PowerShell、Explorer 和用户实际使用的一种中文 IME；其他终端宿主、WSL/shell、Edge、布局和设备需逐项扩展验证。

无可访问的 Windows + Magic Keyboard 时，可继续编写代码和执行静态检查；所有依赖真机的条目保持 NOT TESTED，不得宣称原型已验收。

### 1.2 输入身份、事件契约与规则优先级

区分两件事：识别左 Command 与物理 Control，是按键身份问题；识别 Magic Keyboard 与另一把键盘，是设备身份问题。Phase A 在转换前保留原始修饰键身份，不把左 Command 全局无条件改成 Ctrl。后端无法可靠提供设备身份时，device_id 为 null，不能声称支持按设备隔离；如需限定 Magic Keyboard，则该模式保持 BLOCKED。

内部事件契约：backend、device_id（可空）、vk/scan_code、edge（down/up）、原始左右修饰键快照、origin（physical/macflow/unknown）。它是实现接口，不是输入日志。具体 API 可提供哪些字段、如何屏蔽自身注入事件、备用键或虚拟层使用何种编码，由 Lead 在实现前写入 docs/contracts.md；未知来源不能被伪称为已识别。

规则优先级：Disabled/Native Mode 与安全 bypass → 应用内焦点规则 → 应用规则 → 明确允许的通用规则 → 原生透传。同一事件只能由一个映射规则消费；同级冲突使配置校验失败。未支持的额外修饰键组合不得意外触发较简单的映射。

焦点无法可靠识别时，不应用依赖焦点的映射。终端窗口不得回落到通用 Ctrl+C、文本导航或编辑映射；必要时整个宿主窗口 bypass。按键按下时记录处理规则及合成输出，松开时由同一规则释放，避免焦点切换后留下按下状态。

### 1.3 配置与应用适配接口

唯一手写配置源为 config/mappings.yaml、apps.yaml、release.yaml，并由 config/schema.json 约束。mappings 至少含 schema_version、id、enabled、physical_chord、context、action、priority、on_unmatched；apps 含进程匹配、焦点策略、bypass 条件和已验证配置；release 固定原型/v1.0 必需规则及支持环境。未声明规则默认关闭，on_unmatched 默认为 passthrough。

Lead 维护 tools/generate-config.py，将配置编译为 build/generated/ 下的 AHK 常量及所选后端配置；src/ahk/config.ahk 只加载校验通过的产物。生成文件禁止手改；发布包包含生成产物，运行时不要求 Python。schema 版本不匹配、冲突或解析失败时保持 Native Mode 并显示原因，不部分启用。

VS Code 的 Editor/Integrated Terminal 区分优先使用原生 keybindings.json 的 editorTextFocus、terminalFocus 等条件；仅匹配 Code.exe 不足以识别焦点。原生规则需覆盖“无选区 ⌘C 无操作”，防止落入 shell。若需专用触发组合键，必须验证冲突并写入公共契约。

Windows Terminal 适配按宿主版本、settings 配置与 shell 组合验收。不能可靠判断选区或保证复制动作不透传时，⌘C 功能保持关闭/BLOCKED；不得用盲发 Ctrl+Shift+C 代替证明。应用配置采用可审查的增量片段，保存变更前备份与变更清单，恢复时仅撤销 MacFlow 自己的更改。原生应用增量规则必须在 Native Mode、Quit 或引擎崩溃后失效，或保持不影响任何已声明支持的原生输入；可采用经验证的激活条件，或本机无冲突且仅由映射流程使用的专用触发。不得持久覆盖原生 Ctrl/Alt 组合键后仅靠退出进程声称恢复。

左 Command 常见为 LWin、Option 常见为 Alt，右 Command 候选为原生 Windows 入口；均须实测。AltGr/右 Option 默认不重映射。若左右键无法区分，使用可见 Native Mode 和经验证的独立输入/鼠标入口。

技术依据：AutoHotkey v2 文档 https://www.autohotkey.com/docs/v2/ ；Kanata Windows 变体及 AHK 集成说明 https://github.com/jtroo/kanata/releases ；Windows Terminal copy/action 行为 https://learn.microsoft.com/en-us/windows/terminal/customize-settings/actions#copy ；VS Code 焦点条件 https://code.visualstudio.com/api/references/when-clause-contexts 。实现时固定具体版本；引用资料不替代本机验证。

## 2. 输入输出映射契约（设计目标，不是已验证结果）

P0 GLOBAL：在支持的普通编辑上下文中，左⌘+C/V/X/A/Z/S/F 对应复制/粘贴/剪切/全选/撤销/保存/搜索；左⌘+Shift+Z 重做，按应用选择 Ctrl+Shift+Z 或 Ctrl+Y。左⌘+Tab / Shift+⌘+Tab 切换应用；按住 Command 连续 Tab、逆序、松开确认与取消均须验证。这里的 GLOBAL 不代表无条件覆盖所有进程。

P0 TEXT：在 Notepad 与 VS Code Editor 支持的文本上下文中，左⌥+Left/Right → Ctrl+Left/Right；左⌥+Shift+Left/Right → Ctrl+Shift+Left/Right；左⌥+Backspace → Ctrl+Backspace；左⌘+Left/Right → Home/End；左⌘+Up/Down → Ctrl+Home/End。记录软换行、智能 Home 和单词边界差异，不宣称所有编辑器都与 macOS 完全相同。终端默认禁用这些转换。

P1 BROWSER（v1.0 必需）：在 Chrome 基线中，左⌘+L/T/W/R/Shift+T 分别执行地址栏、新标签、关闭标签、刷新、恢复标签；左⌘+[ / ] 后退/前进，按实际布局验证。⌘L 在原型允许 BLOCKED，但 v1.0 必须通过；Ctrl+L 备用入口不算 ⌘L 通过。Edge 仅在纳入 release.yaml 支持范围后成为该环境的必测项。

P1 EXPLORER（v1.0 必需）：左⌘+C/V/X/A、左⌘+Shift+N 新文件夹；左⌘+Backspace 仅在可确认会进入回收站的本地测试位置启用，必须验证可还原。不保证回收的网络/可移动位置不执行该删除映射；无法识别时禁用该功能并记 BLOCKED。测试仅使用临时样本。Finder 风格 ⌥+⌘+V 移动为 P2 可选，不得静默覆盖同名文件。

P0 TERMINAL：物理 Ctrl+C/D/Z 保留该宿主、配置和 shell 的原生行为。物理 Ctrl+C 只在“无选区＋可中断前台任务”中要求中断；有选区时与停用 MacFlow 的行为基线比较，不额外承诺必定中断。

左⌘+C：有选区时复制且不中断；无选区时无操作、不改变剪贴板、不向 shell 发送按键或控制序列。左⌘+V 调用已验证的粘贴动作，不额外发送 Enter，并保留终端现有多行粘贴确认。VS Code Editor 与 Integrated Terminal 分别验收。

Windows Terminal 官方 copy 动作在无选区时会把组合键交给终端，且默认 Ctrl+C 也可用于复制。因此不能仅凭映射到 Ctrl+Shift+C 宣称符合上述契约；必须证明具体实现处理了无选区情形。

P0 NATIVE FALLBACK：优先保留右 Command 原生语义，验收右⌘+E/R/L/V；若实际设备不支持可区分的右 Command，须提供已验证的替代入口。必须至少有一种鼠标恢复路径和一种不依赖 MacFlow 运行的 Windows 原生操作路径。Native Mode 必须停止全部映射层，不仅关闭 AHK 热键。

P0 中文 IME 兼容：基线 IME 的组字、候选翻页/选择、提交、取消及输入法切换不得受损，不得出现重复输入、字符丢失或卡住的修饰键。此项保证原生输入安全，不要求所有映射在组字期间生效；无法可靠处理组字状态时 bypass 相关映射，无法识别时对相应应用/模式整体 bypass，并验证此退路有效。

P0 边界保护：游戏、Remote Desktop、VM、密码管理器和不支持的管理员窗口默认不启用映射。对声明支持的识别/bypass 路径须实测；无法自动识别时明确要求先进入 Native Mode，不能声称自动保护。UAC/登录/锁屏界面的映射不在支持范围，但返回桌面后不得遗留修饰键状态。

P2 扩展：其他 IME、布局、shell、AltGr 特殊组合、多设备隔离、游戏/RDP/VM 内映射和 Finder 风格移动按环境单独验证；默认关闭。macOS Option+字母符号输入不在 v1 范围。

## 3. 关键系统冲突：不可绕过的验收关

⌘L / Win+L：单个 AHK 热键声明不能证明系统锁屏冲突已解决。必须在目标 Windows、键盘和后端上记录真实按键结果，且保持右 Windows 入口或独立锁屏方式有效。禁止修改系统锁屏安全策略。涉及驱动或提权的实验须另有用户明确授权。

若无法证明左⌘L 聚焦地址栏且不锁屏，将功能标为 BLOCKED 并关闭该映射；原型说明中明确物理左⌘L 仍可能触发原生锁屏，应使用 Ctrl+L。原型可按第 9 节验收，完整 v1.0 不得通过；不能把备用入口记成原功能 PASS。

终端：每个受支持宿主 × shell × 配置均测“有/无选区 × 空闲/运行可中断任务”。选区识别失败时不得回落通用复制。对 Cmd+C 无选区测试，用无敏感信息的剪贴板哨兵验证内容未变，并检查 shell 未收到输入、前台任务持续运行。

Win Native：独立原生入口应在 MacFlow 启用、停用、异常结束后都可使用。恢复 Windows 锁屏、文件资源管理器或运行对话框，不得依赖 MacFlow 正常运行。

双引擎生命周期：统一控制器负责所有受管组件的 Enable/Disable/Quit、健康检查与状态展示。若采用分离进程，监督机制不得仅依赖可能崩溃的 AHK 工作进程；任一映射引擎失效应停止其余受管映射，回到可验证的 Native Mode。仅结束一个进程不算恢复成功。

停用时停止接收新映射，按已验证顺序退出/旁路各输入层，释放本次映射产生的合成按键并清理状态；不得盲目改写用户仍按住的原生键。焦点切换、断连、唤醒也要处理遗留状态。若不能保证整套停用及崩溃恢复，双引擎模式不得交付。

Disable、Quit 和单引擎崩溃恢复的验收目标均为触发后 2 秒内停止映射并恢复可用原生输入；未达到即 FAIL。异常无法清理时显示可见故障并提供鼠标恢复入口，不能仅将托盘文字改成 Disabled。

## 4. 文件与目录结构

MacFlow/

  README.md

  AGENTS.md

  PLAN.md

  docs/{contracts.md,decisions.md,progress.md,environment.md,input-discovery.md,compatibility-matrix.md,test-report.md,rollback.md}

  config/{schema.json,mappings.yaml,apps.yaml,release.yaml}

  src/ahk/{main.ahk,config.ahk,input.ahk,router.ahk,global.ahk,terminal.ahk,browser.ahk,explorer.ahk,emergency.ahk}

  src/controller/                         # 仅在候选多进程模式需要时实现

  integrations/{vscode/,windows-terminal/}

  src/kanata/{experimental.kbd,README.md}

  tools/{inspect-keys.ps1,generate-config.py,validate-config.py,smoke-tests.ps1}

  tests/{mapping-spec.yaml,manual-checklist.md,evidence/}

  build/generated/                       # 配置编译产物，禁止手改

  .github/workflows/

  dist/

## 5. 多 Agent 协作与责任分工

### Integrator / Lead

唯一维护：AGENTS.md、PLAN.md、docs/{contracts.md,decisions.md,progress.md}、config/{schema.json,release.yaml}、tools/generate-config.py、src/ahk/{config.ahk,input.ahk,router.ahk}、CI 与 dist/ 发布装配。负责接口版本、配置生成、冲突处理、支持范围和发布判定；只有 Lead 合并 main。

开工依赖：A 的输入发现、D 的基础退出设计及 E 的测试定义。B/C/D 进入集成实现前，由 Lead 冻结事件字段、函数接口、规则优先级和 schema。交付证据：接口文档、配置生成结果、集成检查与逐项发布判定；Agent 签字不能替代真机操作者的实测记录。

### Agent A — Input Discovery & Low-level Spike

唯一维护：tools/inspect-keys.ps1、docs/{environment.md,input-discovery.md}、src/kanata/。负责左右 Command/Option/Control 探测、设备隔离能力和候选后端实验；提交报告给 E 更新兼容性矩阵，不直接编辑 E 的文件。

交付证据：设备与版本信息、受控修饰键探测结果、后端/权限/启动命令、事件路径及失败记录。探测工具只在显式诊断会话使用，不持续记录用户输入；涉及驱动或提权另行获得授权。Phase B 依赖 Phase A 原型门槛通过。

### Agent B — Global & Text mappings

唯一维护：src/ahk/global.ahk、config/mappings.yaml。依赖已冻结的输入/路由接口、schema 与 D 的生命周期接口；实现常用 Command、Option 文本导航和应用切换状态，不自行另建全局 hook 或第二份配置。

交付证据：规则 ID、支持上下文、重复/按住/松开行为、可关闭开关、已知差异及可重复测试步骤。测试结果交 E 归档；不得修改公共契约来绕开失败。

### Agent C — Per-application profiles

唯一维护：src/ahk/{terminal.ahk,browser.ahk,explorer.ahk}、config/apps.yaml、integrations/{vscode/,windows-terminal/}。负责应用匹配、原生焦点规则、终端选区行为与增量配置适配；依赖 Lead 的路由接口和 B 的规则 ID。

交付证据：具体应用版本/配置、VS Code Editor/Terminal 区分、终端有无选区与任务状态结果、配置增量及备份/恢复清单。无法识别上下文时提交 BLOCKED 与安全退路，不能靠窗口标题猜测选区。恢复接口交 D 集成。

### Agent D — Tray, startup and rollback

唯一维护：src/ahk/{main.ahk,emergency.ahk}、src/controller/、docs/rollback.md。负责托盘 Enable/Disable/Native Mode/Quit、显示实际模式/配置/受管进程状态、单实例启动、合成按键清理及应用配置恢复入口。

交付证据：鼠标退出、2 秒恢复目标、按住修饰键停用、异常进程退出、重启/唤醒与恢复后的原生操作。多进程方案必须覆盖任一引擎崩溃及监督失效；开机自启仅在用户选择后实施，初次启动保持 Native Mode。

### Agent E — QA & Documentation

唯一维护：tests/、tools/{validate-config.py,smoke-tests.ps1}、docs/{compatibility-matrix.md,test-report.md}、README.md。依赖冻结的契约及各实现者提供的步骤/证据，提供独立的配置冲突检查、测试用例与回归报告。

交付证据：用例 ID、需求/规则 ID、环境、运行模式、commit、操作者/日期、操作步骤、预期与实际结果及状态。自动检查只证明其覆盖的静态或模拟行为；硬件用例须实际操作者执行。不得保存真实输入、密码或剪贴板明文。

协作规则：每个文件仅一个负责人；他人提出补丁/证据，由负责人合入。每个实现分支使用独立 worktree，按可用并发数分批调度，不要求五个 Agent 同时运行。接口变更由 Lead 更新契约并通知受影响角色，随后 E 更新测试。build/generated/ 仅由生成器产生。

## 6. 执行里程碑（24 小时仅作估算）

G0 环境与契约：A 探测基线；Lead 建仓库、文件归属和配置 schema；D 做基础鼠标退出；E 定义验收。退出条件：接口冻结、未知项登记、基础回退可用。无 Windows 真机时可完成开发准备，但硬件门槛保持 NOT TESTED。

G1 核心实现：B/C/D 按接口并行，E 持续检查；优先终端 Ctrl+C/⌘C、中文 IME、常用编辑与停用恢复。退出条件：静态检查通过，全部 P0 在目标环境实测 PASS；否则只算开发预览。

G2 AHK 原型：集成、打包、完成原型验收与 Known Limitations。⌘L 等 P1 可以 BLOCKED/NOT TESTED，但必须关闭或提供明确原生退路；不得把原型标为 v1.0。

G3 候选后端实验：仅在原型基础上评估 Kanata/事件传递方式；驱动或提权前单独取得授权。退出条件：事件身份、Win+L、注入去重及整套故障恢复有证据；实验失败保留 AHK 原型，不强行合入。

G4 v1.0 回归：所选交付模式重新跑全部 P0 与 P1，覆盖版本、配置、中文输入、系统退路及恢复。AHK 原型的 PASS 不自动沿用为另一后端模式的 PASS。

G5 交付：E 整理实测矩阵、安装/停用/卸载说明及演示；Lead 按第 9 节决定交付状态。时间耗尽不会使 FAIL/BLOCKED/NOT TESTED 变成 PASS；缺少真机操作者或关键依赖时如实报告开发预览/原型状态。

## 7. 必测验收用例

记录规则：每个环境和运行模式独立记录 PASS / FAIL / BLOCKED / NOT TESTED。PASS＝实际结果符合全部预期且有证据；FAIL＝已执行但不符合；BLOCKED＝有明确技术/环境障碍；NOT TESTED＝尚未执行。可选项用 required=false 标注，不用假 PASS 掩盖未测试。

T01｜P0｜通用编辑：在 release.yaml 声明支持 GLOBAL 的每个应用/上下文执行，至少包括 Chrome、Notepad 与 VS Code Editor；⌘C/V/X/A/Z/S/F、Shift+⌘Z；在支持编辑/选择状态验证预期动作，无意外系统动作。按应用记录 Ctrl+Y 与 Ctrl+Shift+Z 的选择。

T01b｜P1｜Chrome 浏览器：⌘L/T/W/R/Shift+T、⌘[/]；⌘L 必须聚焦地址栏且不锁屏。原型可登记 BLOCKED；v1.0 必须 PASS。

T02｜P0｜Notepad / VS Code Editor：Option 导航、选择和删词，Command 行首尾/文档首尾；覆盖软换行、中文/英文文本和长按，记录与 macOS 的已知差异。

T03｜P0｜Windows Terminal + PowerShell：逐一执行有/无选区 × 空闲/可中断任务。⌘C 有选区复制且不中断，无选区不输入、不改剪贴板、不中断；物理 Ctrl+C 无选区能中断，有选区与原生基线一致；Ctrl+D/Z 不变；⌘V 不额外执行命令。

T04｜P0｜VS Code：Editor、Integrated Terminal、搜索框/命令面板分别验收焦点规则；Editor 执行 T01＋T02，终端执行 T03。无法识别的区域须验证 bypass，终端不得触发通用编辑映射。

T05｜P0｜原生入口：右⌘+E/R/L/V 或经记录的独立替代入口，在启用、停用、异常退出后均可用。右 Command 能识别时须保留原生语义；替代入口不得依赖 MacFlow 正常运行。

T06｜P0｜基线中文 IME：组字、候选翻页/选择、提交/取消、输入法切换、组字时导航/删除；无丢字、重复或卡键。测试实际 bypass 是否有效；组字期间映射暂停可接受，原生输入损坏不可接受。

T06b｜P0｜边界保护：对基线中的游戏/RDP/VM/密码管理器/管理员窗口验证自动或明确的手动 Native Mode 路径；核验 UAC/锁屏返回后的状态。基线外未安装环境列为 required=false、NOT TESTED，不列入兼容声明；冻结基线中的环境缺失或不可访问则记 BLOCKED 并阻止对应交付。

T07｜P0｜生命周期：鼠标 Disable/Quit、结束受管进程、按住 Command/Option/Shift 时停用、焦点切换后松键；2 秒内停止全部映射，释放自身合成按键，原生键位可用，残留的应用配置不得改变原生输入；注销/重启后默认不自启。

T07b｜P0｜连接与恢复：按住修饰键时断连、蓝牙重连或 USB 拔插、睡眠唤醒；无重复输入、卡键或残留映射，恢复后重测 Ctrl+C、Win+E/L、Alt+Tab。只声明已测连接方式。

T07c｜条件必需｜多进程/双引擎：分别结束 AHK、Kanata、监督组件，验证其余映射停止、真实状态显示、原生应用配置行为及鼠标恢复；按住键时重复。任何失败阻止该模式交付；纯 AHK 单进程不适用，须记录原因。

T07d｜P0｜应用切换：按住⌘连续 Tab、Shift 逆序、松开确认、取消及切换期间停用；无 Alt/Win 残留。

T08｜P0｜配置与隐私：无未经授权的提权/驱动/自启，无输入或剪贴板明文日志、无运行时主动联网；冲突/损坏配置保持 Native Mode；单实例启动；应用配置备份及仅撤销自身变更的恢复可用。

T09｜P1｜Explorer：临时样本复制/粘贴/剪切/全选、新文件夹及删除至回收站后还原；不保证回收的路径禁用删除映射，不执行永久删除；P2 文件移动另测同名冲突。

证据要求：tests/evidence/ 仅存合成测试材料、去敏截图/录屏或人工记录；记录 commit、配置版本、设备/连接、Windows build、应用/IME/shell、模式、操作者及日期。短按至少重复 10 次，长按/焦点切换与相关恢复场景均执行；偶发失败也记 FAIL，不以多数成功判 PASS。

## 8. 故障恢复 Runbook

使用鼠标打开 MacFlow 托盘 → Disable 或 Quit；确认所有受管映射均停止，并测试原生键位。若状态仍异常，继续执行后续步骤。

托盘或控制器无响应时，用鼠标打开 Task Manager，按运行时清单核对 PID、路径和命令行，按已记录的停止顺序先阻止监督组件重启工作进程，再结束本次 MacFlow 实例的全部受管进程（含候选 Kanata/监督进程）；不得批量结束用户其他 AHK 脚本。

先确认应用增量配置已不影响原生输入；若仍有影响，必须按 integrations/ 变更清单撤销。卸载或主动移除适配时，也只恢复 VS Code/Windows Terminal 中 MacFlow 自己的配置，保留用户后续修改。卸载同时移除用户曾选择的自启项。

若仍无法输入，使用独立原生设备和鼠标重启并排查；涉及已获授权的驱动实验时，按记录的具体驱动版本与卸载步骤处理，必要时进入安全模式。不得依赖被映射的键作为唯一恢复手段。

重测 Win+E/L、Ctrl+C、Alt+Tab 和中文 IME；记录根因、受影响模式与失败用例，修复并重新通过相关 P0 前禁止重新启用该模式。

交付包必须列出实际进程名、路径、停用命令、配置备份位置以及具体恢复步骤；“名称以实际为准”不能替代可执行说明。保留鼠标恢复和无需 MacFlow 的原生输入路径；禁止不可回滚的注册表键位改造。

## 9. Definition of Done

验收以固定的 release.yaml、实测环境及运行模式为单位。P0 为基础行为和安全门槛；P1 为 v1.0 必需功能；P2 默认关闭、可延期。用例按环境/连接方式拆成子项：冻结基线内 required=true 的适用子项全部参与发布判定，基线外为 required=false；T06b、T07b 同样适用。基线条件临时不可用属于 BLOCKED，不能临时移出基线规避失败。下表为唯一发布判定，前文 BLOCKED 退路不得绕过此表。



| 交付状态 | 必须满足的门槛 | 可对外说明的结果 |
| --- | --- | --- |
| 开发预览 | 尚有基线必需 P0 未通过，或缺少真机验证。 | 只报告代码、静态检查和阻塞项；不得称为已验收原型或 v1.0。 |
| AHK 原型 | 纯 AHK 模式下，冻结基线内所有 required=true 的 P0 子项均 PASS。P1 可延期，但关闭未验证映射并说明原生退路。 | 可交付已验收原型。⌘L 可为 BLOCKED，明确提示原生锁屏行为；不得称为 v1.0。 |
| MacFlow v1.0 | 所选模式在冻结基线内全部必需 P0、P1 子项 PASS；多进程/双引擎另须 T07c PASS。未验收的可选功能保持关闭。 | 可按已测环境发布 v1.0；必须包含 ⌘L 真机成功证据及整套恢复证据。 |



必需项只接受 PASS；FAIL、BLOCKED、NOT TESTED 任一存在即未满足相应门槛。替代快捷键、Native Mode 或 Known Limitations 只能说明退路，不能替代必需功能验收。冻结后变更支持范围或必需项，必须在 decisions.md 说明原因并同步矩阵，不得为掩盖失败静默降级。

每种模式单独验收；新后端、版本、设备、连接方式或应用配置变更后，受影响结果重测。采用双引擎时 T07c 为发布必需；未采用时记录不适用原因。额外环境未测不阻止基线发布，但不得出现在支持声明中。

交付材料：可启动脚本包、依赖版本与来源、有效生成配置、README、安装/停用/卸载/恢复说明、兼容性矩阵和证据、Known Limitations。E 核对记录完整性，Lead 判定发布状态；硬件测试操作者/日期必须真实。

## 10. 给 Codex Lead 的启动 Prompt（原样复制）

Implement MacFlow from this specification. First inspect the available environment and record the exact Windows build, Magic Keyboard model/transport, layouts/IME, app versions and native terminal behavior. If Windows hardware is unavailable, continue code and static work but keep hardware tests NOT TESTED. Start with the AHK-only prototype; Kanata is an optional experiment, not a predetermined architecture.

Freeze docs/contracts.md, the event/routing/lifecycle interfaces, config/schema.json and config/release.yaml before parallel implementation. Use the single configuration generator and honor the file ownership in section 5. Use isolated worktrees for implementation streams and schedule roles within available concurrency. Lead alone integrates shared interfaces and main.

Preserve physical Control+C/D/Z native behavior; require interruption for Control+C only with no selection and an interruptible foreground task. Command+C must copy selected text without interrupting, and with no selection must neither send input nor change the clipboard. Use verified native VS Code focus bindings and an explicitly validated Windows Terminal adapter. Keep Chinese IME input safe and verify bypass behavior.

Provide mouse-accessible whole-system Disable/Quit, cleanup of owned synthetic keys, configuration backups and rollback. A multi-engine mode requires independent failure supervision and all lifecycle tests. Do not install drivers, change keyboard/security registry settings, elevate or enable autorun without explicit approval. Do not log input or clipboard plaintext.

Follow the milestone gates and the release table in section 9. All required tests need real evidence and PASS; known limitations never waive a required test. Command+L may remain BLOCKED in the prototype but must PASS for v1.0. Do not claim compatibility from compilation or simulation. Report actual tests, changed files, evidence, limitations and the accurate delivery status after each milestone.

## 11. 当前交付与状态

THIS IS AN EXECUTION PLAN, NOT A BUILT APP. 本次仅修订技术路线、公共接口、Agent 归属、测试及发布门槛；尚未在用户的 Windows PC 上运行配置、安装驱动或验证 Magic Keyboard。修订文档不代表授权安装、提权或启用自启。

当前未完成事项：确认环境基线与真机操作者、选择/验证事件实现、冻结 release.yaml、实现并执行全部用例。所有依赖硬件的测试初始状态均为 NOT TESTED；Kanata 路线为候选，尚未选择或验证。




