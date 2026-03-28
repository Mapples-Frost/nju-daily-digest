# 南大消息与大学生竞赛每日汇总项目

这是一个基于 Python 3.11+ 的可运行项目，用于每天自动抓取：

- 南京大学官网及公开页面中的新闻、通知、公告、活动、比赛、学工、教务、招生就业、科研、讲座、院系动态等信息
- 互联网上与大学生竞赛、创新创业、科研申报、挑战杯、互联网+、数学建模、英语竞赛、程序设计竞赛、电子设计竞赛、创业比赛、征文、志愿活动、实践活动等相关的公开信息

系统会对抓取结果做去重、分类、摘要整理，并按天汇总为 HTML 邮件发送到指定邮箱。

## 一、项目结构

```text
project/
  app.py
  scheduler.py
  config.py
  requirements.txt
  README.md
  .env.example
  data/
  logs/
  crawlers/
    __init__.py
    base.py
    nju_crawler.py
    competition_crawler.py
  services/
    __init__.py
    collector.py
    deduplicator.py
    classifier.py
    summarizer.py
    mailer.py
    storage.py
  utils/
    __init__.py
    logger.py
    time_utils.py
    text_utils.py
    url_utils.py
  tests/
    test_dedup.py
    test_classifier.py
    test_mailer.py
    test_url_utils.py
```

## 二、功能说明

### 1. 抓取能力

- 支持南京大学多来源页面抓取并合并
- 支持竞赛类网站列表配置
- 支持 RSS 抓取，如果来源配置了 `rss_url`
- 自动补全相对链接
- 自动提取标题、链接、发布时间、来源、摘要、命中关键词
- 对单站抓取失败进行容错，不会中断整次任务
- 控制请求频率，并尝试读取 `robots.txt`

### 2. 数据处理

- 同链接去重
- 相似标题去重
- 自动分类
- 自动生成简短摘要
- SQLite 本地持久化，避免重复发送
- 邮件发送失败时保留未发送状态，下一次会继续尝试发送

### 3. 邮件推送

- 每日定时执行
- 生成 HTML 邮件
- 当天没有新增内容时，也会发送“今日无新增内容”
- SMTP 配置全部从 `.env` 读取

## 三、安装依赖

建议使用 Python 3.11 或更高版本。

### Windows / Linux 通用

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux / macOS:

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

## 四、配置 `.env`

先复制配置模板：

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Linux / macOS:

```bash
cp .env.example .env
```

然后重点修改以下字段：

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_TO`
- `SCHEDULER_TIME`
- `NJU_SOURCES_JSON`
- `COMPETITION_SOURCES_JSON`

注意：

- 邮箱账号和 SMTP 密码不要写死在代码里，必须放在 `.env`
- `SMTP_PASSWORD` 对 QQ 邮箱来说通常不是登录密码，而是 SMTP 授权码
- `NJU_SOURCES_JSON` 和 `COMPETITION_SOURCES_JSON` 是 JSON 数组字符串，可按需增删站点

## 五、如何开启 QQ 邮箱 SMTP

如果你使用 QQ 邮箱：

1. 登录 QQ 邮箱网页端
2. 进入“设置”
3. 找到“账户”或“POP3/IMAP/SMTP 服务”
4. 开启 SMTP 服务
5. 按提示生成授权码
6. 将授权码填入 `.env` 的 `SMTP_PASSWORD`

常见配置：

- `SMTP_HOST=smtp.qq.com`
- `SMTP_PORT=465`
- `SMTP_USE_SSL=true`
- `SMTP_USE_TLS=false`

## 六、运行方式

### 1. 手动执行一次

```bash
python app.py
```

### 2. 启动定时任务

```bash
python scheduler.py
```

默认每天 `08:00` 执行一次，可通过 `.env` 中的 `SCHEDULER_TIME` 修改。

## 七、本地测试

运行单元测试：

```bash
python -m unittest discover -s tests
```

建议先执行一次手动任务确认抓取和邮件配置：

```bash
python app.py
```

日志默认输出到：

- `logs/app.log`

SQLite 数据库默认保存在：

- `data/digest.db`

## 八、部署说明

### 1. Windows 部署

可以直接使用以下两种方式：

- 保持 `python scheduler.py` 常驻运行
- 使用 Windows Task Scheduler 定时执行 `python app.py`

#### Windows Task Scheduler 示例

1. 打开“任务计划程序”
2. 创建基本任务
3. 触发器选择“每天”
4. 设置执行时间，例如早上 8:00
5. 操作选择“启动程序”
6. 程序填写 Python 可执行文件路径
7. 参数填写：`app.py`
8. 起始于填写项目根目录

如果使用虚拟环境，程序路径改成：

```text
项目目录\.venv\Scripts\python.exe
```

### 2. Linux 部署

也有两种常见方式：

- 使用 `python scheduler.py` 配合 `screen`、`tmux` 或 systemd 常驻运行
- 使用 `cron` 每天执行一次 `python app.py`

#### cron 示例

```cron
0 8 * * * /path/to/project/.venv/bin/python /path/to/project/app.py
```

## 九、关于系统计划任务与内置调度的选择

### 方式 A：使用本项目内置调度

执行：

```bash
python scheduler.py
```

优点：

- 配置简单
- 代码集中

缺点：

- 需要进程持续运行

### 方式 B：使用系统计划任务

执行：

```bash
python app.py
```

让系统定时调起该脚本。

优点：

- 更稳
- 资源占用更低
- 更适合服务器部署

建议正式环境优先使用 Windows Task Scheduler 或 cron 来触发 `python app.py`。

## 十、可配置站点说明

由于不同网站结构和稳定性可能变化，本项目将站点列表放入 `.env` 配置中，便于后续调整。

如果某个站点：

- 无法稳定访问
- 页面结构变化较大
- TLS/证书兼容性特殊

你可以直接修改：

- `NJU_SOURCES_JSON`
- `COMPETITION_SOURCES_JSON`

每个来源可配置的常见字段包括：

- `name`: 来源名称
- `url`: 抓取入口页
- `source`: 邮件中展示的来源名
- `source_type`: `nju` 或 `competition`
- `include_keywords`: 过滤关键词
- `seed_keywords`: 站点固有关键词
- `category_hint`: 分类提示
- `always_relevant`: 是否把该站视为强相关站点
- `max_items`: 每个来源最多保留多少条
- `detail_fetch_limit`: 每个来源最多补抓多少条详情页
- `rss_url`: 如果有 RSS，可额外配置

## 十一、注意事项

- 项目默认优先保证可运行，再兼顾复杂度
- 对没有标准时间字段的页面，会尝试从周边文本、URL 中提取日期
- 如果仍然无法提取，会使用“未提取到，按抓取时间归档”的展示方式
- 某些网站可能会因为证书、反爬、网关或页面结构变化导致抓取失败，这属于预期容错场景，程序会记录日志并继续执行其他站点
- 建议先小范围试运行，确认邮件发送成功后再长期部署
