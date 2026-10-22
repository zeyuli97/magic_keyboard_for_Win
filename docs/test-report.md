# 测试报告

日期 2026-10-22。交付为 **DEVELOPMENT PREVIEW**。本报告仅涉及 macOS 上的静态/合成验证，不含 Windows、AHK 运行或真机通过结论。

配置测试覆盖非法/额外修饰键、重复与上下文重叠、未知 action/context、blocked 规则启用、profile 重叠、VS Code 集成约束、严格 JSON/schema、缺失发布用例与虚假门槛通过。模拟 PASS 只存在单元测试临时数据。

生成器测试覆盖确定性、UTF-16 中文 round-trip、SHA256、缺失/篡改/陈旧文件及不写入的 --check。VS Code 数据检查覆盖触发键对应、noop、选区条件与跳过 shell 设置，不证明真实应用行为。

已在临时整合目录合并读取 Lead 的 schema/release/generator、profiles 的配置/桥接和本 QA 流程，执行 python3 -B -m unittest discover -s tests -p 'test_*.py'：53 项通过，0 项跳过。实际组合配置静态校验有效，prototype/v1 均报告 NOT ACCEPTED。最终主分支 commit 验证由 Lead 补充；这不是 AHK 或硬件结果。

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
