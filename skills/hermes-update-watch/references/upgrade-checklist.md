# 本机升级 SOP（git 安装 + uv venv + 多 cron + 飞书网关）

> 本机形态：源码 git 克隆在 `~/.hermes/hermes-agent`（branch `main`），venv 在该目录内；
> 主模型走聚合网关 agent-router；跑着多个 cron；飞书网关常驻。**该环境有 3 个专属坑，见 §3。**

**铁律：升级动作必须先经用户确认，agent 不得自行执行。**

---

## §1 升级前（备份 + 快照）

```bash
# 1) 记录当前版本与提交（回滚点）
hermes --version
git -C ~/.hermes/hermes-agent rev-parse HEAD            # ← 记下这个 SHA
git -C ~/.hermes/hermes-agent log -1 --format='%cI %s'

# 2) 备份配置与任务（改动前必做）
cp ~/.hermes/config.yaml ~/.hermes/config.yaml.bak.$(date +%Y%m%d)
cp ~/.hermes/cron/jobs.json ~/.hermes/cron/jobs.json.bak.$(date +%Y%m%d)

# 3) 记录 venv 里现有第三方包（升级后对比，发现丢失）
ls ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages > /tmp/sitepkgs.before
```

## §2 升级

```bash
# git 安装（推荐，两种情况都行）
hermes update
# 或手动：
git -C ~/.hermes/hermes-agent pull --ff-only origin main

# 依赖变化时（uv 管理，无 pip 模块）
cd ~/.hermes/hermes-agent && uv sync
```

## §3 本机专属坑（务必逐条检查）

1. **uv 重建 venv 会丢第三方包**（该环境无 pip 模块）
   ```bash
   ls ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages > /tmp/sitepkgs.after
   diff /tmp/sitepkgs.before /tmp/sitepkgs.after | grep '^<'   # 丢了什么
   uv pip install --python ~/.hermes/hermes-agent/venv/bin/python3 <包名>
   ```
2. **改主模型后 cron 的 `model_snapshot` 会 drift_skip（静默跳过）**
   - 升级本身不改模型；但若升级后顺手改了主模型/网关，带 `model_snapshot` 的 cron 会被静默跳过
   - 处置：`hermes cron list --all` 看有没有 job 处于跳过/未跑状态；必要时重建该 job 的 snapshot
3. **配置改动要 `/restart` 才生效；工具/技能改动要 `/reset`（新会话）**
   - 网关：`hermes gateway restart` 或在会话里 `/restart`
   - 升级完必须重启网关进程，否则跑的是旧代码

## §4 升级后验证（逐条打勾）

```bash
hermes --version                 # 版本已变
hermes doctor                    # 依赖/配置自检
hermes status --all              # 组件状态
hermes cron list --all           # job 是否正常排期、有无失败/跳过
hermes gateway status            # 网关活着
```

- [ ] `hermes --version` 到达目标版本
- [ ] `hermes doctor` 无 error（warn 可接受，记录）
- [ ] `hermes skills list` 自定义技能仍在（`~/hermes-custom/skills` 的 symlink 未断）
- [ ] 飞书网关实测：发一条测试消息 / 回一条 DM，确认收发正常
- [ ] **实跑一个关键 cron**（例：`cronjob action=run <job_id>`），确认能跑通并投递
- [ ] 会话检索/记忆正常（`session_search` 一次、记忆写入一次）
- [ ] 站点风险：确认没有"升级后首次调用才暴露"的 provider/base_url 兼容问题（跑一次主模型对话）

## §5 回滚

```bash
# 代码回滚到升级前的 SHA（危险操作，需用户确认）
git -C ~/.hermes/hermes-agent reset --hard <升级前 SHA>
cd ~/.hermes/hermes-agent && uv sync          # 依赖回滚
cp ~/.hermes/config.yaml.bak.<日期> ~/.hermes/config.yaml   # 配置回滚（如已改）
hermes gateway restart
```

回滚后重跑 §4 的验证清单。

## §6 升级时间窗

- **避开 cron 密集时段**：08:30（serp）、09:00/20:00（热榜）、14:00（模型巡检）、16:00（A股）、21:00（FinNova）
- 推荐窗口：**周六 10:30–12:00**（本技能周报出完之后，用户在场时）
- 升级期间网关重启会中断在跑的会话，动手前跟用户说一声
