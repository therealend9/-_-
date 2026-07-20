import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

function vendorChunk(id) {
  if (!id.includes('node_modules')) return

  const normalized = id.replaceAll('\\', '/')
  const elementComponentMatch = normalized.match(/\/node_modules\/element-plus\/es\/components\/([^/]+)/)

  if (normalized.includes('/node_modules/vue/') || normalized.includes('/node_modules/vue-router/')) {
    return 'vendor-vue'
  }

  if (elementComponentMatch) {
    const component = elementComponentMatch[1]
    const formComponents = new Set([
      'autocomplete',
      'cascader',
      'checkbox',
      'checkbox-button',
      'checkbox-group',
      'color-picker',
      'date-picker',
      'form',
      'form-item',
      'input',
      'input-number',
      'input-tag',
      'mention',
      'option',
      'option-group',
      'radio',
      'radio-button',
      'radio-group',
      'select',
      'select-v2',
      'slider',
      'switch',
      'time-picker',
      'time-select',
      'transfer',
      'upload'
    ])
    const dataComponents = new Set([
      'badge',
      'calendar',
      'descriptions',
      'descriptions-item',
      'pagination',
      'progress',
      'result',
      'statistic',
      'step',
      'steps',
      'table',
      'table-column',
      'tabs',
      'tab-pane',
      'tag',
      'timeline',
      'timeline-item',
      'tour',
      'tree',
      'tree-select',
      'tree-v2'
    ])
    const overlayComponents = new Set([
      'dialog',
      'drawer',
      'dropdown',
      'dropdown-item',
      'dropdown-menu',
      'message',
      'message-box',
      'notification',
      'popconfirm',
      'popover',
      'popper',
      'tooltip'
    ])
    const layoutComponents = new Set([
      'aside',
      'breadcrumb',
      'breadcrumb-item',
      'button',
      'button-group',
      'card',
      'col',
      'container',
      'divider',
      'footer',
      'header',
      'main',
      'menu',
      'menu-item',
      'menu-item-group',
      'row',
      'scrollbar',
      'sub-menu'
    ])

    if (formComponents.has(component)) return 'element-form'
    if (dataComponents.has(component)) return 'element-data'
    if (overlayComponents.has(component)) return 'element-overlay'
    if (layoutComponents.has(component)) return 'element-layout'
    return 'element-misc'
  }

  if (normalized.includes('/node_modules/element-plus/')) {
    if (normalized.includes('/node_modules/element-plus/es/directives/')) return 'element-directives'
    if (normalized.includes('/node_modules/element-plus/es/locale/')) return 'element-locale'
    return 'element-core'
  }

  if (normalized.includes('/node_modules/@element-plus/icons-vue/')) {
    return 'vendor-element-icons'
  }

  if (normalized.includes('/node_modules/echarts/')) {
    return 'vendor-echarts'
  }

  return 'vendor'
}

// https://vite.dev/config/
export default defineConfig({
  base: '/sizheng-agent-frontend/',
  plugins: [vue()],
  build: {
    outDir: 'docs',
    rolldownOptions: {
      onLog(level, log, handler) {
        const message = String(log.message || '')
        const isKnownPureAnnotationWarning =
          log.code === 'INVALID_ANNOTATION' &&
          message.includes('#__PURE__') &&
          message.includes('@vueuse/core')

        if (isKnownPureAnnotationWarning) return

        handler(level, log)
      },
      output: {
        manualChunks: vendorChunk
      }
    }
  },
})
