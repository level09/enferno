import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    base: '/static/dist/', // Setting the base URL for assets

    build: {
        rollupOptions: {
            input: {
                index: './enferno/src/index.js'
            },
            output: {
                entryFileNames: `[name].js`,
                chunkFileNames: `[name].js`,
                assetFileNames: `[name].[ext]`,

                manualChunks: undefined
            }
        },
        sourcemap: true,
        target: 'esnext',
        outDir: './enferno/static/dist/'
    }
})
