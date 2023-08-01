/**
 * @param {string} key
 */
function get_data (key) {
    return JSON.parse(document.getElementById(`data:${key}`).textContent)
}

//! 作答

const form = document.querySelector("form")
const filed_sets = Array.from(form.querySelectorAll('fieldset'))
const inputs = filed_sets.map(set => Array.from(set.querySelectorAll('input')))
const update_url = get_data("update-url")
/** @type {HTMLDivElement} */
const contest_bar = document.querySelector('div#contest-progress-bar')
/** @type {HTMLSpanElement} */
const contest_text = document.querySelector('span#contest-progress-text')

function display_contest_progress () {
    const n_completed = inputs.filter(set => set.some(i => i.checked)).length

    contest_bar.style.width = `${100 * n_completed / inputs.length}%`
    contest_text.textContent = inputs.length - n_completed
}

display_contest_progress()

form.addEventListener('input', () => {
    // Send
    fetch(update_url, {
        method: 'POST',
        body: new FormData(form)
    }).then(response => {
        if (!response.ok && response.status == 403) {
            filed_sets.forEach(set => set.disabled = true)
        }
    })

    // Display
    display_contest_progress()
})

//! 时间

/** 时间进度 */
class TimeProgress {
    constructor() {
        this.deadline = Date.parse(get_data("deadline"))
        this.deadline_duration_seconds = get_data("deadline-duration")

        /** @type {HTMLDivElement} */
        this.bar = document.querySelector('div#time-progress-bar')
        /** @type {HTMLSpanElement} */
        this.text = document.querySelector('span#time-progress-text')
    }

    /**
     * @returns {number} 时间进度，0 代表发卷，1 代表截止
     */
    get progress () {
        // timestamps are in milliseconds.
        return 1 + (Date.now() - this.deadline) / 1e3 / this.deadline_duration_seconds
    }

    /**
     * 更新进度条
     */
    update () {
        if (this.progress < 1) {
            this.bar.style.width = `${100 * this.progress}%`

            const seconds_left = (this.deadline - Date.now()) / 1e3
            if (seconds_left > 100) {
                this.text.textContent = `${Math.round(seconds_left / 60)}分`
                setTimeout(() => { this.update() }, 1000)
            } else {
                this.text.textContent = `${Math.round(seconds_left)}秒`
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
