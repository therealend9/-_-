import './styles/global.css'

import { createApp } from 'vue'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElAlert } from 'element-plus/es/components/alert/index.mjs'
import { ElAvatar } from 'element-plus/es/components/avatar/index.mjs'
import { ElButton } from 'element-plus/es/components/button/index.mjs'
import { ElCard } from 'element-plus/es/components/card/index.mjs'
import { ElCheckbox, ElCheckboxGroup } from 'element-plus/es/components/checkbox/index.mjs'
import { ElCol } from 'element-plus/es/components/col/index.mjs'
import { ElConfigProvider } from 'element-plus/es/components/config-provider/index.mjs'
import { ElDatePicker } from 'element-plus/es/components/date-picker/index.mjs'
import { ElDialog } from 'element-plus/es/components/dialog/index.mjs'
import { ElDivider } from 'element-plus/es/components/divider/index.mjs'
import { ElEmpty } from 'element-plus/es/components/empty/index.mjs'
import { ElForm, ElFormItem } from 'element-plus/es/components/form/index.mjs'
import { ElIcon } from 'element-plus/es/components/icon/index.mjs'
import { ElInput } from 'element-plus/es/components/input/index.mjs'
import { ElInputNumber } from 'element-plus/es/components/input-number/index.mjs'
import { ElLoading } from 'element-plus/es/components/loading/index.mjs'
import { ElMessage } from 'element-plus/es/components/message/index.mjs'
import { ElPagination } from 'element-plus/es/components/pagination/index.mjs'
import { ElProgress } from 'element-plus/es/components/progress/index.mjs'
import { ElRadio, ElRadioButton, ElRadioGroup } from 'element-plus/es/components/radio/index.mjs'
import { ElResult } from 'element-plus/es/components/result/index.mjs'
import { ElRow } from 'element-plus/es/components/row/index.mjs'
import { ElOption, ElSelect } from 'element-plus/es/components/select/index.mjs'
import { ElSlider } from 'element-plus/es/components/slider/index.mjs'
import { ElStep, ElSteps } from 'element-plus/es/components/steps/index.mjs'
import { ElSwitch } from 'element-plus/es/components/switch/index.mjs'
import { ElTable, ElTableColumn } from 'element-plus/es/components/table/index.mjs'
import { ElTabPane, ElTabs } from 'element-plus/es/components/tabs/index.mjs'
import { ElTag } from 'element-plus/es/components/tag/index.mjs'
import { ElTimeline, ElTimelineItem } from 'element-plus/es/components/timeline/index.mjs'
import { ElTree } from 'element-plus/es/components/tree/index.mjs'
import { ElUpload } from 'element-plus/es/components/upload/index.mjs'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const components = [
  ElAlert,
  ElAvatar,
  ElButton,
  ElCard,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElConfigProvider,
  ElDatePicker,
  ElDialog,
  ElDivider,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElInput,
  ElInputNumber,
  ElOption,
  ElPagination,
  ElProgress,
  ElRadio,
  ElRadioButton,
  ElRadioGroup,
  ElResult,
  ElRow,
  ElSelect,
  ElSlider,
  ElStep,
  ElSteps,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabPane,
  ElTabs,
  ElTag,
  ElTimeline,
  ElTimelineItem,
  ElTree,
  ElUpload
]

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

for (const component of components) {
  app.use(component)
}

app.use(router)
app.use(ElLoading)

app.config.errorHandler = (error) => {
  console.error(error)
  ElMessage.error(error?.message || '页面运行异常')
}

window.addEventListener('unhandledrejection', (event) => {
  console.error(event.reason)
  ElMessage.error(event.reason?.message || '接口请求异常')
})

app.mount('#app')
