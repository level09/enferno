import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
    plugins: [vue()],
    base: '/static/dist/', // Setting the base URL for assets
    build: {

        rollupOptions: {
            input: {
                index: resolve(__dirname, 'enferno/src/index.js'),
            },
            output: {
                entryFileNames: `[name].js`,
                assetFileNames: `[name].[ext]`,
            }
        },
        sourcemap: true,
        target: 'esnext',
        outDir: resolve(__dirname, 'enferno/static/dist/')
    }
})
