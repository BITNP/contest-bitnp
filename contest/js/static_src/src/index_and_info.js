/**
 * - 发生自动提交时通知参赛者
 * - 转到 quiz:contest 前强调竞赛规则
 */
import Swal from 'sweetalert2'

import { get_data } from './util'

/** @type {"not taking" | "taking contest" | "deadline passed" | ""} */
const status = get_data('status')

if (status === 'deadline passed') {
    Swal.fire({
        title: '上次作答已超时',
        text: '截止前作答部分已尽量保存。建议下次早些提交。',
        icon: 'warning',
        confirmButtonText: '好'
    })
}
if (status !== 'taking contest') {
    // 为了这段程序不加载或还没加载时也正常，采用`<a>`而非`<button>`。

    /** @type {HTMLAnchorElement | null} */
    const anchor = document.querySelector('a#url-quiz-contest')
    // 如果允许答题（没答完所有机会）
    if (anchor !== null) {
        anchor.addEventListener('click', async (event) => {
            // 后续请求异步，必须先阻止
            event.preventDefault()

            const result = await Swal.fire({
                title: '确定前往答题？',
                text: '答题次数有限，发卷后计时无法暂停。',
                icon: 'question',
                confirmButtonText: anchor.textContent,
                showCancelButton: true,
                cancelButtonText: '取消',
                showCloseButton: true,
            })
            if (result.isConfirmed) {
                window.location.assign(anchor.href)
            }
        })
    }
}
