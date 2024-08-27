set dotenv-load

# 你可以在项目根目录创建`.env`文件，写入`PYTHON = "./.venv/Scripts/python.exe"`等。
# 这样能跳过 poetry 使用虚拟环境，稍快一些。
python := env_var_or_default("PYTHON", "python")

is_dev := if env_var_or_default("DJANGO_PRODUCTION", "") == "" {
    "true"
} else {
    "false"
}

poetry_install_additional_args := if env_var_or_default("CI", "") == "" {
    ""
} else {
    "--sync"
}

src_dir := "contest"


# 列出可用任务
@default:
    just --list

# 调用 Django 的 manage.py
[private]
manage *ARGS:
    {{ python }} {{ src_dir }}/manage.py {{ ARGS }}

# 启动 Django 服务器
serve: (manage "runserver")

# 运行 Python 交互解释器，可操作数据库
shell: (manage "shell")

# 检查类型
[private]
mypy:
    {{ python }} -m mypy .

# 运行测试
[private]
test: (manage "test" "quiz")

# 检查所有
check-all: mypy test (manage "check") (manage "makemigrations" "--check")

# （部署）检查
check-deploy: && test (manage "check" "--deploy")
    @echo \$DJANGO_PRODUCTION: {{ env_var("DJANGO_PRODUCTION") }}

# 更新依赖
[private]
update-dependencies:
    poetry install --no-root {{ if is_dev == "false" { "--without dev" } else { "" } }} {{ poetry_install_additional_args }}
    {{ if is_dev == "true" { "pnpm --dir " + src_dir + "/theme/static_src/ install" } else { "" } }}
    {{ if is_dev == "true" { "pnpm --dir " + src_dir + "/js/static_src/ install" } else { "" } }}

# 更新依赖、数据库等（拉取他人提交后建议运行）
update: update-dependencies (manage "migrate")

# 监视 theme 并随时构建
watch-theme: (manage "tailwind start")

# 构建 theme
build-theme: (manage "tailwind build")

# 监视 js 并随时构建
watch-js:
    pnpm --dir {{ src_dir }}/js/static_src/ run watch

# 构建 js
build-js:
    pnpm --dir {{ src_dir }}/js/static_src/ run build

# celery
task-beat:
    cd {{ src_dir }} ; celery -A contest beat -l info

task-worker:
    cd {{ src_dir }} ; celery -A contest worker -P eventlet -l info
