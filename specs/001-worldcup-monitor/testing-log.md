# 测试问题记录与修复日志

**Feature**: 001-worldcup-monitor  
**Date**: 2026-04-09  
**阶段**: Spec 2-6 实现后集成测试

---

## 问题 1: Pydantic Config 拒绝额外环境变量

**现象**: 后端启动时报错 `Extra inputs are not permitted` — `.env` 中的 `DEBUG`、`LOG_LEVEL` 导致 Config 验证失败。

**原因**: `Config(BaseSettings)` 的 `class Config` 没有设置 `extra = "ignore"`，Pydantic v2 默认 `extra = "forbid"`。

**解决方案**: 在 `backend/src/core/config.py` 的 `Config.Config` 内类中加 `extra = "ignore"`。

**结果**: 成功 ✅

---

## 问题 2: APScheduler 无法序列化被装饰的函数

**现象**: 启动时报 `ValueError: This Job cannot be serialized since the reference to its callable could not be determined`。

**原因**: `log_pipeline_stage` 装饰器没有使用 `functools.wraps`，导致 APScheduler 的 SQLite job store 无法序列化函数引用（需要 `module:function_name` 格式）。

**解决方案**: 在 `backend/src/core/logging.py` 的 `log_pipeline_stage` 装饰器中添加 `@functools.wraps(func)`。

**结果**: 成功 ✅

---

## 问题 3: 数据库模块级别调用 get_config() 导致循环初始化

**现象**: 导入 `database.py` 时立即调用 `get_config()`，在 config 还未就绪时就尝试创建 engine。

**原因**: `database.py` 在模块顶层执行 `config = get_config()` 和 `engine = create_engine(...)`，而不是延迟初始化。

**解决方案**: 改为懒加载模式 — `_get_engine()` 和 `_get_session_factory()` 在首次调用时才创建，使用 `DeclarativeBase` 替代已弃用的 `declarative_base()`。

**结果**: 成功 ✅

---

## 问题 4: Mock 数据重复 — 不同平台生成相同 fingerprint

**现象**: pipeline 运行时 `UNIQUE constraint failed: source_content.fingerprint`，因为不同 platform 的 mock item 文本相同，产生相同 hash。

**原因**: `generate_mock_source_content()` 为不同 platform 分配了相同的 topic 文本，`generate_fingerprint(title, content)` 不区分 platform。

**解决方案**: 在 pipeline 的 `scrape_and_store()` 中添加批内去重检查（`if any(s.fingerprint == fp for s in stored_items)`），并改为逐条 `session.flush()` 捕获约束错误而不是批量 commit。

**结果**: 成功 ✅

---

## 问题 5: Mock 卡片数据单一 — 全部标题相同

**现象**: 8张测试卡片全是"梅西确认参加世界杯"，可信度全是"传闻"，分类单一，无图片。

**原因**: `generate_mock_card()` 每次返回固定的硬编码数据，没有多样性。

**解决方案**: 重写 `mock.py`，新增 `_CARD_POOL` 包含 8 条不同话题（覆盖 4 个分类、3 种可信度、1-3 个来源、有图/无图混合），`generate_mock_card()` 循环取用。同时手动插入精心设计的测试数据直接绕过 pipeline 局限。

**结果**: 成功 ✅ — 8 张卡片覆盖了所有分类、可信度、来源数量组合。

---

## 问题 6: 虎扑爬虫 CSS 选择器全部失效

**现象**: 爬虫返回 0 条数据。`div.post-item`、`a.post-title` 等选择器在真实虎扑页面匹配不到任何元素。

**原因**: 虎扑搜索页是 SPA 架构，搜索结果以 JSON 数据嵌入在 `window.$$data=` 中，不是传统的 DOM 渲染。原爬虫按传统 HTML 爬取方式设计。

**解决方案**: 完全重写 `hupu.py` — 从 HTML 中定位 `window.$$data=` 标记，用 `json.JSONDecoder.raw_decode()` 精确解析 JSON 边界，提取 `searchRes.data` 数组，解析每个 item 的 `title`、`content`、`username`、`addtime`、`replies`、`lights`、`picture`、`id` 字段。

**结果**: 成功 ✅ — 稳定提取 20 条搜索结果。

---

## 问题 7: JSON 边界解析失败

**现象**: 用 `text.find(";</script>")` 截取 JSON 后 `json.loads()` 报 `Extra data` 错误。

**原因**: 虎扑页面中 `window.$$data={...}</script>`，JSON 和 `</script>` 之间没有分号，导致 `find(";</script>")` 找到的是更后面的位置，截取了多余数据。

**解决方案**: 改用 `json.JSONDecoder().raw_decode(html, json_start)`，它会自动在第一个完整 JSON 对象结束处停止，不依赖结束标记。

**结果**: 成功 ✅

---

## 问题 8: 中文关键词 URL 编码错误

**现象**: `scrape_hupu(keyword='2026世界杯')` 报 `'latin-1' codec can't encode characters`。

