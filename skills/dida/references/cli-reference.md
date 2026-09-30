# dida CLI 命令参考（自动抓取）

来源：`dida --help` 递归采集，共 65 个命令节点。CLI 版本：
来源：`dida --help` 递归采集，共 65 个命令节点，CLI 版本 v0.1.14。

```
dida
    -V, --version   output the version number
    -h, --help      display help for command
  auth
      -h, --help      display help for command
  preference
      -h, --help      display help for command
  task
      -h, --help                          display help for command
  project
      -h, --help                     display help for command
  habit
      -h, --help                   display help for command
  focus
      -h, --help                  display help for command
  tag
      -h, --help        display help for command
  countdown
      -h, --help      display help for command
    login
        -h, --help  display help for command
    token
        -h, --help  display help for command
    status
        -h, --help  display help for command
    logout
        -h, --help  display help for command
    list
        --json      以 JSON 输出
        -h, --help  display help for command
    get
        --type <type>  0|pomodoro 或 1|timing
        --json         以 JSON 输出
        -h, --help     display help for command
    list
        --from <iso>   开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --to <iso>     结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --type <type>  0|pomodoro 或 1|timing
        --json         以 JSON 输出
        -h, --help     display help for command
    create
        --type <type>               0|pomodoro 或 1|timing
        --start-time <iso>          开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --end-time <iso>            结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --task-id <taskId>          关联任务 ID
        --note <note>               专注备注（最多 5000 字符）
        --tasks <json>              关联任务 briefs JSON 数组（最多 1 项）
        --pause-duration <seconds>  暂停时长（秒）
        --adjust-time <seconds>     手动调整时长（秒）
        --added <bool>              是否手动添加（true/false）
        --status <n>                番茄状态（仅番茄钟）
        --duration <seconds>        专注时长（秒）
        --relation-type <types>     关联类型（逗号分隔整数）
        --json                      以 JSON 输出
        -h, --help                  display help for command
    update
        --type <type>               0|pomodoro 或 1|timing
        --task-id <taskId>          关联任务 ID（番茄钟）
        --note <note>               专注备注（最多 5000 字符）
        --tasks <json>              替换关联任务 briefs JSON 数组
        --status <n>                番茄状态
        --start-time <iso>          开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --end-time <iso>            结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
        --pause-duration <seconds>  暂停时长（秒）
        --adjust-time <seconds>     手动调整时长（秒）
        --added <bool>              是否手动添加（true/false）
        --json                      以 JSON 输出
        -h, --help                  display help for command
    delete
        --type <type>  0|pomodoro 或 1|timing
        --json         以 JSON 输出
        -h, --help     display help for command
    get
        --json      以 JSON 输出
        -h, --help  display help for command
    list
        --json      以 JSON 输出
        -h, --help  display help for command
    section
        -h, --help      display help for command
    create
        --name <name>                   习惯名称
        --icon-res <id>                 图标资源 ID
        --color <hex>                   颜色
        --sort-order <n>                排序值
        --status <n>                    状态码
        --encouragement <text>          鼓励语
        --type <type>                   习惯类型字符串
        --goal <n>                      目标值
        --step <n>                      步长
        --unit <u>                      单位
        --repeat <rrule>                重复规则，例如 RRULE:FREQ=DAILY;INTERVAL=1
        --reminders <list>              提醒列表（逗号分隔）
        --record-enable <bool>          是否启用记录（true/false）
        --section-id <id>               分区 ID（见 habit section list）
        --target-days <n>               目标天数
        --target-start-date <YYYYMMDD>  目标开始日期
        --completed-cycles <n>          已完成周期数
        --ex-dates <list>               排除日期（逗号分隔）
        --style <n>                     样式
        --json                          以 JSON 输出
        -h, --help                      display help for command
    update
        --name <name>                   习惯名称
        --icon-res <id>                 图标资源 ID
        --color <hex>                   颜色
        --sort-order <n>                排序值
        --status <n>                    状态码
        --encouragement <text>          鼓励语
        --type <type>                   习惯类型字符串
        --goal <n>                      目标值
        --step <n>                      步长
        --unit <u>                      单位
        --repeat <rrule>                重复规则，例如 RRULE:FREQ=DAILY;INTERVAL=1
        --reminders <list>              提醒列表（逗号分隔）
        --record-enable <bool>          是否启用记录（true/false）
        --section-id <id>               分区 ID（见 habit section list）
        --target-days <n>               目标天数
        --target-start-date <YYYYMMDD>  目标开始日期
        --completed-cycles <n>          已完成周期数
        --ex-dates <list>               排除日期（逗号分隔）
        --style <n>                     样式
        --json                          以 JSON 输出
        -h, --help                      display help for command
    checkin
        --stamp <YYYYMMDD>  日期戳，例如 20260407
        --time <iso>        打卡时间（yyyy-MM-ddTHH:mm:ssZ）
        --op-time <iso>     操作时间
        --value <n>         值（默认 1.0）
        --goal <n>          该条目标值
        --status <n>        状态
        --json              以 JSON 输出
        -h, --help          display help for command
    checkins
        --habits <ids>     习惯 ID（逗号分隔）
        --from <YYYYMMDD>  开始日期戳
        --to <YYYYMMDD>    结束日期戳
        --json             以 JSON 输出
        -h, --help         display help for command
      list
          --json      以 JSON 输出
          -h, --help  display help for command
    get
        --json      以 JSON 输出
        -h, --help  display help for command
    list
        --json      以 JSON 输出
        -h, --help  display help for command
    get
        --json      以 JSON 输出
        -h, --help  display help for command
    data
        --json      以 JSON 输出
        -h, --help  display help for command
    members
        --json      以 JSON 输出
        -h, --help  display help for command
    create
        --name <name>       清单名称
        --color <color>     清单颜色（例如 "#F18181"）
        --sort-order <n>    排序值
        --view-mode <mode>  视图模式：list, kanban, timeline
        --kind <kind>       清单类型：TASK, NOTE
        --json              以 JSON 输出
        -h, --help          display help for command
    update
        --name <name>       清单名称
        --color <color>     清单颜色
        --sort-order <n>    排序值
        --view-mode <mode>  视图模式：list, kanban, timeline
        --kind <kind>       清单类型：TASK, NOTE
        --json              以 JSON 输出
        -h, --help          display help for command
    delete
        -h, --help  display help for command
    group
        -h, --help                  display help for command
    column
        -h, --help                               display help for command
      list
          --json      以 JSON 输出
          -h, --help  display help for command
      create
          --name <name>  列名称
          --json         以 JSON 输出
          -h, --help     display help for command
      update
          --name <name>  列名称
          --json         以 JSON 输出
          -h, --help     display help for command
      list
          --json      以 JSON 输出
          -h, --help  display help for command
      create
          --name <name>  分组名称（最多 64 字符）
          --json         以 JSON 输出
          -h, --help     display help for command
      update
          --name <name>  分组名称
          --json         以 JSON 输出
          -h, --help     display help for command
      delete
          -h, --help  display help for command
    list
        --json      以 JSON 输出
        -h, --help  display help for command
    create
        --name <name>       标签名（小写，最多 64 字符）
        --label <label>     标签显示名（最多 64 字符；小写后须等于 name）
        --color <color>     标签颜色（例如 "#F18181"）
        --sort-order <n>    排序值
        --sort-type <type>  排序分组：project, dueDate, createdTime, priority, modifiedTime
        --parent <name>     父标签 name（嵌套标签）
        --json              以 JSON 输出
        -h, --help          display help for command
    update
        --name <name>       标签 name（用于定位）
        --color <color>     标签颜色
        --sort-order <n>    排序值
        --sort-type <type>  排序分组：project, dueDate, createdTime, priority, modifiedTime
        --parent <name>     父标签 name
        --type <n>          标签类型：1=个人，2=共享
        --json              以 JSON 输出
        -h, --help          display help for command
    rename
        --name <name>         当前标签 name
        --new-name <newName>  新标签名
        --scope <n>           0=全部可访问任务同步改名（默认）；1=仅非共享任务改名（共享清单保留旧名） (default: "0")
        --json                以 JSON 输出
        -h, --help            display help for command
    delete
        --name <name>  标签 name
        --scope <n>    0=删除标签并从全部可访问任务移除（默认）；1=仅从非共享任务移除标签（保留标签记录） (default: "0")
        -h, --help     display help for command
    get
        --json      以 JSON 输出
        -h, --help  display help for command
    create
        --title <title>         任务标题
        --project <projectId>   清单 ID
        --parent-id <parentId>  父任务 ID（传 null/none/空表示无父任务）
        --content <content>     任务内容
        --desc <desc>           清单描述
        --all-day               全天任务
        --start-date <date>     开始时间（yyyy-MM-ddTHH:mm:ssZ）
        --due-date <date>       截止时间（yyyy-MM-ddTHH:mm:ssZ）
        --time-zone <tz>        时区
        --reminders <triggers>  提醒触发器（逗号分隔）
        --repeat <rule>         重复规则（RRULE 格式）
        --repeat-from <mode>    重复起算：0=按原截止日期，1=按完成日，2=按日历默认（需同时有 --repeat）
        --priority <n>          优先级：0=无，1=低，3=中，5=高
        --sort-order <n>        排序值
        --items <json|csv>      子任务：JSON 数组或逗号分隔标题
        --tags <tags>           任务标签（逗号分隔）
        --json                  以 JSON 输出
        -h, --help              display help for command
    update
        --id <id>                       任务 ID（body 中必填）
        --project <projectId>           清单 ID
        --parent-id <parentId>          父任务 ID（传 "null" 或 "none" 可取消父子关联）
        --estimated-duration <seconds>  预计专注时长（秒）
        --estimated-pomo <count>        预计番茄数（0-60）
        --title <title>                 任务标题
        --content <content>             任务内容
        --desc <desc>                   清单描述
        --all-day                       全天任务
        --start-date <date>             开始时间（yyyy-MM-ddTHH:mm:ssZ；传 null/none 可清除）
        --due-date <date>               截止时间（yyyy-MM-ddTHH:mm:ssZ；传 null/none 可清除）
        --time-zone <tz>                时区
        --reminders <triggers>          提醒触发器（逗号分隔）
        --repeat <rule>                 重复规则（RRULE 格式）
        --repeat-from <mode>            重复起算：0=按原截止日期，1=按完成日，2=按日历默认（需同时有重复规则）
        --priority <n>                  优先级：0=无，1=低，3=中，5=高
        --sort-order <n>                排序值
        --status <n>                    状态：-1=已放弃，0=未完成，2=已完成（负数请用 --status=-1）
        --completed-time <date>         完成时间（yyyy-MM-ddTHH:mm:ssZ；仅已关闭任务可改，不可清除）
        --items <json|csv>              子任务：JSON 数组或逗号分隔标题
        --tags <tags>                   任务标签（逗号分隔）
        --json                          以 JSON 输出
        -h, --help                      display help for command
    complete
        -h, --help  display help for command
    complete-batch
        --project <projectId>  清单 ID（省略则用收件箱）
        --tasks <ids>          任务 ID（逗号分隔；超过 50 个时截断前 50）
        --json                 以 JSON 输出
        -h, --help             display help for command
    delete
        -h, --help  display help for command
    move
        --from <projectId...>  源清单 ID（可多次指定）
        --to <projectId...>    目标清单 ID（可多次指定）
        --task <taskId...>     要移动的任务 ID（可多次指定）
        --json                 以 JSON 输出
        -h, --help             display help for command
    assign
        --project <projectId>  清单 ID
        --task <taskId>        任务 ID
        --assignee <username>  成员 username（见 project members）
        --json                 以 JSON 输出
        -h, --help             display help for command
    unassign
        --project <projectId>  清单 ID
        --task <taskId>        任务 ID
        --json                 以 JSON 输出
        -h, --help             display help for command
    completed
        --projects <ids>     清单 ID（逗号分隔）
        --start-date <date>  开始时间过滤（yyyy-MM-ddTHH:mm:ssZ）
        --end-date <date>    结束时间过滤（yyyy-MM-ddTHH:mm:ssZ）
        --json               以 JSON 输出
        -h, --help           display help for command
    filter
        --projects <ids>     清单 ID（逗号分隔）
        --start-date <date>  按截止时间（dueDate）下限过滤
        --end-date <date>    按截止时间（dueDate）上限过滤
        --priority <levels>  优先级（逗号分隔：0,1,3,5）
        --tag <tags>         标签（逗号分隔）
        --kind <kinds>       任务类型（逗号分隔：TEXT,NOTE,CHECKLIST）
        --status <codes>     状态（逗号分隔：-1=已放弃，0=未完成，2=已完成；含负数请用 --status=-1,0）
        --json               以 JSON 输出
        -h, --help           display help for command
    search
        --projects <ids>   清单 ID（逗号分隔）
        --tags <tags>      标签（逗号分隔）
        --status <codes>   状态（逗号分隔：-1=已放弃，0=未完成，2=已完成；含负数请用 --status=-1,0）
        --due-from <date>  截止时间下限（yyyy-MM-ddTHH:mm:ssZ）
        --due-to <date>    截止时间上限（yyyy-MM-ddTHH:mm:ssZ）
        --json             以 JSON 输出
        -h, --help         display help for command
    comment
        -h, --help                               display help for command
      list
          --json      以 JSON 输出
          -h, --help  display help for command
      add
          --title <title>  评论内容
          --json           以 JSON 输出
          -h, --help       display help for command
      delete
          -h, --help  display help for command
```

