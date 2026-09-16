// 国防知识竞赛 — k6 压力测试
//
// 覆盖全部 HTTP API，并模拟真实学生作答流程：
//   登录 → 历史成绩 → （未发卷时交卷应 403）→ 发卷 → 逐题暂存（前端每次 input 都会暂存）
//   → 交卷 → 查分 → 回顾 → 第二次作答 → 越界回顾 404 → 登出
//
// 认证：题库 API 均在 CAS 之后。测试通过 `ModelBackend` 从 `/admin/login/` 登录
// 预置的 is_staff 学生账号，从而无需连接学校 CAS 服务器。
//
// 用法见同目录 README.md。快速开始：
//   just seed-stress 200
//   k6 run stress/contest.js
//
// 依赖环境变量（均有默认值）：
//   BASE_URL          目标地址，默认 http://127.0.0.1:8000
//   STUDENTS          预置学生数量，需 >= 总共迭代次数，默认 200
//   STUDENT_PREFIX    学生用户名前缀，默认 stress
//   STUDENT_PASSWORD  学生密码，默认 stress-password-123
//   VUS / ITERATIONS  workflow 场景每 VU 迭代次数，默认 10 / 1
//   ANON_VUS / ANON_DURATION  anonymous 场景，默认 2 / 1m

import { check, fail, group, sleep } from 'k6'
import exec from 'k6/execution'
import http, { expectedStatuses } from 'k6/http'
import { parseHTML } from 'k6/html'

// 本脚本会刻意触发 4xx：未发卷交卷 403、回顾越界 404、匿名访问 403/302。
// k6 默认把它们算作 http_req_failed，故显式声明为“预期内”。
// 未列出的状态（如 500）仍会被计为失败——这正是我们想监控的。
http.setResponseCallback(
    expectedStatuses(200, 201, 204, 301, 302, 303, 307, 308, 400, 401, 403, 404),
)

//! 配置

const BASE = (__ENV.BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '')

const STUDENTS = Number(__ENV.STUDENTS || 200)
const PREFIX = __ENV.STUDENT_PREFIX || 'stress'
const PASSWORD = __ENV.STUDENT_PASSWORD || 'stress-password-123'

const VUS = Number(__ENV.VUS || 10)
const ITERATIONS = Number(__ENV.ITERATIONS || 1)
const ANON_VUS = Number(__ENV.ANON_VUS || 2)
const ANON_DURATION = __ENV.ANON_DURATION || '1m'

// 每份答卷题数（与 quiz.constants.N_QUESTIONS_PER_RESPONSE 一致）
const N_QUESTIONS = 20

export const options = {
    scenarios: {
    // 完整学生流程
        workflow: {
            executor: 'per-vu-iterations',
            exec: 'workflow',
            vus: VUS,
            iterations: ITERATIONS,
            maxDuration: __ENV.MAX_DURATION || '30m',
            tags: { scenario: 'workflow' },
        },
        // 匿名访问与 4xx 边界
        anonymous: {
            executor: 'constant-vus',
            exec: 'anonymous',
            vus: ANON_VUS,
            duration: ANON_DURATION,
            tags: { scenario: 'anonymous' },
        },
    },
    thresholds: {
    // SQLite 高并发写入可能触发 database is locked，必要时放宽或改用 Postgres
        http_req_failed: ['rate<0.01'],
        checks: ['rate>0.99'],
        'http_req_duration{scenario:workflow}': ['p(95)<1000'],
    },
}

//! 小工具

function pad (n) {
    return String(n).padStart(4, '0')
}

/** 读取当前会话的 csrftoken cookie（Django 允许直接用作 X-CSRFToken） */
function csrfToken () {
    const cookies = http.cookieJar().cookiesForURL(BASE)
    return cookies.csrftoken || ''
}

/** 表单编码，避免依赖 URLSearchParams */
function encodeForm (fields) {
    return Object.entries(fields)
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&')
}

/** 解析考卷页面为 { question-<id>: [choice-<id>, ...] } */
function parseQuestions (doc) {
    const questions = {}
    doc.find('input[type=radio]').toArray().forEach((el) => {
        const name = el.attr('name')
        const value = el.attr('value')
        if (!name || !value) return
        if (!questions[name]) questions[name] = []
        questions[name].push(value)
    })
    return questions
}

/** 每题随机选一个选项，模拟真实作答 */
function randomAnswers (questions) {
    const answers = {}
    for (const [question, choices] of Object.entries(questions)) {
        answers[question] = choices[Math.floor(Math.random() * choices.length)]
    }
    return answers
}

/** 登录，成功后会话 cookie 存于 VU 的 cookie jar */
function login (username) {
    http.get(`${BASE}/admin/login/`, { tags: { endpoint: 'admin_login_page' } })

    const res = http.post(
        `${BASE}/admin/login/`,
        encodeForm({
            username,
            password: PASSWORD,
            csrfmiddlewaretoken: csrfToken(),
            next: '/',
        }),
        {
            redirects: 0,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                Referer: `${BASE}/admin/login/`,
            },
            tags: { endpoint: 'admin_login' },
        },
    )
    check(res, { 'login 302': (r) => r.status === 302 })
    if (res.status !== 302) {
        fail(`登录失败（${res.status}），请确认已运行 \`just seed-stress ${STUDENTS}\`。`)
    }
}

