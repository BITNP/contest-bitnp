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