## 各命令完整 help 原文

### `dida`

```
Usage: dida [options] [command]

DIDA CLI – 在终端管理滴答清单的任务、清单、习惯与专注

Options:
  -V, --version   output the version number
  -h, --help      display help for command

Commands:
  auth            OAuth 登录与 token 存储
  preference      查看用户偏好
  task            创建、更新与查询任务
  project         列出并管理清单
  habit           管理习惯与打卡
  focus           创建、查询、更新与删除专注（番茄钟）记录
  tag             列出与管理标签
  countdown       列出倒数日
  help [command]  display help for command
```

### `dida auth`

```
Usage: dida auth [options] [command]

OAuth 登录与 token 存储

Options:
  -h, --help      display help for command

Commands:
  login           通过 OAuth 登录（PKCE，会打开浏览器）
  token <token>   直接设置 access token
  status          查看是否已保存 token
  logout          删除本地保存的 token
  help [command]  display help for command
```

### `dida preference`

```
Usage: dida preference [options] [command]

查看用户偏好

Options:
  -h, --help      display help for command

Commands:
  get [options]   获取用户偏好（当前返回时区）
  help [command]  display help for command
```

### `dida task`

```
Usage: dida task [options] [command]

创建、更新与查询任务

Options:
  -h, --help                          display help for command

Commands:
  get [options] <projectId> <taskId>  按清单与任务 ID 获取任务
  create [options]                    创建任务
  update [options] <taskId>           更新任务
  complete <projectId> <taskId>       完成任务
  complete-batch [options]            批量完成同一清单下的任务（最多 50 个；超出截断并警告；省略 --project
                                      时用 inbox）
  delete <projectId> <taskId>         删除任务
  move [options]                      在清单间移动任务
  assign [options]                    将任务分配给清单成员
  unassign [options]                  取消任务分配
  completed [options]                 列出已完成任务
  filter [options]                    按高级条件筛选任务
  search [options] [keywords]         按关键词与条件搜索任务
  comment                             任务评论
  help [command]                      display help for command
```