/** 发卷并返回题目；每名学生每轮一张 */
function fetchContest () {
    const res = http.get(`${BASE}/contest/`, { tags: { endpoint: 'contest' } })

    // 403 通常意味着答题未开放，或该账号 2 次机会已用尽（未重新 seed）
    if (res.status === 403) {
        fail(
            'GET /contest/ 返回 403：答题未开放，或该学生答题次数已用尽。' +
        ' 请先运行 `just seed-stress` 重置数据后再压测。',
        )
    }

    const doc = parseHTML(res.body)
    const questions = parseQuestions(doc)

    check(res, {
        'contest 200': (r) => r.status === 200,
        'contest has questions': () => Object.keys(questions).length === N_QUESTIONS,
    })

    if (Object.keys(questions).length !== N_QUESTIONS) {
        fail(`考卷题目数为 ${Object.keys(questions).length}，期望 ${N_QUESTIONS}，题库可能不足。`)
    }
    return questions
}

/** 暂存答卷（对应前端每次选择触发的 fetch） */
function update (answers) {
    const res = http.post(
        `${BASE}/contest/update/`,
        encodeForm({ ...answers, csrfmiddlewaretoken: csrfToken() }),
        {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken(),
                Referer: `${BASE}/contest/`,
            },
            tags: { endpoint: 'contest_update' },
        },
    )
    check(res, { 'update 200': (r) => r.status === 200 })
}

/** 交卷，成功时服务端 302 到 /info/ */
function submit (answers) {
    const res = http.post(
        `${BASE}/contest/submit/`,
        encodeForm({ ...answers, csrfmiddlewaretoken: csrfToken() }),
        {
            redirects: 0,
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken(),
                Referer: `${BASE}/contest/`,
            },
            tags: { endpoint: 'contest_submit' },
        },
    )
    check(res, { 'submit 302': (r) => r.status === 302 })
}

//! 场景

/** 匿名访问：首页 200，其余需登录的接口应 302 */
export function anonymous () {
    const index = http.get(`${BASE}/`, { tags: { endpoint: 'index' } })
    check(index, { 'index 200': (r) => r.status === 200 })

    const contest = http.get(`${BASE}/contest/`, {
        redirects: 0,
        tags: { endpoint: 'contest_anon' },
    })
    check(contest, {
        'contest requires login': (r) => r.status === 302 || r.status === 403,
    })

    const review = http.get(`${BASE}/contest/review/0/`, {
        redirects: 0,
        tags: { endpoint: 'contest_review_anon' },
    })
    check(review, {
        'review requires login': (r) => r.status === 302 || r.status === 403,
    })

    const info = http.get(`${BASE}/info/`, {
        redirects: 0,
        tags: { endpoint: 'info_anon' },
    })
    check(info, {
        'info requires login': (r) => r.status === 302 || r.status === 403,
    })

    sleep(1)
}

/** 完整学生流程，每次迭代使用一名独立学生，避免答题次数冲突 */
export function workflow () {
    const index = exec.scenario.iterationInTest
    const username = PREFIX + pad((index % STUDENTS) + 1)

    group('login', () => {
        login(username)
    })

    group('history', () => {
        const res = http.get(`${BASE}/info/`, { tags: { endpoint: 'info' } })
        check(res, { 'info 200': (r) => r.status === 200 })
    })

    group('submit_without_draft', () => {
    // 尚未发卷，应被 pass_or_forbid 拒绝
        const res = http.post(
            `${BASE}/contest/submit/`,
            encodeForm({ csrfmiddlewaretoken: csrfToken() }),
            {
                redirects: 0,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken(),
                    Referer: `${BASE}/info/`,
                },
                tags: { endpoint: 'contest_submit_no_draft' },
            },
        )
        check(res, { 'submit without draft 403': (r) => r.status === 403 })
    })

    // 两次作答机会
    for (let attempt = 0; attempt < 2; attempt++) {
        group(`attempt_${attempt + 1}`, () => {
            const questions = fetchContest()

            // 逐题暂存，模拟前端行为
            const answers = {}
            for (const question of Object.keys(questions)) {
                answers[question] = questions[question][
                    Math.floor(Math.random() * questions[question].length)
                ]
                update(answers)
            }

            submit(answers)

            const info = http.get(`${BASE}/info/`, { tags: { endpoint: 'info' } })
            check(info, { 'info 200 after submit': (r) => r.status === 200 })

            const review = http.get(`${BASE}/contest/review/${attempt}/`, {
                tags: { endpoint: 'contest_review' },
            })
            check(review, {
                [`review ${attempt} 200`]: (r) => r.status === 200,
            })
        })
    }

    group('review_out_of_range', () => {
        const res = http.get(`${BASE}/contest/review/99/`, {
            tags: { endpoint: 'contest_review_missing' },
        })
        check(res, { 'review missing 404': (r) => r.status === 404 })
    })

    group('logout', () => {
    // 带上 next，LogoutView 才会 302；否则渲染登出页返回 200
        const res = http.post(
            `${BASE}/admin/logout/?next=/`,
            encodeForm({ csrfmiddlewaretoken: csrfToken() }),
            {
                redirects: 0,
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken(),
                    Referer: `${BASE}/`,
                },
                tags: { endpoint: 'admin_logout' },
            },
        )
        check(res, { 'logout 302': (r) => r.status === 302 })
    })

    sleep(0.5)
}
