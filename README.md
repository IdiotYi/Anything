# Anything / 电影种子搜索示例

一个前后端分离的演示项目，输入电影名称后跳转至帝国影视（dygang.cc）的搜索结果页面。

## 目录结构

```
backend/    Flask API 服务
frontend/   静态站点（单页应用）
scripts/    调试脚本（包含 legacy 方案）
```

## 环境准备

1. 建议创建虚拟环境 `python -m venv .venv`
2. 激活虚拟环境
3. 安装依赖：

```bash
pip install -r requirements.txt
```

## 启动后台服务

```bash
python backend/app.py
```

默认监听 `http://127.0.0.1:5000`。控制台会提示前端入口。

## 使用前端页面

直接在浏览器打开 `frontend/index.html`，输入电影名并搜索，页面会展示一个跳转至帝国影视的结果链接。

## API 说明

- `GET /api/search?q=关键词`：返回包含帝国影视搜索结果链接的 JSON 数据
- `GET /api/detail?url=...`：演示用途，返回静态的磁力链接示例

示例：

```
GET http://127.0.0.1:5000/api/search?q=新闻女王
```

## 调试脚本

- `scripts/test_dygang.py`：单独验证搜索跳转是否生效
- `scripts/legacy/`：旧版爬虫调试脚本，保留作参考

## 注意事项

- 网站依赖第三方站点（dygang.cc）的搜索跳转，若对方策略调整可能失效
- 请遵守目标站点的 robots.txt 与使用条款，合理控制访问频率
- 本项目仅供学习与演示使用
