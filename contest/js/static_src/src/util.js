/**
 * @param {string} key
 */
export function get_data (key) {
    return JSON.parse(document.getElementById(`data:${key}`).textContent)
}