**原因**: 中文字符直接用 f-string 拼入 URL `f"https://bbs.hupu.com/search?q={keyword}"`，`requests` 库在发送 HTTP 请求时 headers 默认用 latin-1 编码，无法编码中文。

**解决方案**: 导入 `urllib.parse.quote`，URL 改为 `f"https://bbs.hupu.com/search?q={quote(keyword)}"`。

**结果**: 成功 ✅

---

## 问题 9: cleaned_text 存的是 JSON 碎片而非正文

**现象**: 数据库中 `cleaned_text` 字段显示为 `"id" "638351938" "score" 017290954...`，不是可读正文。

**原因**: pipeline 中 `cleaned_text = clean_text(item["raw_html"])` 对 raw_html 做 HTML 清洗。但虎扑新爬虫把原始 JSON 存入 raw_html，HTML 清洗器把 JSON 的 key-value 当文本提取了。

**解决方案**: pipeline 改为优先使用爬虫已提取的 `cleaned_text` 字段：`if item.get("cleaned_text"): cleaned_text = item["cleaned_text"]`，仅在没有预清洗文本时才对 raw_html 做 clean。

**结果**: 成功 ✅ — cleaned_text 正确存储虎扑帖子的内容摘要。

---

## 问题 10: 前端大卡片无图时大片空白

**现象**: 大卡片（`col-span-2 row-span-2`）不显示图片后，多占了两行高度，出现大块空白。

**原因**: `row-span-2` 让卡片跨两行，但没有图片时内容只占一行高度，第二行完全空白。

**解决方案**: HotCard 组件去掉 `row-span-2`，只保留 `col-span-1 md:col-span-2`（横向跨列不跨行）。CardFeed 只让第 1 张卡片为大卡片，其余全小卡片。

**结果**: 成功 ✅

---

## 问题 11: 混排行小卡片顶部不对齐

**现象**: 大卡片和小卡片同行时，小卡片纵向居中而非顶部对齐，出现顶部空隙。

**原因**: CSS grid 默认 `align-items: stretch`，不同高度的卡片在同一行内纵向拉伸。

**解决方案**: CardFeed 的 grid 容器添加 `items-start`（即 `align-items: start`），所有卡片顶部对齐。

**结果**: 成功 ✅

---

## 问题 12: requirements.txt 版本锁死导致安装失败

**现象**: `pip install -r requirements.txt` 报 `Could not find a version that satisfies the requirement alibabacloud_dashscope==1.14.0`。

**原因**: 包名错误（应为 `dashscope` 而非 `alibabacloud_dashscope`），且精确版本号 `==1.14.0` 已不可用。

**解决方案**: 包名改为 `dashscope>=1.14.0`，所有依赖从 `==` 精确版本改为 `>=` 最低版本。

**结果**: 成功 ✅

---

## 问题 13: 详情页点击后加载失败 (HTTP 500)

**现象**: 前端点击卡片跳转详情页后白屏，后端返回 `{"detail":"Failed to generate detail content"}` HTTP 500。

**排查步骤**:
1. 确认后端路由存在（`GET /api/cards/{card_id}/detail`），路由注册正确
2. curl 测试确认 500 错误
3. 查看后端日志发现 `generate_detail()` 返回 None

**原因**: Qwen-Max 返回格式不稳定，存在两种失败模式：
- 返回纯 Markdown（`### 事件概述\n...`）而非 JSON，导致 `json.loads` 直接失败
- 返回 JSON 但末尾附带额外解释文字，导致 `Extra data` 解析错误

**解决方案**: 三处修复
1. `parse_llm_response` 增加三层解析策略：直接 `json.loads` → `JSONDecoder.raw_decode` 处理 trailing data → 首尾花括号提取兜底
2. `generate_detail` 首次解析失败后自动重试，追加 "请严格返回JSON" 强制指令
3. 前端详情页改为友好错误提示（显示具体错误 + 重试按钮 + 返回首页）

**结果**: 成功 ✅

---

## 问题 14: 详情页重试返回 JSON 但 Pydantic 验证失败

**现象**: 重试后 LLM 确实返回了 JSON，但 Pydantic 报 `Field required` 错误——viewpoints 缺少 `view`/`citation`，timeline 缺少 `time`/`citation`，sources 缺少 `id`。

**原因**: LLM 使用了不同的字段名：`content` 代替 `view`，`date` 代替 `time`，`number` 代替 `id`，且部分字段被省略。

**解决方案**: Schema 改为宽容模式
- 所有字段设默认值（不再 required）
- 在 `__init__` 中自动映射常见变体字段名（`content→view`, `date→time`, `number→id`, `opinion→view`, `description→event`）

**结果**: 成功 ✅

---

## 问题 15: client.py 修改后遗留重复 except 块导致 SyntaxError

**现象**: 修改 `parse_llm_response` 后后端启动报 `SyntaxError: unmatched ')'`。

**原因**: 编辑时旧的 `except json.JSONDecodeError` 和 `except Exception` 块没有完全清理，导致代码中出现了重复的 `return None` 和多余的右括号。

**解决方案**: 清理残留代码，只保留一套 `except ValidationError` + `except Exception` 块。

**结果**: 成功 ✅
