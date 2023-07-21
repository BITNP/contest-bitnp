const form = document.querySelector("form")
const update_url = form.action.replace(/submit\/$/, 'update/')

form.addEventListener('input', () => {
    const request = new XMLHttpRequest()
    request.open("POST", update_url)
    request.send(new FormData(form))
})
