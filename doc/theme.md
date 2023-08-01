# Theme

在模板中写 [Tailwind CSS](https://tailwindcss.com/)，利用 [django-tailwind](https://pypi.org/project/django-tailwind/) 生成 CSS（`contest/theme/`的`static/css/`，这是 Django 项目的一个应用），然后通过模板中的`{% tailwind_css %}`引入。

## 开发

### `NPM_BIN_PATH`

构建 Tailwind CSS 需要 Node.js 及 npm 或 [pnpm](https://pnpm.io/)。

仓库中设置会用`$PATH`上的`pnpm.CMD`；若有其它需求，请更改[`settings.py`](../contest/contest/settings.py)中的`NPM_BIN_PATH`。

### 自动重新构建

开发时可以监视源代码，修改时自动重新构建。

`just serve`会监视一般源代码，但对 theme 不知情；`just watch-theme`会监视模板生成 CSS，进而让浏览器页面刷新。因此，开发时需要两个进程同时工作。

## 示例

以下是[初始化 django-tailwind](https://django-tailwind.readthedocs.io/en/latest/installation.html) 时生成的`base.html`。

```html
{% load static tailwind_tags %}
<!DOCTYPE html>
<html lang="en">
	<head>
    <title>Django Tailwind</title>
		<meta charset="UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<meta http-equiv="X-UA-Compatible" content="ie=edge">
		{% tailwind_css %}
	</head>

	<body class="bg-gray-50 font-serif leading-normal tracking-normal">
		<div class="container mx-auto">
			<section class="flex items-center justify-center h-screen">
				<h1 class="text-5xl">Django + Tailwind = ❤️</h1>
			</section>
		</div>
	</body>
</html>
```