### `dida project`

```
Usage: dida project [options] [command]

列出并管理清单

Options:
  -h, --help                     display help for command

Commands:
  list [options]                 列出清单
  get [options] <projectId>      按 ID 获取清单
  data [options] <projectId>     获取清单（含任务与分组）
  members [options] <projectId>  列出清单成员（用于 task assign）
  create [options]               创建清单
  update [options] <projectId>   更新清单字段
  delete <projectId>             删除清单
  group                          清单分组（文件夹）
  column                         看板列
  help [command]                 display help for command
```

### `dida habit`

```
Usage: dida habit [options] [command]

管理习惯与打卡

Options:
  -h, --help                   display help for command

Commands:
  get [options] <habitId>      按 ID 获取习惯
  list [options]               列出全部习惯
  section                      习惯分区
  create [options]             创建习惯
  update [options] <habitId>   更新习惯
  checkin [options] <habitId>  创建或更新打卡（stamp 为 YYYYMMDD）
  checkins [options]           按日期范围查询习惯打卡
  help [command]               display help for command
```

### `dida focus`

```
Usage: dida focus [options] [command]

创建、查询、更新与删除专注（番茄钟）记录

Options:
  -h, --help                  display help for command

Commands:
  get [options] <focusId>     按 ID 获取单条专注记录
  list [options]              列出时间范围内的专注记录（最大 30 天）
  create [options]            创建专注记录（type、start-time、end-time 必填）
  update [options] <focusId>  更新专注记录（type 必填）
  delete [options] <focusId>  删除专注记录
  help [command]              display help for command
```

