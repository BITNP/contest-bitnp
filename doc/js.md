# JavaScript

在`contest/js/`的`static_src/`编写 JavaScript，利用 [webpack](https://webpack.js.org/) 等打包（到`static/`），在模板中按如下方式引用。

```html
<script type='module' src="{% static 'js/dist/[name].js' %}"></script>
```

## 开发

- 需要 [pnpm](https://pnpm.io/)。
- 类似 [theme](./theme.md#自动重新构建)，可`just watch-js`、`just build-js`。
