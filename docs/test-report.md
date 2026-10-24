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