### `dida tag`

```
Usage: dida tag [options] [command]

列出与管理标签

Options:
  -h, --help        display help for command

Commands:
  list [options]    列出所有标签
  create [options]  创建标签（name 与 label 小写后须一致）
  update [options]  更新标签属性（不能改 name/label；改名用 rename）
  rename [options]  重命名标签（联动任务上的标签）
  delete [options]  删除标签
  help [command]    display help for command
```

### `dida countdown`

```
Usage: dida countdown [options] [command]

列出倒数日

Options:
  -h, --help      display help for command

Commands:
  list [options]  列出所有倒数日
  help [command]  display help for command
```

### `dida auth login`

```
Usage: dida auth login [options]

通过 OAuth 登录（PKCE，会打开浏览器）

Options:
  -h, --help  display help for command
```

### `dida auth token`

```
Usage: dida auth token [options] <token>

直接设置 access token

Arguments:
  token       access token 字符串

Options:
  -h, --help  display help for command
```

### `dida auth status`

```
Usage: dida auth status [options]

查看是否已保存 token

Options:
  -h, --help  display help for command
```

### `dida auth logout`

```
Usage: dida auth logout [options]

删除本地保存的 token

Options:
  -h, --help  display help for command
```

### `dida countdown list`

```
Usage: dida countdown list [options]

列出所有倒数日

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida focus get`

