# 个人 AI 学习助手

一个通过 DeepSeek 提供回答、长期记忆和工具调用的 Python 命令行助手。

## 桌面对话窗口（Windows）

完成下面的环境和密钥配置后，双击项目中的 **启动助手.vbs**，即可打开独立窗口，
无需启动 VS Code 或终端。也可运行 `venv\Scripts\pythonw.exe desktop.py`。
启动器使用本项目的虚拟环境，不需要安装额外的 GUI 依赖（使用 Python 自带 Tkinter）。

- 默认采用深色背景与蓝紫色点缀；侧边栏的“外观与个性化”支持深空、明亮、暖纸主题。
- 可选择系统字体、10–20 号字号和自定义强调色，修改会实时预览；保存后下次启动沿用。
- “取消”会恢复修改前的样式，“恢复默认”可以重置，再点击“保存”使其生效。
- 外观独立保存在 `data/appearance.json`，会话继续复用原来的记忆文件。
- 支持新建、切换、删除会话及只读查看长期记忆；删除前会询问。
- Enter 发送，Shift+Enter 换行，文字可选中后按 Ctrl+C 复制。
- 请求在后台线程执行，等待时可以编辑下一条草稿或调整外观；为保证会话归属，
  本轮结束前暂时禁止切换/删除会话、发送和关闭窗口。
- 模型失败时，问题放回输入框供重试；关闭窗口后不会有后台对话继续运行。

桌面窗口会阻止重复启动。请不要同时运行终端版写入同一份记忆文件；目前不是多进程数据库。
助手回答支持轻量 Markdown 排版：标题、粗体、斜体、删除线、列表、引用、分隔线、
行内代码、围栏代码块，以及可点击的 HTTP/HTTPS 链接。历史回答也会按相同方式排版，
存储的原始 Markdown 保持不变；用户输入与错误提示按原文显示。
不支持完整 CommonMark、复杂嵌套、表格、HTML、图片或数学公式排版；逐字流式输出、附件和任务取消尚未实现。
本地界面无需联网，但对话和工具仍使用原先的远程 API，密钥配置仍在 `.env`。

如需离线预览，可运行 `venv\Scripts\python.exe test/desktop_preview.py`，
该预览使用临时对话和模拟回答，不调用 API；与正式窗口共用外观设置。

## 启动

使用 Python 3.10 或以上版本，在项目目录执行：

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
# 编辑 .env，填写 DEEPSEEK_API_KEY；已有配置会保留。
.\venv\Scripts\python.exe main.py
```

已有环境只需安装依赖并启动，不必重新创建 venv。
requirements.txt 固定的是本项目当前虚拟环境中已安装的直接依赖版本。

配置项：

- DEEPSEEK_API_KEY：模型调用所需密钥；缺失时仍可导入模块和使用本地会话命令。
- DEEPSEEK_MODEL：默认 deepseek-flash，可按自己的 API 权限调整。
- DEEPSEEK_BASE_URL：默认 https://api.deepseek.com。
- BOCHA_API_KEY：可选，不配置时联网搜索返回不可用提示。

模型可用性需要真实 API 验证；离线测试不验证账号权限或服务端模型名称。

## 命令

/help、/new、/history、/switch 会话ID、/delete 会话ID、
/memory、/forget 记忆ID、/exit。删除操作保留二次确认。
Ctrl+C 或输入结束均可退出。

## 结构

- main.py：命令行交互与命令分发，导入时不启动程序或创建会话。
- chat.py：ChatService 组织一轮问答、整轮保存和长期记忆提取。
- context.py：系统提示词、长期记忆和最近完整问答的上下文组装。
- agent.py：模型与工具之间的循环，最多 5 次带工具的模型请求；耗尽后额外请求一次无工具总结。
- llm.py：模型客户端按需初始化，单次请求超时 60 秒，最多重试 1 次；整体耗时可能更长。
- config.py：项目目录下的环境变量、模型配置与上下文预算。
- memory.py：多会话 JSON 存储及标题生成，add_turn 一次提交整轮问答。
- long_term_memory.py：跨会话的用户资料提取、去重和存储。
- prompt.py：助手的系统提示词。
- executor.py、tools/：工具分发、参数说明、计算器与联网搜索。
- data/：原有会话和长期记忆文件，数据格式保持兼容。
- test/：离线回归测试，真实 API 测试默认跳过。

## 上下文与限制

发送给主对话模型的历史默认最多 24000 字符，按最近完整问答对保留。
长期记忆默认最多 4000 字符，优先纳入最近更新的完整条目。
单次输入上限 12000 字符，超限会提示拆分，不会静默截断。
每条工具结果最多 3000 字符，截断时显式标注。这些限制可在 config.py 调整。

字符预算不等于精确 token 预算，也不包含工具 schema 等协议开销。
暂未实现历史摘要、相关记忆检索和全轮工具输出总预算；较早或单轮过长的历史可能不进入当前上下文，
但磁盘中的完整历史继续保存。长期记忆提取仍会传入全部已有记忆，规模增大后也需要单独管理预算。

默认情况下，每轮回答后仍会请求一次长期记忆提取，新会话还会请求标题生成。
当前 CLI 在这些同步操作完成后展示结果，流式回答与后台更新列为后续扩展。

问答保存失败会显示已生成的回答及未保存提示；记忆更新失败不会撤销已保存的问答。
JSON 原子替换用于防止半文件写入，目前仍面向单进程使用，不提供多进程并发事务。

## 测试

```powershell
.\venv\Scripts\python.exe test/run_all.py
```

离线测试使用模拟模型或临时文件，不修改实际记忆数据。
test/test_title_live.py 和 test/test_tool_call.py 单独运行会真实请求 API 并可能产生费用。
本项目的 skip 标记由 test/run_all.py 处理，测试入口以该运行器为准。

后续功能及实现顺序见 [ROADMAP.md](ROADMAP.md)。
