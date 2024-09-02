/**
 * - 发生自动提交时通知参赛者
 * - 转到 quiz:contest 前强调竞赛规则
 */
import Swal from 'sweetalert2'

import { get_data } from './util'

/** @type {"not taking" | "taking contest" | "deadline passed" | ""} */
const status = get_data('status')

/** @type {number} */
const traffic = get_data('traffic')
/** 人多时建议等待的秒数 */
const TIME_TO_WAIT_IF_JAMMED = 30 // s

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
            // 如果系统仍有能力，正常答题；不然建议稍后参与
            // 为避免进一步向后端施压，这部分逻辑在前端实现，并尽可能拖延时间
            if (traffic < 0.90) {
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
            } else {
                let interval
                await Swal.fire({
                    title: '非常抱歉',
                    html: '<p>当前答题人数已达上限。</p><p>请等<strong></strong>秒再重新参与。</p>',
                    icon: 'warning',
                    timer: TIME_TO_WAIT_IF_JAMMED * 1000, // ms
                    timerProgressBar: true,
                    didOpen: () => {
                        Swal.showLoading()
                        const tick = Swal.getPopup().querySelector('strong')
                        interval = setInterval(() => {
                            tick.textContent = `${(Swal.getTimerLeft() / 1000).toFixed()}`
                        }, 500)
                    },
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    willClose: () => clearInterval(interval),
                })

                window.location.reload()
            }
        })
    }
}