```
Usage: dida focus get [options] <focusId>

按 ID 获取单条专注记录

Options:
  --type <type>  0|pomodoro 或 1|timing
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida focus list`

```
Usage: dida focus list [options]

列出时间范围内的专注记录（最大 30 天）

Options:
  --from <iso>   开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --to <iso>     结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --type <type>  0|pomodoro 或 1|timing
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida focus create`

```
Usage: dida focus create [options]

创建专注记录（type、start-time、end-time 必填）

Options:
  --type <type>               0|pomodoro 或 1|timing
  --start-time <iso>          开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --end-time <iso>            结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --task-id <taskId>          关联任务 ID
  --note <note>               专注备注（最多 5000 字符）
  --tasks <json>              关联任务 briefs JSON 数组（最多 1 项）
  --pause-duration <seconds>  暂停时长（秒）
  --adjust-time <seconds>     手动调整时长（秒）
  --added <bool>              是否手动添加（true/false）
  --status <n>                番茄状态（仅番茄钟）
  --duration <seconds>        专注时长（秒）
  --relation-type <types>     关联类型（逗号分隔整数）
  --json                      以 JSON 输出
  -h, --help                  display help for command
```

### `dida focus update`

```
Usage: dida focus update [options] <focusId>

更新专注记录（type 必填）

Options:
  --type <type>               0|pomodoro 或 1|timing
  --task-id <taskId>          关联任务 ID（番茄钟）
  --note <note>               专注备注（最多 5000 字符）
  --tasks <json>              替换关联任务 briefs JSON 数组
  --status <n>                番茄状态
  --start-time <iso>          开始时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --end-time <iso>            结束时间（yyyy-MM-ddTHH:mm:ss+ZZZZ）
  --pause-duration <seconds>  暂停时长（秒）
  --adjust-time <seconds>     手动调整时长（秒）
  --added <bool>              是否手动添加（true/false）
  --json                      以 JSON 输出
  -h, --help                  display help for command
```

### `dida focus delete`

```
Usage: dida focus delete [options] <focusId>

删除专注记录

Options:
  --type <type>  0|pomodoro 或 1|timing
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida habit get`

```
Usage: dida habit get [options] <habitId>

按 ID 获取习惯

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida habit list`

```
Usage: dida habit list [options]

列出全部习惯

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida habit section`

```
Usage: dida habit section [options] [command]

习惯分区

Options:
  -h, --help      display help for command

Commands:
  list [options]  列出习惯分区
  help [command]  display help for command
```

### `dida habit create`

```
Usage: dida habit create [options]

创建习惯

Options:
  --name <name>                   习惯名称
  --icon-res <id>                 图标资源 ID
  --color <hex>                   颜色
  --sort-order <n>                排序值
  --status <n>                    状态码
  --encouragement <text>          鼓励语
  --type <type>                   习惯类型字符串
  --goal <n>                      目标值
  --step <n>                      步长
  --unit <u>                      单位
  --repeat <rrule>                重复规则，例如 RRULE:FREQ=DAILY;INTERVAL=1
  --reminders <list>              提醒列表（逗号分隔）
  --record-enable <bool>          是否启用记录（true/false）
  --section-id <id>               分区 ID（见 habit section list）
  --target-days <n>               目标天数
  --target-start-date <YYYYMMDD>  目标开始日期
  --completed-cycles <n>          已完成周期数
  --ex-dates <list>               排除日期（逗号分隔）
  --style <n>                     样式
  --json                          以 JSON 输出
  -h, --help                      display help for command
```

### `dida habit update`

