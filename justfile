set dotenv-load

# 你可以在项目根目录创建`.env`文件，写入`PYTHON = "./.venv/Scripts/python.exe"`等。
# 这样能跳过 poetry 使用虚拟环境，稍快一些。
python := env_var_or_default("PYTHON", "python")

src_dir := "contest"


# 列出可用任务
@default:
    just --list

# 调用 Django 的 manage.py
manage *ARGS:
    {{ python }} {{ src_dir }}/manage.py {{ ARGS }}

# 启动 Django 服务器
serve: (manage "runserver")

# 检查类型
mypy:
    {{ python }} -m mypy .

# 运行测试
test: (manage "test" "quiz")

# 检查所有
check-all: mypy test (manage "check")

# 更新依赖、数据库等（拉取他人提交后建议运行）
update: && (manage "migrate")
    poetry install

# 监视 theme 并随时构建
watch-theme: (manage "tailwind start")

# 构建 theme
build-theme: (manage "tailwind build")
