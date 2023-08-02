# JavaScript

在`contest/js/`的`static_src/`编写 JavaScript，利用 [webpack](https://webpack.js.org/) 等打包（到`static/`），在模板中按如下方式引用。

```html
<script type='module' src="{% static 'js/dist/[name].js' %}"></script>
```

> **Note**
> `type='module'`会自动[`defer`](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script#attributes)。

## 获取后端的数据

1. 视图将上下文传入模板。

2. 模板将数据用 [`json_script`](https://docs.djangoproject.com/en/4.2/ref/templates/builtins/#std-templatefilter-json_script) 蕴含于 HTML 中。

   ```html
   {{ your_data | json_script:"data:your_key" }}
   ```

3. 在 JavaScript 中获取。

   ```javascript
   import { get_data } from "./util"

   const your_data = get_data("your_key")
   ```


> **Note**
> 如果`your_data`不存在，`json_script`会按`""`处理。

## 开发

- 需要 [pnpm](https://pnpm.io/)。
- 类似 [theme](./theme.md#自动重新构建)，可`just watch-js`、`just build-js`。