```
Usage: dida habit update [options] <habitId>

更新习惯

Options:
  --name <name>                   习惯名称
  --icon-res <id>                 图标资源 ID
  --color <hex>                   颜色
  --sort-order <n>                排序值
  --status <n>                    状态码
  --encouragement <text>          鼓励语
  --type <type>                   习惯类型字符串
  --goal <n>                      目标值
  --step <n>                      步长
  --unit <u>                      单位
  --repeat <rrule>                重复规则，例如 RRULE:FREQ=DAILY;INTERVAL=1
  --reminders <list>              提醒列表（逗号分隔）
  --record-enable <bool>          是否启用记录（true/false）
  --section-id <id>               分区 ID（见 habit section list）
  --target-days <n>               目标天数
  --target-start-date <YYYYMMDD>  目标开始日期
  --completed-cycles <n>          已完成周期数
  --ex-dates <list>               排除日期（逗号分隔）
  --style <n>                     样式
  --json                          以 JSON 输出
  -h, --help                      display help for command
```

### `dida habit checkin`

```
Usage: dida habit checkin [options] <habitId>

创建或更新打卡（stamp 为 YYYYMMDD）

Options:
  --stamp <YYYYMMDD>  日期戳，例如 20260407
  --time <iso>        打卡时间（yyyy-MM-ddTHH:mm:ssZ）
  --op-time <iso>     操作时间
  --value <n>         值（默认 1.0）
  --goal <n>          该条目标值
  --status <n>        状态
  --json              以 JSON 输出
  -h, --help          display help for command
```

### `dida habit checkins`

```
Usage: dida habit checkins [options]

按日期范围查询习惯打卡

Options:
  --habits <ids>     习惯 ID（逗号分隔）
  --from <YYYYMMDD>  开始日期戳
  --to <YYYYMMDD>    结束日期戳
  --json             以 JSON 输出
  -h, --help         display help for command
```

### `dida habit section list`

```
Usage: dida habit section list [options]

列出习惯分区

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida preference get`

```
Usage: dida preference get [options]

获取用户偏好（当前返回时区）

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project list`

```
Usage: dida project list [options]

列出清单

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project get`

```
Usage: dida project get [options] <projectId>

按 ID 获取清单

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project data`

```
Usage: dida project data [options] <projectId>

获取清单（含任务与分组）

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project members`

```
Usage: dida project members [options] <projectId>

列出清单成员（用于 task assign）

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project create`

```
Usage: dida project create [options]

创建清单

Options:
  --name <name>       清单名称
  --color <color>     清单颜色（例如 "#F18181"）
  --sort-order <n>    排序值
  --view-mode <mode>  视图模式：list, kanban, timeline
  --kind <kind>       清单类型：TASK, NOTE
  --json              以 JSON 输出
  -h, --help          display help for command
```

### `dida project update`

```
Usage: dida project update [options] <projectId>

更新清单字段

Options:
  --name <name>       清单名称
  --color <color>     清单颜色
  --sort-order <n>    排序值
  --view-mode <mode>  视图模式：list, kanban, timeline
  --kind <kind>       清单类型：TASK, NOTE
  --json              以 JSON 输出
  -h, --help          display help for command
```

### `dida project delete`

```
Usage: dida project delete [options] <projectId>

删除清单

Options:
  -h, --help  display help for command
```

### `dida project group`

```
Usage: dida project group [options] [command]

清单分组（文件夹）

Options:
  -h, --help                  display help for command

Commands:
  list [options]              列出清单分组
  create [options]            创建清单分组
  update [options] <groupId>  更新清单分组
  delete <groupId>            删除清单分组
  help [command]              display help for command
```

### `dida project column`

```
Usage: dida project column [options] [command]

看板列

Options:
  -h, --help                               display help for command

Commands:
  list [options] <projectId>               列出清单下的看板列
  create [options] <projectId>             创建看板列
  update [options] <projectId> <columnId>  更新看板列
  help [command]                           display help for command
```

### `dida project column list`

```
Usage: dida project column list [options] <projectId>

列出清单下的看板列

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project column create`

```
Usage: dida project column create [options] <projectId>

创建看板列

Options:
  --name <name>  列名称
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida project column update`

```
Usage: dida project column update [options] <projectId> <columnId>

更新看板列

Options:
  --name <name>  列名称
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida project group list`

```
Usage: dida project group list [options]

列出清单分组

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida project group create`

```
Usage: dida project group create [options]

创建清单分组

Options:
  --name <name>  分组名称（最多 64 字符）
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida project group update`

```
Usage: dida project group update [options] <groupId>

更新清单分组

Options:
  --name <name>  分组名称
  --json         以 JSON 输出
  -h, --help     display help for command
```

### `dida project group delete`

