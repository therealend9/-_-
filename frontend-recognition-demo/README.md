# 马原智学 Agent 前端

这是“马克思主义基本原理”智慧教学平台的前端工程，包含学生端、教师端、管理端三类页面。当前版本已经内置模拟数据，可以先完成页面演示，后续再切换到真实后端数据库。

## 本地运行

```bash
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173/sizheng-agent-frontend/
```

## 构建

```bash
npm run build
```

构建产物会输出到 `docs/`，可用于静态部署。

## 数据接入

前端默认读取本地 mock 数据，接口封装在 `src/api/`。后端完成后，复制 `.env.example` 为 `.env.local`，并设置：

```text
VITE_USE_MOCK=false
VITE_API_BASE_URL=http://localhost:8080/api
```

详细接口约定见 `src/api/README.md`。

后端服务统一使用项目根目录的 `backend/`，不要在 `frontend/` 下再维护后端副本。
