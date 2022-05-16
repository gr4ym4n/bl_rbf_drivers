
import theme from '@nuxt/content-theme-docs'

export default theme({
    target: 'static',
    router: {
        base: '/bl_rbf_drivers/'
    },
    docs: {
        primaryColor: '#8b3577'
    },
    head: {
        link: [
            {rel: 'icon', type: 'image/x-icon', href: '/bl_rbf_drivers/favicon.ico'}
        ]
    },
    i18n: {
        locales: () => [{
          code: 'en',
          iso: 'en-US',
          file: 'en-US.js',
          name: 'English'
        }],
        defaultLocale: 'en'
    },
    content: {
        markdown: {
            remarkPlugins: ['remark-mermaidjs']
        }
    }
})