```
Usage: dida project group delete [options] <groupId>

删除清单分组

Options:
  -h, --help  display help for command
```

### `dida tag list`

```
Usage: dida tag list [options]

列出所有标签

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida tag create`

```
Usage: dida tag create [options]

创建标签（name 与 label 小写后须一致）

Options:
  --name <name>       标签名（小写，最多 64 字符）
  --label <label>     标签显示名（最多 64 字符；小写后须等于 name）
  --color <color>     标签颜色（例如 "#F18181"）
  --sort-order <n>    排序值
  --sort-type <type>  排序分组：project, dueDate, createdTime, priority, modifiedTime
  --parent <name>     父标签 name（嵌套标签）
  --json              以 JSON 输出
  -h, --help          display help for command
```

### `dida tag update`

```
Usage: dida tag update [options]

更新标签属性（不能改 name/label；改名用 rename）

Options:
  --name <name>       标签 name（用于定位）
  --color <color>     标签颜色
  --sort-order <n>    排序值
  --sort-type <type>  排序分组：project, dueDate, createdTime, priority, modifiedTime
  --parent <name>     父标签 name
  --type <n>          标签类型：1=个人，2=共享
  --json              以 JSON 输出
  -h, --help          display help for command
```

### `dida tag rename`

```
Usage: dida tag rename [options]

重命名标签（联动任务上的标签）

Options:
  --name <name>         当前标签 name
  --new-name <newName>  新标签名
  --scope <n>           0=全部可访问任务同步改名（默认）；1=仅非共享任务改名（共享清单保留旧名） (default: "0")
  --json                以 JSON 输出
  -h, --help            display help for command
```

### `dida tag delete`

```
Usage: dida tag delete [options]

删除标签

Options:
  --name <name>  标签 name
  --scope <n>    0=删除标签并从全部可访问任务移除（默认）；1=仅从非共享任务移除标签（保留标签记录） (default: "0")
  -h, --help     display help for command
```

### `dida task get`

```
Usage: dida task get [options] <projectId> <taskId>

按清单与任务 ID 获取任务

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida task create`

```
Usage: dida task create [options]

创建任务

Options:
  --title <title>         任务标题
  --project <projectId>   清单 ID
  --parent-id <parentId>  父任务 ID（传 null/none/空表示无父任务）
  --content <content>     任务内容
  --desc <desc>           清单描述
  --all-day               全天任务
  --start-date <date>     开始时间（yyyy-MM-ddTHH:mm:ssZ）
  --due-date <date>       截止时间（yyyy-MM-ddTHH:mm:ssZ）
  --time-zone <tz>        时区
  --reminders <triggers>  提醒触发器（逗号分隔）
  --repeat <rule>         重复规则（RRULE 格式）
  --repeat-from <mode>    重复起算：0=按原截止日期，1=按完成日，2=按日历默认（需同时有 --repeat）
  --priority <n>          优先级：0=无，1=低，3=中，5=高
  --sort-order <n>        排序值
  --items <json|csv>      子任务：JSON 数组或逗号分隔标题
  --tags <tags>           任务标签（逗号分隔）
  --json                  以 JSON 输出
  -h, --help              display help for command
```

### `dida task update`

```
Usage: dida task update [options] <taskId>

更新任务

Options:
  --id <id>                       任务 ID（body 中必填）
  --project <projectId>           清单 ID
  --parent-id <parentId>          父任务 ID（传 "null" 或 "none" 可取消父子关联）
  --estimated-duration <seconds>  预计专注时长（秒）
  --estimated-pomo <count>        预计番茄数（0-60）
  --title <title>                 任务标题
  --content <content>             任务内容
  --desc <desc>                   清单描述
  --all-day                       全天任务
  --start-date <date>             开始时间（yyyy-MM-ddTHH:mm:ssZ；传 null/none 可清除）
  --due-date <date>               截止时间（yyyy-MM-ddTHH:mm:ssZ；传 null/none 可清除）
  --time-zone <tz>                时区
  --reminders <triggers>          提醒触发器（逗号分隔）
  --repeat <rule>                 重复规则（RRULE 格式）
  --repeat-from <mode>            重复起算：0=按原截止日期，1=按完成日，2=按日历默认（需同时有重复规则）
  --priority <n>                  优先级：0=无，1=低，3=中，5=高
  --sort-order <n>                排序值
  --status <n>                    状态：-1=已放弃，0=未完成，2=已完成（负数请用 --status=-1）
  --completed-time <date>         完成时间（yyyy-MM-ddTHH:mm:ssZ；仅已关闭任务可改，不可清除）
  --items <json|csv>              子任务：JSON 数组或逗号分隔标题
  --tags <tags>                   任务标签（逗号分隔）
  --json                          以 JSON 输出
  -h, --help                      display help for command
```

