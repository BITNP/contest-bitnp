import Swal from 'sweetalert2'

import { get_data } from "./util"

/** 时间允差，毫秒 */
const TIME_MARGIN = 10 * 1e3

const update_url = get_data("update-url")
const deadline = Date.parse(get_data("deadline"))
const deadline_duration_seconds = get_data("deadline-duration")

//! 作答

const form = document.querySelector("form")
const filed_sets = Array.from(form.querySelectorAll('fieldset'))
const inputs = filed_sets.map(set => Array.from(set.querySelectorAll('input')))
/** @type {HTMLDivElement} */
const contest_bar = document.querySelector('div#contest-progress-bar')
/** @type {HTMLSpanElement} */
const contest_text = document.querySelector('span#contest-progress-text')

function display_contest_progress () {
    const n_completed = inputs.filter(set => set.some(i => i.checked)).length

    contest_bar.style.width = `${100 * n_completed / inputs.length}%`
    contest_text.textContent = inputs.length - n_completed
}

async function update_contest_progress () {
    const response = await fetch(update_url, {
        method: 'POST',
        body: new FormData(form)
    })
    if (!response.ok && response.status == 403) {
        // 锁定表单
        filed_sets.forEach(set => set.disabled = true)

        // 提示提交
        const result = await Swal.fire({
            title: '此次作答已超时',
            html: '<p>无法再更改答卷，但您还可以查看自己的答卷。</p><p>（截止前作答部分已尽量保存）</p>',
            icon: 'warning',
            confirmButtonText: '现在提交',
            showCancelButton: true,
            cancelButtonText: '再看看答卷',
            showCloseButton: true,
        })
        if (result.isConfirmed) {
            form.submit()
        }
    }
}

function update_contest_progress_periodically () {
    // 若之前同步时仍有时间，则继续定期同步
    if (!filed_sets[0].disabled) {
        setTimeout(update_contest_progress_periodically, TIME_MARGIN / 16)
    }
    return update_contest_progress()
}

// 浏览器可能缓存之前答卷，因此进入页面后立即更新进度条
display_contest_progress()

// 每次修改时更新
form.addEventListener('input', () => {
    update_contest_progress()
    display_contest_progress()
})

// 将近截止时定期更新
setTimeout(update_contest_progress_periodically, deadline - Date.now() - TIME_MARGIN)

//! 时间

/** 时间进度 */
class TimeProgress {
    constructor() {
        /** @type {HTMLDivElement} */
        this.bar = document.querySelector('div#time-progress-bar')
        /** @type {HTMLSpanElement} */
        this.text = document.querySelector('span#time-progress-text')
    }

    /**
     * @returns {number} 剩余秒数
     */
    get seconds_left () {
        // timestamps are in milliseconds.
        return (deadline - Date.now()) / 1e3
    }

    /**
     * @returns {number} 时间进度，0 代表发卷，1 代表截止
     */
    get progress () {
        return 1 - this.seconds_left / deadline_duration_seconds
    }

    /**
     * 更新进度条
     */
    update () {
        if (this.progress < 1) {
            this.bar.style.width = `${100 * this.progress}%`

            if (this.seconds_left > 100) {
                this.text.textContent = `${Math.round(this.seconds_left / 60)}分`
                setTimeout(() => { this.update() }, 1000)
            } else {
                this.text.textContent = `约${Math.round(this.seconds_left)}秒`
                setTimeout(() => { this.update() }, 100)
            }
        } else {
            this.bar.style.width = `100%`
            this.text.textContent = '0秒'
        }

        if (this.progress > 0.85) {
            this.bar.classList.add('time-progress-severe')
        }
    }
}
const time_progress = new TimeProgress()
time_progress.update()
