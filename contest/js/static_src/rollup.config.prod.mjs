import resolve from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs'
import { babel } from '@rollup/plugin-babel'
import terser from '@rollup/plugin-terser'

import dev_config from './rollup.config.dev.mjs'

export default {
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
