import resolve from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'
import { babel } from '@rollup/plugin-babel'
import terser from '@rollup/plugin-terser'

import dev_config from './rollup.config.dev.mjs'

const config = {
    input: dev_config.input,
    output: {
        ...dev_config.output,
        compact: true,
    },
    plugins: [
        commonjs(),
        resolve(),
        babel({ babelHelpers: 'bundled' }),
        terser(),
    ],
}

export default [
    config,
    ...config.input.map(file => ({
        ...config,
        input: file,
        output: {
            ...config.output,
            entryFileNames: '[name].no-split.js',
        },
    }))
]
