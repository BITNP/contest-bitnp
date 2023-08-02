/** @type {HTMLButtonElement} */
const toggle = document.querySelector('button#toggle-mobile-menu')
const [open_icon, close_icon] = toggle.parentElement.querySelectorAll('svg')
const menu = document.querySelector('#mobile-menu')

toggle.addEventListener('click', () => {
    if (menu.classList.contains('hidden')) {
        menu.classList.remove('hidden')
        open_icon.classList.add('hidden')
        close_icon.classList.remove('hidden')
    } else {
        menu.classList.add('hidden')
        open_icon.classList.remove('hidden')
        close_icon.classList.add('hidden')
    }
})
