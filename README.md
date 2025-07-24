# DocMind

文档分割模块
完整的软件开发团队包含：管理、产品、交互、前端、后端、数据、测试。总计7个岗位，当前弱化分工，合并为全栈开发，但是项目过程管理仍然按照7个步骤进行。

## 文档

[文档说明](docs/文档/1项目管理.md)

## 参考链接

- minerU: https://github.com/opendatalab/MinerU
- PearAdmin框架: https://gitee.com/pear-admin/pear-admin-flask

## 结构

```bash


docmind/
├── backend/               # Flask 后端
│   ├── app.py             # 应用入口
│   ├── requirements.txt   # Python 依赖
│   ├── config.py          # 配置（数据库、路径等）
│   ├── models/            # SQLAlchemy 模型
│   │   └── __init__.py
│   ├── routes/            # 各功能路由
│   │   └── __init__.py
│   ├── services/          # 核心服务（PDF 解析、Markdown 转换等）
│   │   └── __init__.py
│   └── utils/             # 工具函数（文件存储、命名等）
│       └── __init__.py
│
├── frontend/              # Vue 前端
│   ├── package.json
│   ├── vue.config.js
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router.js
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 公共组件
│   │   └── api/           # 调用后端接口封装
│   └── public/
│       └── index.html
│
└── deploy-compose.yml     # 可选：MySQL + 后端 + 前端 一键启动
```
