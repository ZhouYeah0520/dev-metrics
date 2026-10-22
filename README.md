# Dev Metrics

一个零第三方依赖的研发效能采集与看板示例。Python CLI 采集 Git commit、流水线标识、构建/测试耗时、测试通过率和环境指纹，SQLite 用 `(commit_sha, pipeline_id)` 主键保证重复上报幂等，静态 HTML 看板展示最近运行。

## 本地运行

要求 Python 3.10+ 和 Git。

```powershell
cd dev-metrics
$env:PYTHONPATH='src'
python -m unittest discover -s tests -v
python -m dev_metrics collect --pipeline-id local-demo --build-seconds 12.4 --test-seconds 2.1 --tests-passed 8 --tests-total 8
python -m dev_metrics dashboard --output dashboard.html
```

打开生成的 `dashboard.html` 查看数据。默认数据库为 `metrics.db`，可通过 `--db` 指定。CI 环境默认从 `GITHUB_SHA`、`GITHUB_RUN_ID` 或 `CI_COMMIT_SHA`、`CI_PIPELINE_ID` 读取提交和流水线标识。

## CI

- `.github/workflows/ci.yml` 在 push 和 pull request 上运行单元测试、采集一次 CI 指标并保存 HTML 看板为 artifact。
- `.gitlab-ci.yml` 提供等价的测试与指标采集 job。
- `Dockerfile` 提供固定 Python 基础镜像的本地运行环境。环境指纹覆盖 Python 版本、系统平台、Git 版本和依赖清单哈希。

CI runner 需要 checkout 当前提交并提供 Git。Docker 本地镜像构建需安装并启动 Docker Engine。CLI 接收由流水线阶段测得的构建/测试耗时；当前 GitHub workflow 用固定演示值写入一条记录，示例不包含应用部署。

## 指标口径

`test_pass_rate = tests_passed / tests_total`，无测试时为 `null`；每次运行按 commit 和 pipeline id 唯一。重新执行同一 pipeline 会覆盖同一条记录。SQLite 文件是本地演示存储，GitHub artifact 是短期结果传递方式，不是团队级持久化服务。样例未连接 GitLab/GitHub API，也不声称已有团队数据或效率提升结果。
