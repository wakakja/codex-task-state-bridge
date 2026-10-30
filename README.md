# Codex Task State Bridge

用于桌宠和本地状态面板的 Codex 多对话任务状态读取模块。通过只读方式获取本机 Codex 主对话的最新任务状态与显示名称，方便解决任务开始通知漏收、多对话计数不准、结束任务残留的问题。

## 来源、致谢与发布范围

本项目起因于对 [jingh12312-rgb/bailong-desktop-pet](https://github.com/jingh12312-rgb/bailong-desktop-pet) 的本机使用和功能增强；本机集成基于原项目 **v0.4.1**，感谢原作者提供的桌宠项目。原项目后续版本的功能和素材请以其仓库为准。

**这里发布的是独立编写的增强模块，不是原项目转载包或完整修改版。** 原项目 [README](https://github.com/jingh12312-rgb/bailong-desktop-pet/blob/main/README.md) 说明源码未指定开源许可证，[ASSETS.md](https://github.com/jingh12312-rgb/bailong-desktop-pet/blob/main/ASSETS.md) 说明美术未额外授予再分发许可。此仓库不包含原项目源码、角色动画、图片、声音、安装包或修改后的可执行文件。

本仓库的 MIT 许可证仅适用于本仓库内独立编写的代码，不授予对原项目及其素材的使用或再分发权。

## 此仓库新增的功能

- **多对话状态读取**：获取每个主对话的最新任务轮次，返回运行、完成或中断等状态。
- **漏事件补偿**：为桌宠提供定期对账依据，即使开始事件丢失，也能发现正在运行的主对话。
- **残留任务清理依据**：提供终态记录，方便界面移除已完成任务。
- **排除子代理**：过滤子代理、审查代理和归档对话，避免把内部工作误算成用户对话。
- **读取真实对话名称**：优先使用本机 Codex 的对话显示名称。
- **只读与容错**：读取实时 WAL；数据库缺失、锁定或结构不支持时返回不可用状态，不修改数据库。
- **JSON 命令行输出**：可单次读取，或每两秒输出一次状态，便于对接其他程序。

详细的本机桌宠增强记录见 [功能对照](docs/LOCAL_ENHANCEMENTS.md)。该文档明确区分已在本仓库发布的模块与仅作说明的本机界面改动。

## 使用

需要 Python 3.10 或更新版本，以及安装并使用过的本机 Codex；代码仅依赖 Python 标准库。

```bash
python cli.py
python cli.py --watch --interval 2
```

程序使用 `CODEX_HOME`，未设置时读取当前用户的 `.codex` 目录。输出会包含真实对话名称与对话编号；请自行决定是否保存、共享或展示这些信息。

在其他 Python 程序中使用：

```python
from codex_activity import read_chat_activity
from codex_titles import read_chat_titles

activity = read_chat_activity()
if activity is not None:
    running = {
        session: row for session, row in activity.items()
        if row['status'] == 'inProgress' and row['completed_at'] is None
    }
    names = read_chat_titles(running)
```

`read_chat_activity()` 返回 `None` 表示暂不可用，不能当作“没有任务”；返回 `{}` 才表示成功读取但没有相关记录。界面应保留原状态，并为开始钩子留出短暂写入宽限，再据最新轮次同步。

## 适用范围与限制

- 当前实现适配本机 Codex 使用的 `state_*.sqlite` 和 `thread_history_*.sqlite` 元数据结构。这是内部实现，Codex 更新可能需要同步适配。
- 按每个对话最大的 `rollout_ordinal` 选择最新轮次，避免历史运行记录造成误报。
- 数据库投影不是跨崩溃场景的绝对实时状态证明；应用异常退出可能留下未终止记录。集成时应结合桌面进程状态与正常生命周期事件。
- 不连接 OpenAI API，不发送网络请求，不读取消息正文；只查询名称、会话标识、代理类型及轮次状态元数据。
- 这是状态读取工具，不含桌宠界面、动画播放或 Windows 自启动安装器，也不会自动修改 Codex 配置。
- 本项目非 OpenAI 官方产品，也不代表原桌宠作者发布。

## 开发记录

本仓库从本机桌宠同步增强工作中整理而来，发布时仅进行了源文件与发布范围整理；没有为这个独立仓库运行自动化测试。原本机集成的运行状态观察不等同于独立仓库在所有环境的验证。

## 许可证

本仓库独立代码采用 [MIT](LICENSE)。第三方项目及素材遵循各自授权。