### `dida task complete`

```
Usage: dida task complete [options] <projectId> <taskId>

完成任务

Options:
  -h, --help  display help for command
```

### `dida task complete-batch`

```
Usage: dida task complete-batch [options]

批量完成同一清单下的任务（最多 50 个；超出截断并警告；省略 --project 时用 inbox）

Options:
  --project <projectId>  清单 ID（省略则用收件箱）
  --tasks <ids>          任务 ID（逗号分隔；超过 50 个时截断前 50）
  --json                 以 JSON 输出
  -h, --help             display help for command
```

### `dida task delete`

```
Usage: dida task delete [options] <projectId> <taskId>

删除任务

Options:
  -h, --help  display help for command
```

### `dida task move`

```
Usage: dida task move [options]

在清单间移动任务

Options:
  --from <projectId...>  源清单 ID（可多次指定）
  --to <projectId...>    目标清单 ID（可多次指定）
  --task <taskId...>     要移动的任务 ID（可多次指定）
  --json                 以 JSON 输出
  -h, --help             display help for command
```

### `dida task assign`

```
Usage: dida task assign [options]

将任务分配给清单成员

Options:
  --project <projectId>  清单 ID
  --task <taskId>        任务 ID
  --assignee <username>  成员 username（见 project members）
  --json                 以 JSON 输出
  -h, --help             display help for command
```

### `dida task unassign`

```
Usage: dida task unassign [options]

取消任务分配

Options:
  --project <projectId>  清单 ID
  --task <taskId>        任务 ID
  --json                 以 JSON 输出
  -h, --help             display help for command
```

### `dida task completed`

```
Usage: dida task completed [options]

列出已完成任务

Options:
  --projects <ids>     清单 ID（逗号分隔）
  --start-date <date>  开始时间过滤（yyyy-MM-ddTHH:mm:ssZ）
  --end-date <date>    结束时间过滤（yyyy-MM-ddTHH:mm:ssZ）
  --json               以 JSON 输出
  -h, --help           display help for command
```

### `dida task filter`

```
Usage: dida task filter [options]

按高级条件筛选任务

Options:
  --projects <ids>     清单 ID（逗号分隔）
  --start-date <date>  按截止时间（dueDate）下限过滤
  --end-date <date>    按截止时间（dueDate）上限过滤
  --priority <levels>  优先级（逗号分隔：0,1,3,5）
  --tag <tags>         标签（逗号分隔）
  --kind <kinds>       任务类型（逗号分隔：TEXT,NOTE,CHECKLIST）
  --status <codes>     状态（逗号分隔：-1=已放弃，0=未完成，2=已完成；含负数请用 --status=-1,0）
  --json               以 JSON 输出
  -h, --help           display help for command
```

### `dida task search`

```
Usage: dida task search [options] [keywords]

按关键词与条件搜索任务

Options:
  --projects <ids>   清单 ID（逗号分隔）
  --tags <tags>      标签（逗号分隔）
  --status <codes>   状态（逗号分隔：-1=已放弃，0=未完成，2=已完成；含负数请用 --status=-1,0）
  --due-from <date>  截止时间下限（yyyy-MM-ddTHH:mm:ssZ）
  --due-to <date>    截止时间上限（yyyy-MM-ddTHH:mm:ssZ）
  --json             以 JSON 输出
  -h, --help         display help for command
```

### `dida task comment`

```
Usage: dida task comment [options] [command]

任务评论

Options:
  -h, --help                               display help for command

Commands:
  list [options] <projectId> <taskId>      列出任务评论
  add [options] <projectId> <taskId>       添加任务评论
  delete <projectId> <taskId> <commentId>  删除任务评论
  help [command]                           display help for command
```

### `dida task comment list`

```
Usage: dida task comment list [options] <projectId> <taskId>

列出任务评论

Options:
  --json      以 JSON 输出
  -h, --help  display help for command
```

### `dida task comment add`

```
Usage: dida task comment add [options] <projectId> <taskId>

添加任务评论

Options:
  --title <title>  评论内容
  --json           以 JSON 输出
  -h, --help       display help for command
```

### `dida task comment delete`

```
Usage: dida task comment delete [options] <projectId> <taskId> <commentId>

删除任务评论

Options:
  -h, --help  display help for command
```

