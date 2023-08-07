# 开发指南

这里介绍概况，技术细节请参考[`doc/`](./doc/)。

## 开始

> **Note**
>
> 还可参考 [GitHub Actions](./.github/workflows/check.yml)。

### ⚒️ 安装工具

#### [Poetry][poetry]

- **功能**：本项目使用 [![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)][poetry] 管理 python 包。

  > 例如`poetry shell`可在终端直接使用虚拟环境。

- **安装方法**：请参阅 [Introduction | Documentation | Poetry](https://python-poetry.org/docs/#installation)。

- **配置**

  完成安装后，建议您选择[将虚拟环境放在项目中](https://python-poetry.org/docs/configuration/#virtualenvsin-project)：

  ```shell
  $ poetry config virtualenvs.in-project true
  ```

  > 原因：这样`poetry install`时会在项目所在文件夹创建`.venv/`，比`C:/Users/…/AppData/Local/pypoetry/Cache/…`或`~/.cache/pypoetry/…`更明显。

#### [Just][just]

- **功能**：本项目源代码不在根目录，有许多命令执行时有 tricks。因此建议安装 [just][]，用 just 调用。

  > 例如，运行 [mypy][] 时，必须使用正确配置在正确的位置运行。

  ```shell
  $ just --list  # 列出可用任务
  ```

- **安装方法（Unix）**

  建议参考 [Packages - Just Programmer's Manual](https://just.systems/man/en/chapter_4.html)，使用包管理器安装。

- **安装方法（Windows）**

  [下载编译好的可执行文件](https://github.com/casey/just/releases)，解压出`just.exe`，放到`$PATH`环境变量包含的任意地方。另外也可用包管理器 [scoop][] 安装：

  ```powershell
  > scoop install just
  ```

  在 Windows 上，除了 just，您还需要[选个 shell](https://just.systems/man/en/chapter_59.html)。至少有下面几种选择。

  - 将`C:/Program Files/Git/bin/`添加到`$PATH`环境变量，使用 Git for Windows 附带的 Git Bash（`sh.exe`）。

  - 也使用 Git Bash，但不用环境变量，而用 [scoop][] 包装：创建`~/scoop/shims/sh.shim`，写入`path = "C:/Program Files/Git/usr/sh.exe"`。

  - 编辑项目根目录的`justfile`，使用 Command Prompt 或 PowerShell。

    ```just
    # 在 justfile 开头加上以下任意一行
    set shell := ["cmd.exe", "/c"]
    set shell := ["powershell.exe", "-c"]
    ```

  > **Note**
  >
  > `C:/Program Files/Git/`指 Git 的安装目录。
  >
  > 另外注意是`…/Git/bin/`，而非`…/Git/usr/bin/`。

  > **Note**
  >
  > 可用[`--shell`](https://just.systems/man/en/chapter_59.html?highlight=--shell)临时测试，例如：
  >
  > ```shell
  > $ just --shell 'C:/Program Files/Git/usr/bin/bash.exe' …
  > ```

- **配置**

  如果需控制 just 使用哪个 python，请在项目根目录创建`.env`文件，设置`PYTHON`变量。下面是一些例子。

  ```toml
  # 使用项目中的虚拟环境
  PYTHON = "./.venv/Scripts/python.exe"

  # 使用 poetry 缓存中的环境
  PYTHON = "C:/Users/bjalp/AppData/Local/pypoetry/Cache/virtualenvs/…/python.exe"

  # 直接调用 poetry（万能，但比较慢）
  PYTHON = "poetry run python"
  ```

  > **Note**
  >
  > `poetry install`创建虚拟环境后，可用`poetry env info`查看“Executable”的位置。

#### [Pnpm][]

- **功能**：构建前端 CSS 和 JavaScript。

- **安装方法**

  1. 前往 [Node.js][nodejs] 网站，下载并安装 v18 LTS。（安装结束后会提示安装 choco，可取消勾选）

  2. 使用 corepack 安装 [pnpm][]。

     ```shell
     $ corepack enable
     $ corepack prepare pnpm@latest --activate
     ```

  > **Note**
  >
  > 也可尝试 [Installation | pnpm](https://pnpm.io/installation) 介绍的其它方法。

### 👢 安装包

初次使用时，需要安装项目依赖的包并创建数据库：

```shell
$ just update
```

以后拉取他人提交后，如果他人更新了依赖或更改了数据模型，你可能无法继续开发，此时也请`just update`。

### 🏃‍♀️ 启动服务器

1. 构建前端。

   ```shell
   $ just build-js build-theme
   ```

   > **Note**
   >
   > 如果你想更改前端代码，可`just watch-js`、`just watch-theme`来自动重新构建。

2. 启动 Django 服务器。

   ```shell
   $ just serve
   ```

3. 访问 [localhost:8000/quiz/](http://localhost:8000/quiz/)，用户名、密码请咨询他人。

### ✅ 检查

- **代码质量**

  ```shell
  $ just check-all
  ```

  这会检查类型、运行测试等。

- **格式**（可选）

  本项目配置了 [pre-commit][]，可自动格式化代码、检查错别字等。

  如果你想使用它，那么可用 pip 或 [pipx][] 安装 pre-commit，然后运行`pre-commit install`。此后提交到仓库时会自动检查格式。

  > **Note**
  >
  > `git commit --no-verify`可绕过 pre-commit。

## VS Code

### 任务

部分 just 命令配备了 problem matcher。<kbd>Ctrl</kbd>+<kbd>P</kbd>，输入`task`及空格，按提示操作可运行。

### Django 魔法

VS Code 默认的 [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) 无法识别很多 Django 魔法（如`*_set`）。可考虑禁用之，代以 [Matan Gover 的 Mypy](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)。这需要你在工作区设置`mypy.dmypyExecutable`，目前的设置仅适用于 Windows。

[just]: https://just.systems
[mypy]: https://mypy.readthedocs.io
[nodejs]: https://nodejs.org
[pipx]: https://pypa.github.io/pipx/
[pnpm]: https://pnpm.io/
[poetry]: https://python-poetry.org
[pre-commit]: https://pre-commit.com/
[scoop]: https://scoop.sh
