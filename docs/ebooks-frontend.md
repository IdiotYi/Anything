# 电子书前端

新增“影视 / 电子书”页签；各自保留输入与结果。影视仍使用原有 API。

## 当前行为

电子书后端尚未实现，当前默认使用明确标注的演示数据，不请求不存在的接口，不提供伪造下载链接。
搜索“红楼梦”“西游记”“Pride and Prejudice”或作者可预览结果；格式按钮禁用。
空查询由表单校验拦截；无匹配显示空状态。

## 接入后端

在 frontend/assets/books.js 将 DEMO_MODE 改为 false。
预留接口：GET /api/books/search?q=书名或作者。
该接口目前仅为前端约定，尚未实现。

返回示例（示意 URL，不是真实资源）：

```json
{
  "success": true,
  "results": [
    {
      "title": "示例书籍",
      "author": "作者",
      "language": "中文",
      "description": "简介",
      "source": "授权来源",
      "license": "授权说明",
      "downloadLinks": [
        {
          "title": "EPUB 版本",
          "format": "EPUB",
          "url": "https://example.org/book.epub"
        }
      ]
    }
  ]
}
```

下载链接仅接受无内嵌凭据的绝对 HTTP/HTTPS URL；后端需确保资源授权。
支持加载、空结果、错误提示与重复搜索取消。接口 404/501 显示“尚未接入”。

验证：`node --test tests/test_books.cjs`，以及 `python -m unittest discover -s tests -v`。
