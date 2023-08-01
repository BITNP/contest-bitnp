/**
 * @param {string} key
 */
function get_data (key) {
    return JSON.parse(document.getElementById(`data:${key}`).textContent)
}

const form = document.querySelector("form")
const update_url = get_data("update-url")

form.addEventListener('input', () => {
    const request = new XMLHttpRequest()
    request.open("POST", update_url)
    request.send(new FormData(form))
})
