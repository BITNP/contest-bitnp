import resolve from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'

export default {
    input: {
        index_and_info: './src/index_and_info.js',
        contest: './src/contest.js',
        toggle_mobile_menu: './src/toggle_mobile_menu.js',
    },
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
