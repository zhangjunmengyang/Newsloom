# Newsloom 部署指南

本文档介绍如何部署 Newsloom 到不同环境。

## 目录

- [GitHub Actions 自动化](#github-actions-自动化)
- [服务器部署](#服务器部署)
- [本地定时运行](#本地定时运行)
- [环境变量配置](#环境变量配置)

---

## GitHub Actions 自动化

### 1. 配置 GitHub Secrets

在仓库设置中添加以下 Secrets:

1. 访问 `Settings` → `Secrets and variables` → `Actions`
2. 添加 `ANTHROPIC_API_KEY`:
   - Name: `ANTHROPIC_API_KEY`
   - Value: 你的 Anthropic API Key

### 2. 启用 GitHub Pages

1. 访问 `Settings` → `Pages`
2. Source 选择 `Deploy from a branch`
3. Branch 选择 `gh-pages` / `root`
4. 保存

### 3. 工作流说明

`.github/workflows/daily-report.yml` 会自动:

- **每天 UTC 0:00** (北京时间 8:00) 运行
- 抓取数据 → 过滤 → AI 分析 → 生成报告
- 提交结果到 main 分支
- 部署报告到 GitHub Pages

### 4. 手动触发

访问 `Actions` → `Daily Report Generation` → `Run workflow`

---

## 服务器部署

### 1. 克隆仓库

```bash
git clone https://github.com/zhangjunmengyang/Newsloom.git
cd Newsloom
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_api_key_here
EOF

# 加载环境变量
export $(cat .env | xargs)
```

### 4. 测试运行

```bash
python3 run.py --layers fetch,filter,generate
```

### 5. 设置 Cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每天凌晨 2 点运行）
0 2 * * * cd /path/to/Newsloom && ./scripts/run_daily.sh
```

---

## 本地定时运行

### macOS/Linux

使用 cron:

```bash
# 编辑 crontab
crontab -e

# 每天 8:00 运行
0 8 * * * cd ~/Newsloom && python3 run.py --layers fetch,filter,analyze,generate
```

### Windows

使用任务计划程序:

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天
4. 操作：启动程序
5. 程序：`python`
6. 参数：`C:\path\to\Newsloom\run.py --layers fetch,filter,analyze,generate`
7. 起始于：`C:\path\to\Newsloom`

---

## 环境变量配置

### 必需的环境变量

```bash
# Anthropic API Key (AI 分析必需)
export ANTHROPIC_API_KEY="your_key_here"
```

### 可选的环境变量

```bash
# Twitter API (如果使用 Twitter 数据源)
export TWITTER_API_KEY="your_twitter_key"
export TWITTER_API_SECRET="your_twitter_secret"

# GitHub Token (提高 API 限制)
export GITHUB_TOKEN="your_github_token"
```

### 使用 .env 文件

创建 `.env` 文件:

```bash
ANTHROPIC_API_KEY=sk-ant-xxx
TWITTER_API_KEY=xxx
GITHUB_TOKEN=ghp_xxx
```

加载方式:

```bash
# 方法 1: 手动加载
export $(cat .env | xargs)

# 方法 2: 使用 python-dotenv
pip install python-dotenv
```

---

## Docker 部署（可选）

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "run.py", "--layers", "fetch,filter,analyze,generate"]
```

### 2. 构建镜像

```bash
docker build -t newsloom .
```

### 3. 运行容器

```bash
docker run -e ANTHROPIC_API_KEY="your_key" \
           -v $(pwd)/reports:/app/reports \
           -v $(pwd)/data:/app/data \
           newsloom
```

### 4. Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  newsloom:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./reports:/app/reports
      - ./data:/app/data
```

运行:

```bash
docker-compose up
```

---

## 部署到云服务

### Vercel (静态报告)

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署 reports 目录
cd reports
vercel
```

### AWS Lambda (定时任务)

1. 打包项目: `zip -r newsloom.zip .`
2. 创建 Lambda 函数
3. 上传 zip 文件
4. 配置环境变量
5. 设置 EventBridge 定时触发

### Heroku

```bash
# 创建 Procfile
echo "worker: python3 run.py --layers fetch,filter,analyze,generate" > Procfile

# 部署
heroku create newsloom-app
heroku config:set ANTHROPIC_API_KEY=your_key
git push heroku main
```

---

## 监控和日志

### 查看日志

```bash
# GitHub Actions 日志
# 访问 Actions → 选择运行 → 查看日志

# 服务器日志
tail -f logs/run_$(date +%Y-%m-%d).log
```

### 错误通知

配置 GitHub Actions 失败通知:

```yaml
# 在 workflow 添加
- name: Notify on failure
  if: failure()
  uses: actions/github-script@v6
  with:
    script: |
      github.rest.issues.create({
        owner: context.repo.owner,
        repo: context.repo.repo,
        title: '日报生成失败',
        body: '请检查 Actions 日志'
      })
```

---

## 故障排除

### 问题: API Rate Limit

**解决方案**:
- 减少 `max_results` 配置
- 添加 GitHub Token
- 调整运行频率

### 问题: 内存不足

**解决方案**:
- 减少并行数 `parallel_workers`
- 减少批处理大小 `batch_size`
- 增加服务器内存

### 问题: 报告未生成

**检查清单**:
1. ✅ 环境变量是否配置正确
2. ✅ 依赖是否全部安装
3. ✅ 数据源是否可访问
4. ✅ 磁盘空间是否充足

---

## 最佳实践

1. **定期备份**: 备份 `data/state/` 目录
2. **监控磁盘**: 设置清理策略（保留 30 天）
3. **API 配额**: 监控 API 使用量
4. **错误通知**: 配置告警机制
5. **版本控制**: 定期更新依赖

---

## 需要帮助？

- 查看 [README.md](../README.md)
- 提交 [Issue](https://github.com/zhangjunmengyang/Newsloom/issues)
- 参考 [扩展指南](EXTENDING.md)
