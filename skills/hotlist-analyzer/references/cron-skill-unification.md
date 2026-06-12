# Cron-Skill 统一模式

> 发现于 hotlist-analyzer 优化（2026-05-30）。
> 当 cron 定时任务有自己的内联 prompt，而 SKILL.md 也有自己的流程说明时，
> 两套内容并行 → 维护负担、不一致风险、cron 更新不会自动同步到 SKILL.md。

## 问题信号

cron job 的 prompt 和 SKILL.md 出现以下特征时，说明存在"两套系统"问题：

1. **cron prompt 不加载 skill** — `skills: []`，prompt 内联写了完整的采集+分析流程
2. **SKILL.md 没有被 cron 引用** — cron prompt 看不到 SKILL.md 的更新
3. **内容重复** — 同样的采集平台列表、分析规则、降级方案在两者中各自维护
4. **Prompts >200 字** — 如果 cron prompt 自己描述了完整流程而非引用 skill

## 修复模式

### Step 1：在 SKILL.md 顶部创建「Cron 执行流程」章节

```
## Cron 执行流程（单一真相源）

> 用途：cron 定时任务直接加载本 skill，按此流程执行。替换内联 prompt。

### Step 1：采集 → ...
- **输入**：...
- **输出**：...
- **操作**：...

### Step 2：筛选 → ...
...
```

关键要素：
- 位于 SKILL.md 最顶部（降低后内容之下，具体实现之上）
- 输入/输出明确
- 5 步以内，线性流程
- 含回退链/降级方案

### Step 2：简化 cron prompt

改前（内联完整流程）：
```
你是一名热点分析系统。任务：
1. 用 curl 实时采集全网热点
2. 挑出 3-4 条值得深挖的
3. 阅读原文+搜索背景
4. 给原文链接
```

改后（引用 skill）：
```
按 hotlist-analyzer skill 的 Cron 执行流程执行
```

最好加载 skill（`skills: [hotlist-analyzer]`）而非仅靠 prompt 引用。

### Step 3：清理 SKILL.md 中的重复内容

创建 Cron 执行流程后，原来分布在文档各处的重复流程章节应标记为 superseded：
- 旧 cron 模板章节 → 加注「已被 Cron 执行流程替代」
- 分散的采集命令 → 归入「详细参考」
- Python 代码模板 → 移到 `references/` 目录

## 适用场景

- 任何有定时任务的 skill，且 cron prompt 和 SKILL.md 内容重叠
- 特别是内容会频繁更新的 skill（API 变更、降级方案调整、追踪项增加）
- 一个 Cron 执行流程 + 一个简短的 cron prompt = 单一真相源
