# 测试报告

初始报告日期 2026-10-22；本地 Windows 补充于 2026-10-23。交付为 **DEVELOPMENT PREVIEW**。本报告区分静态验证、Windows AHK 自检和真机结果；当前没有物理按键或应用兼容性 PASS。

配置测试覆盖非法/额外修饰键、重复与上下文重叠、未知 action/context、blocked 规则启用、profile 重叠、VS Code 集成约束、严格 JSON/schema、缺失发布用例与虚假门槛通过。模拟 PASS 只存在单元测试临时数据。

生成器测试覆盖确定性、UTF-16 中文 round-trip、SHA256、缺失/篡改/陈旧文件及不写入的 --check。VS Code 数据检查覆盖触发键对应、noop、选区条件与跳过 shell 设置，不证明真实应用行为。

初始 macOS 检查及本次 Windows 隔离工作树检查均为 **76 项通过，0 项跳过**。覆盖 Explorer undo/find 配置回归、每应用动作能力检查、Python/AHK/schema 策略一致性、实际 handler 支持集检查、Git 索引打包（含拒绝未暂存修改），以及 CI 共用清理脚本和行为测试接入的源码检查。PowerShell 行为脚本另行执行，不计入这 76 项。缺少必须模块不再跳过测试。tools/validate-config.py 报告配置有效；tools/generate-config.py --check 确认 3 个生成产物一致。prototype/v1 均报告 NOT ACCEPTED；静态结果不代表 AHK 或硬件结果。

| 项目 | 状态 | 原因 |
| --- | --- | --- |
| AHK /validate、--self-test、--registration-test | PASS（本地自检） | Windows build 26200.9711、AHK 2.0.19 x64、非管理员进程；未启用映射或发送输入 |
| Windows CI 与 SAFER 降权启动器 | NOT TESTED | 已配置；本轮未推送/运行 Windows job |
| PowerShell 7.5+ 模块路径回归 | PASS（本地行为测试） | PowerShell 7.6.5；非空、空字符串、缺失三种状态及 Windows PowerShell 核心模块自动加载通过 |
| 全部真机用例 | NOT TESTED | 用户报告 Magic Keyboard 经 USB 连接；尚无逐项按键或应用行为证据 |
| T03 实现 | BLOCKED | Windows Terminal 选区/no-op 适配不可用 |
| T01b 的 ⌘L | BLOCKED | 保留键冲突未解决 |
| T09 回收站删除 | BLOCKED | 缺少可靠回收能力判断 |
| T07c | 不适用 | 单进程 ahk-only；不是 PASS |

原型/v1.0 均未通过。Windows 检查入口：

~~~powershell
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' -SelfTest
~~~

CI 模块路径回归可在 Windows 的 PowerShell 7.5+ 中单独执行 `pwsh -NoProfile -File .\tests\test-ci-module-path.ps1`。它实际调用启动器共用的清理脚本，覆盖非空、空字符串和缺失的 PSModulePath，并以原始 .NET 子进程启动 Windows PowerShell 检查核心模块自动加载；不启动 AHK，也不代表降权 smoke 或硬件通过。

工具只用已安装运行时，不下载安装、提权或启用映射；超时只停止本次启动的子进程。语法/初始化通过仍保持硬件 NOT TESTED。

## Windows 检查参数核对

