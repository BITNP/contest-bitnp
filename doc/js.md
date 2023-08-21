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

## 适配 [WebVPN](https://www.wrdtech.com/content/content.php?p=2_30_203)

### ESM 支持有限

WebVPN 会修改原本的文件，用`vpn_eval`包裹，而`import`、`export`必须在顶层，导致无法[分割代码](https://rollupjs.org/tutorial/#code-splitting)。

```javascript
vpn_eval((function(){
import{d as e}from"./_rollupPluginBabelHelpers-b026cde4.js";…
}
).toString().slice(12, -2),"");
```

```javascript
Uncaught SyntaxError: import declarations may only appear at top level of a module
```

于是采用两套代码：

- 直接访问时（包括开发时），使用 ESM 并分割代码。
- 用 WebVPN 访问时，另准备一套`*.no-split.js`，不分割代码，每个入口单独构建。详见[`static_src/rollup.config.prod.mjs`](../contest/js/static_src/rollup.config.prod.mjs)。

在模板中只写直接访问的代码，另外添加`{% fallback_for_webvpn %}`来实现切换。详见[`templatetags/fallback_for_webvpn.py`](../contest/js/templatetags/fallback_for_webvpn.py)。

### URL 中`.` ≠ `/`

```html
<script id="data:update-url" type="application/json">"/contest/update/"</script>
```

一般不必担心，因为 WebVPN 会修改 Fetch 之类的 API，把`/`映射到 WebVPN 下的 URL。
