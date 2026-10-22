# 测试报告

日期 2026-10-22。交付为 **DEVELOPMENT PREVIEW**。本报告仅涉及 macOS 上的静态/合成验证，不含 Windows、AHK 运行或真机通过结论。

配置测试覆盖非法/额外修饰键、重复与上下文重叠、未知 action/context、blocked 规则启用、profile 重叠、VS Code 集成约束、严格 JSON/schema、缺失发布用例与虚假门槛通过。模拟 PASS 只存在单元测试临时数据。

生成器测试覆盖确定性、UTF-16 中文 round-trip、SHA256、缺失/篡改/陈旧文件及不写入的 --check。VS Code 数据检查覆盖触发键对应、noop、选区条件与跳过 shell 设置，不证明真实应用行为。

已在当前项目主分支整合目录执行 python3 -B -m unittest discover -s tests -p 'test_*.py'：**54 项通过，0 项跳过**，包含运行配置中的全部源文件 SHA256 对应检查。tools/validate-config.py 报告配置有效；tools/generate-config.py --check 确认 3 个生成产物一致。prototype/v1 均报告 NOT ACCEPTED；这不是 AHK 或硬件结果。Windows 结果需另记实际测试 commit 与配置 hash。

| 项目 | 状态 | 原因 |
| --- | --- | --- |
| AHK /validate 和 --self-test | NOT TESTED | 没有 Windows AHK 运行环境 |
| 全部真机用例 | NOT TESTED | 无 Windows + Magic Keyboard 操作者/证据 |
| T03 实现 | BLOCKED | Windows Terminal 选区/no-op 适配不可用 |
| T01b 的 ⌘L | BLOCKED | 保留键冲突未解决 |
| T09 回收站删除 | BLOCKED | 缺少可靠回收能力判断 |
| T07c | 不适用 | 单进程 ahk-only；不是 PASS |

原型/v1.0 均未通过。Windows 检查入口：

~~~powershell
powershell -NoProfile -File .\tools\smoke-tests.ps1 -AutoHotkeyPath 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe' -SelfTest
~~~

工具只用已安装运行时，不下载安装、提权或启用映射；超时只停止本次启动的子进程。语法/初始化通过仍保持硬件 NOT TESTED。

## Windows 检查参数核对

已核对 [AutoHotkey 官方 Scripts 文档](https://www.autohotkey.com/docs/v2/Scripts.htm#validate) 及 [v2.0.19 参数解析源码](https://github.com/AutoHotkey/AutoHotkey/blob/v2.0.19/source/AutoHotkey.cpp#L128)：该最低支持版本已经识别 /validate。它加载脚本后退出，不执行主脚本启动逻辑；成功返回 0，加载错误返回非零。保留该官方参数，不引入临时包装主脚本，因此 A_ScriptDir 仍指向原 main.ahk 所在目录。

smoke 脚本并发捕获 UTF-8 stdout/stderr，保留 /ErrorStdOut=UTF-8；每次检查在 15 秒超时后只终止自己启动的子进程，并对清理/输出收尾使用有界等待。语法错误、超时或捕获失败返回非零。可选 --self-test 仅初始化 Native Mode 后退出，不安装映射。语法检查本身不要求生成配置，--self-test 要求配置已生成。

本次仅核对官方文档/最低版本源码并审阅 PowerShell 实现；当前主机没有 PowerShell 或 Windows AHK，尚未执行该脚本。Windows 语法检查、超时/错误捕获路径和硬件结果继续为 NOT TESTED。