已核对 [AutoHotkey 官方 Scripts 文档](https://www.autohotkey.com/docs/v2/Scripts.htm#validate) 及 [v2.0.19 参数解析源码](https://github.com/AutoHotkey/AutoHotkey/blob/v2.0.19/source/AutoHotkey.cpp#L128)：该最低支持版本已经识别 /validate。它加载脚本后退出，不执行主脚本启动逻辑；成功返回 0，加载错误返回非零。保留该官方参数，不引入临时包装主脚本，因此 A_ScriptDir 仍指向原 main.ahk 所在目录。

smoke 脚本并发捕获 UTF-8 stdout/stderr，保留 /ErrorStdOut=UTF-8；每次检查在 15 秒超时后只终止自己启动的子进程，并对清理/输出收尾使用有界等待。语法错误、超时或捕获失败返回非零。可选 --self-test 仅初始化 Native Mode 后退出，不安装映射。语法检查本身不要求生成配置，--self-test 要求配置已生成。

初始开发轮仅核对官方文档/最低版本源码并审阅 PowerShell 实现，当时没有 Windows AHK 环境。本次本地 Windows 执行结果见上表；完整超时/错误捕获路径覆盖及硬件验收仍不能由正常自检通过推断。

注册自检另用 -RegistrationTest，实际执行正常启动共用的 HotIf/Hotkey/emergency 注册路径，所有条件保持 Native，随后 Suspend/卸 hook 并退出；不发送输入。它不验证托盘、WTS 会话通知、物理按键或应用效果。

预览包改为 Git 索引清单，不再递归收集未跟踪文件；内容取自索引，发布文件存在未暂存修改时拒绝打包；ZIP_STORED 和固定元数据避免压缩库差异。CI 的 --check 校验重建包与已提交清单，失配不自动更新清单。所有打包测试均使用临时 Git 仓库和无敏感信息的哨兵。

## 2026-10-23 本地 Windows 修复与验证

- 将路由函数中的局部 `thread` 改为 `threadId`，消除与 AHK 内置名称重名产生的警告弹窗；前台线程、布局和权限判断逻辑保持一致。
- 校验和读取显式去除空格、制表符及 CR/LF。AHK 的默认 Trim 只去除空格和制表符，原实现会因生成器写入的末尾换行而误报 checksum mismatch；64 位十六进制格式与实际 SHA256 比较仍执行。
- 打包测试在自身临时目录内将 `.git` 改名以模拟缺失索引，由 TemporaryDirectory 清理；避免直接删除 Windows 上只读的 Git 对象文件。原有失败断言保持生效。
- 使用实际 AHK `--self-test` 验证五组隔离配置：LF、CRLF 校验和均正常加载；错误校验和、修改后的 INI、陈旧源配置均返回失败。未安装热键或启用映射。

环境：Windows x64 25H2 build 26200.9711；Python 3.13.5；PowerShell 7.6.5；官方 AutoHotkey 2.0.19 x64，EXE SHA256 `3880f9ec464dfe78c16bbd8b9f30560227154c292280337346a30c8fd92871fe`。配置 INI SHA256 `fcac4113d35de9f949385c097f1f2391254591847985feea3e8b6da8273ff837`。自动检查操作者为 Codex；物理按键操作者及设备型号/布局待记录。

传入目录不含上游 Git 元数据。本轮在项目 `.local` 中建立本地快照及隔离 Git 工作树，基线 commit 为 `8fc0a0c6a53561f48ecbc409c5ce184ecf57f900`；这是本地验证基线，不是上游提交。本轮差异、集成后源文件 hash 和检查记录保存在 `tests/evidence/local/`。未推送远端；本地检查不代表 GitHub Windows CI 或 Magic Keyboard 真机验收通过。

## 2026-10-23 修复轮（候选修复，硬件 NOT TESTED）

背景：受控 Notepad 测试中，⌥← 已经进入判定、处理和发送，但应用只显示 F/E 菜单访问键、光标不动；“Enabled 但全部不生效、⌘A 打开快速设置”与 Notepad 布局变回 `08040804` 同时出现。候选解释有两点：
- WinUI 访问键不把 Ctrl（AHK 默认屏蔽键 `vk11sc01D`）当作中间键；
- ⌥⇧ 组合在 Windows 看来是单独按下又松开的 Left Alt+Shift，触发了默认的输入语言热键。

两者都未经真机证实。改动均在本地分支 `claude/alt-guard-fixes`，未集成到根目录发布文件：

- Option 组合输出前后各插入一次 `{Blind}{vkE8}`；`A_MenuMaskKey` 改为 `vkE8`。
- `MF_SendTap` 返回是否实际发送；首次 Tab 未发出时立即带屏蔽释放持有的 Alt。
- Status 显示最近一次映射判定的固定原因（只存内存，不含按键）。
- `#Warn All, StdOut`，smoke 遇到 AHK 警告即失败。
- 门槛新增按 rules × profiles 的覆盖检查。
- 打包测试不再要求源目录是 Git checkout，预览包包含 CI workflow；validate-config 在重定向输出时不再因中文 reason 崩溃；测试读文件统一用 UTF-8。
- `release.yaml` 更新了基线和 reason 文本，用例状态未改。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| validate-config / generate-config --check | VALID；3 个生成物一致 | 静态 |
| unittest（worktree） | 87 项通过，0 跳过 | 含新增覆盖、编码、源码防护检查 |
| unittest（不含 .git 的副本、解压后的新预览包） | 87 项通过 | 验证 R2；只需已安装 Git |
| AHK /validate、--self-test、--registration-test | PASS，无 `#Warn` 警告 | AHK 2.0.19 x64，非管理员；不发送输入 |
| smoke 警告检测反向验证 | 注入警告的临时副本按预期失败 | 不涉及按键 |
| 真机 Option/⌘Tab/输入法复测 | NOT TESTED | 需用户按 FIXES 文档步骤执行 |

配置 INI SHA256 `28d2c07721b0afe29e4dbf7e5b78a6a7f409270cbc94a5d54852ec0c2028c21c`。门槛现报：
- prototype 额外阻塞：Chrome 浏览器映射只依赖 T01b；Explorer 映射只依赖 T09；Chrome 文本导航无任何用例覆盖。
- v1 额外阻塞：Chrome 文本导航无任何用例覆盖。

## 2026-10-23 阶段 1：微软拼音英文模式（已被本报告最后一节取代，未集成）

用户报告：Alt 防护版在 ENG 布局下的映射已经生效，包括 Option 导航。这是用户口头报告，不是完整验收运行。

本阶段改动：
- **生效条件：**微软拼音（`08040804`）只在焦点窗口的 IME 转换模式不含中文位时，才按 US 规则映射。
- **布局检查：**前台线程和焦点线程的布局都必须合格。
- **透传：**“中”模式、IME 窗口不可用、查询超时（每次 50 ms）、拿不到焦点线程时，整窗透传，并在 Status 显示原因。
- **配置：**新增 `apps.ime_english_mode_hkls`，Python、schema 与 AHK 加载器保持一致；发布配置启用了 `08040804`。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| 2026-10-23 交互探针（Notepad） | 中 conv=1025、英 conv=0，10 次切换全部对上；组字期间 conv 不变、无可见候选窗 | 只读：进程名、布局、IME 数值、窗口类名 |
| validate-config / generate-config --check | VALID；3 个生成物一致 | 静态 |
| unittest（worktree） | 91 项通过，0 跳过 | 含新增的布局校验、一致性、INI 字段、源码契约检查 |
| AHK /validate、--self-test、--registration-test | PASS，无警告 | AHK 2.0.19 x64，非管理员；不发送输入 |
| 只读判定探针（新代码，ENG 前台） | Chrome、Notepad 走 US 路径，判定为可映射 | 拼音分支需在拼音下实测 |
| 拼音“英”/“中”实机映射，Chrome/VS Code/Explorer 读数 | NOT TESTED | 需用户按 FIXES 文档执行 |

本阶段的配置 INI SHA256 为 `c7517e8e2cb53a09b6b4a88b2c7e2dcec00e4f865d3acf585a4bd4ae1765736b`，source hash 为 `7bb6b7520d5d77333a3c9bbccd2df34da55b2476227bfa3042ddc8c5d6d25273`，取代上一节的值。

## 2026-10-23 布局判定线程修正（候选，硬件 NOT TESTED）

用户在 ENG 下按左 ⌘+A，映射不生效。按用户要求只读诊断，当时的情况：
- 运行中的是阶段 1 之前的修复版（PID 20992，13:53 启动）。
- Notepad 顶层窗口线程的布局是 `08040804`。
- 正文编辑控件在另一个线程，布局是 `04090409`；文本为纯英文，光标后面没有中文。

结论：
- 原实现只检查顶层线程，于是把 ⌘A 透传成 Win+A。
- 阶段 1 初版要求两个线程都合格，同样会透传。

现已改为只看焦点窗口所在线程（真正接收按键的线程）的布局。单测 91 项通过，AHK 语法、自检、注册检查通过，无警告。需要用户退出旧实例并重启新版后复测。

## 2026-10-23 拼音“中”模式也映射（候选，硬件 NOT TESTED）

上一节的复测：用户退出旧实例、重启线程修正版后，在 Notepad 按左 ⌘+A 能全选。只试了一次，当时两个线程的布局没有记录。证据见 `tests/evidence/local/2026-10-23-windows-native/usb-input-thread-fix.json`。

本节改动经用户批准，取代阶段 1：
- **生效条件：**焦点窗口线程的布局为 `04090409` 或 `08040804`，就按 US 规则映射。微软拼音“中”“英”两种模式都映射，不再读输入法状态，也不检测组字。
- **配置：**`08040804` 移入 `apps.allowed_hkls`；删除 `apps.ime_english_mode_hkls`，再出现会报未知字段。删掉 `08040804` 并重新生成，即恢复中文输入整窗透传。
- **取舍：**映射只在按住左 ⌘ 或左 ⌥ 时生效，打拼音碰不到。组字时按到映射组合，等于按了对应的 Windows 快捷键：最坏是拼音字母原样上屏或被取消，再加上快捷键本身的效果。原先“中”模式透传，会把同样的按键变成 Win 键快捷键（快速设置、窗口贴边、Chrome 后退），打断更大。组字检测只有在组字时吞掉按键才有用，代价是每次按映射组合都多一次跨进程查询，所以未采用。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| validate-config / generate-config --check | VALID；3 个生成物一致；门槛阻塞项与上一节相同 | 静态 |
| unittest（worktree） | 91 项通过，0 跳过 | 含布局白名单、旧字段拒绝、INI 字段，以及路由不再查询输入法的源码检查 |
| unittest、generate-config --check（解压后的新预览包） | 91 项通过；3 个生成物一致 | 解压后运行，包内不含 .git |
| AHK /validate、--self-test、--registration-test | PASS，无警告 | AHK 2.0.19 x64，非管理员；不发送输入 |
| 拼音“中”模式映射、组字中误触、⌘⇧Z 是否切换中/英 | NOT TESTED | 需用户按 FIXES 文档执行 |

配置 INI SHA256 为 `645ff2b7cb25f2be47d5ef220feba708796efd26b52941bacdfd03163ea60677`，source hash 为 `0eb5745997dc565f75e9c2e38613356ade17879b9a7671f3d5e61c21374b8f33`，取代前几节的值。

用户报告：重启这一版（20:36Z 启动，晚于最后一次代码修改）后大致测试，没有发现问题。没有说明做了 FIXES 第 11 节的哪些步骤、在哪些应用里测，也没有逐项次数，所以不算完整验收，T06 仍为 NOT TESTED。证据见 `tests/evidence/local/2026-10-23-windows-native/usb-pinyin-both-modes.json`。随后按用户要求提交并集成到项目根目录。
