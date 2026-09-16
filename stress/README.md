# 压力测试

用 [k6](https://grafana.com/docs/k6/latest/) 对 `contest-bitnp` 进行压力测试。测试覆盖全部 HTTP API，并模拟真实学生作答流程。

## 目录

- [覆盖范围](#覆盖范围)
- [准备工作](#准备工作)
- [快速开始](#快速开始)
- [配置](#配置)
- [结果解读](#结果解读)
- [注意事项](#注意事项)

## 覆盖范围

| 场景 | 方法 | 路径 | 预期 |
| --- | --- | --- | --- |
| 首页 | GET | `/` | 200 |
| 首页（匿名） | GET | `/` | 200 |
| 登录页 | GET | `/admin/login/` | 200 |
| 登录 | POST | `/admin/login/` | 302 |
| 历史成绩 | GET | `/info/` | 200 |
| 历史成绩（匿名） | GET | `/info/` | 302 |
| 发卷 | GET | `/contest/` | 200 |
| 发卷（匿名） | GET | `/contest/` | 302 |
| 暂存答卷 | POST | `/contest/update/` | 200 |
| 未发卷即交卷 | POST | `/contest/submit/` | 403 |
| 交卷 | POST | `/contest/submit/` | 302 |
| 回顾答卷 | GET | `/contest/review/<n>/` | 200 |
| 回顾越界 | GET | `/contest/review/99/` | 404 |
| 回顾（匿名） | GET | `/contest/review/0/` | 302 |
| 登出 | POST | `/admin/logout/?next=/` | 302 |

`workflow` 场景对每名学生完整跑两轮（对应 `constants.MAX_TRIES = 2`）：发卷 → 逐题暂存（前端每次选择都会触发一次 `contest_update`）→ 交卷 → 查分 → 回顾。

> `/accounts/login/`、`/accounts/logout/` 会跳转到学校 CAS 服务器（外网），故不纳入压测。

## 准备工作

1. **安装 k6**：参考 [k6 官方文档](https://grafana.com/docs/k6/latest/set-up/install-k6/)，用包管理器或二进制安装。确认：

   ```shell
   $ k6 version
   ```

2. **启动 Redis**：`contest_update` 会把答案写入缓存，缺少 Redis 会报 500。

   ```shell
   $ redis-server
   ```

3. **准备数据库**：`just update`（安装依赖、迁移），随后用 seeder 预置数据。

## 快速开始

开发模式（带 debug toolbar，仅用于功能验证）：

```shell
$ redis-server &            # 另开终端亦可
$ just update
$ just seed-stress 200      # 创建 200 名学生 + 题库
$ just serve                # 另开终端

$ k6 run stress/contest.js
```

生产模式（推荐，关闭 debug toolbar 以获得真实性能数据；`DJANGO_DISABLE_QUIZ_OPENING_TIME_INTERVAL=1` 用于忽略竞赛开放时间）：

```shell
$ export DJANGO_PRODUCTION=1
$ export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
$ export DJANGO_DISABLE_QUIZ_OPENING_TIME_INTERVAL=1

$ just manage migrate
$ just seed-stress 200
# 另开终端，在 contest/ 目录下：
$ gunicorn -w 4 -k uvicorn.workers.UvicornWorker contest.asgi:application

$ k6 run stress/contest.js
```

> seeder 与服务器必须使用同一套环境变量，否则会写入不同的 SQLite 文件
> （开发模式为 `contest/db.sqlite3`，生产模式为 `contest/db/db.sqlite3`）。

### just 命令

```shell
$ just seed-stress 200        # 预置 200 名学生与题库
$ just stress                 # k6 run stress/contest.js
$ just stress-smoke           # 2 VU × 1 轮，快速冒烟
```

## 配置

通过 `-e KEY=VALUE` 或环境变量传入：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `BASE_URL` | `http://127.0.0.1:8000` | 目标地址 |
| `STUDENTS` | `200` | 预置学生数量，**需 ≥ 压测总迭代次数** |
| `STUDENT_PREFIX` | `stress` | 学生用户名前缀，需与 seeder `--prefix` 一致 |
| `STUDENT_PASSWORD` | `stress-password-123` | 学生密码，需与 seeder `--password` 一致 |
| `VUS` | `10` | `workflow` 场景虚拟用户数 |
| `ITERATIONS` | `1` | 每 VU 的迭代次数，总迭代数 = `VUS × ITERATIONS` |
| `ANON_VUS` | `2` | `anonymous` 场景虚拟用户数 |
| `ANON_DURATION` | `1m` | `anonymous` 场景持续时间 |
| `MAX_DURATION` | `30m` | `workflow` 场景最长时限 |

示例：50 名学生、50 VU、每人 2 轮（共 100 次迭代，需先 `just seed-stress 100`）：

```shell
$ just seed-stress 100
$ k6 run -e VUS=50 -e ITERATIONS=2 -e STUDENTS=100 \
    -e BASE_URL=http://127.0.0.1:8000 stress/contest.js
```

> 每次迭代使用一名独立学生（按 `ITERATIONS` 全局计数分配），避免答题次数冲突。

## 结果解读

- `checks`：各断言通过率，附带 `endpoint` 标签，可按接口区分。
- `http_req_duration{scenario:workflow}`：作答流程的响应时间。
- `http_req_failed`：失败请求比例。k6 默认把 4xx 也记为失败，而本脚本会刻意触发 403/404，
  因此脚本已用 `http.setResponseCallback(expectedStatuses(...))` 将其声明为预期；
  该指标此后只反映真实错误（如 500）。

阈值默认 `http_req_failed < 1%`、`checks > 99%`、`p(95) < 1000ms`，可在 `contest.js` 的 `options.thresholds` 中调整。
响应时间阈值与部署环境有关：开发用的 `runserver` + debug toolbar 下 p95 常会超过 1s，属正常现象。

导出结果：

```shell
$ k6 run --out json=stress/results/run.json stress/contest.js
```

## 注意事项

- **每题只消耗 2 次机会**：`workflow` 会完整作答两轮，用尽该学生的答题机会。每次压测前请**重新运行** `just seed-stress`，否则 `/contest/` 返回 403，`checks` 通过率下降。
- **SQLite 写入串行**：高并发下可能出现 `database is locked`（`http_req_failed` 升高）。这本身是压测发现的问题，并非脚本缺陷。要获得干净数据，可降低 VU，或改用 PostgreSQL（需自行修改 `settings.py`，超出本压测范围）。
- **仅供本地使用**：seeder 创建的学生 `is_staff=True` 且密码固定，请只在一次性/本地数据库上运行。
- **debug toolbar**：开发模式下其对 `127.0.0.1` 生效，会显著增加响应时间并插入额外请求，压测请用生产模式。
- **重置数据**：seeder 默认先删除同前缀（`stress`）账号及其答卷、草稿，可反复运行。若不想删除，加 `--keep`。
