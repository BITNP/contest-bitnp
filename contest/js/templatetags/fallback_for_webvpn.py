"""针对 WebVPN 的备用方案"""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

_fallback_js = r"""
if (window.location.hostname === 'webvpn.bit.edu.cn') {
    window.addEventListener('error', async (event) => {
        if (event.error instanceof SyntaxError && event.error.message === "import declarations may only appear at top level of a module") {
            event.preventDefault()

            const source = new URL(event.filename)
            source.searchParams.delete('vpn-7')
            source.pathname = source.pathname.replace(/\.js$/, '.no-split.js')

            const script = document.createElement('script')
            script.src = source.href
            document.body.appendChild(script)
        }
    })
}
"""  # noqa: E501


@register.simple_tag
def fallback_for_webvpn() -> str:
    """一个`<script>`元素，实现用 WebVPN 访问时，`*.js`→`*.no-split.js`

    - 直接访问时，本元素的 JavaScript 不合法
      （Uncaught SyntaxError: expected expression, got '}'），
      不会执行。

    - 用 WebVPN 访问时，本元素的代码会监听页面解析，
      遇到无法加载的 ESM 时，会重新加载`*.no-split.js`。
    """
    # 采用`<script>`，保证在`<script type='module'>`之前运行。
    # JavaScript 代码用`}))`、`(({`包裹，抵消`vpn_eval`的影响，
    # 不然`window.location`还是原来的。
    return format_html(
        "<script>}})){}(({{</script>",
        mark_safe(_fallback_js),  # noqa: S308 suspicious-mark-safe-usage
    )
    # 内容是自己产生的，目的就是运行
