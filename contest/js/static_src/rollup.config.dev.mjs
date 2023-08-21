import resolve from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'

export default {
    input: [
        './src/index_and_info.js',
        './src/contest.js',
        './src/toggle_mobile_menu.js',
    ],
    output: {
        dir: '../static/js/dist/',
        format: 'es',
        entryFileNames: '[name].js',
    },
    plugins: [
        commonjs(),
        resolve(),
    ],
}
