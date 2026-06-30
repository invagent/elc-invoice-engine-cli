---
name: elc-context
description: 初始化 ELC CLI 上下文。在执行任何 ELC CLI 操作前调用，让 AI 了解当前环境、命令、接口行为和已知问题。其他 ELC 相关 Skill 应在开头引用本 Skill。
---

# ELC Context Skill

## 触发条件

以下情况下自动触发（或被其他 Skill 引用触发）：
- 用户说"帮我用 elc 做 X"
- 用户说"用 CLI 查询/创建/导出发票"
- 任何其他 ELC Skill 在执行前引用本 Skill

## 执行步骤

### 第一步：获取当前环境上下文

```bash
elc describe -o json
```

读取输出，建立以下上下文：
- `env.base_url`：API 服务地址
- `env.company_id`：当前公司 ID（X-Company-ID header）
- `env.logged_in`：是否已登录
- `cached_mappings`：已缓存的导出映射表列表
- `commands`：所有可用命令及说明
- `api_behaviors`：接口分页、过滤、状态等行为
- `known_issues`：已知问题和坑
- `export_workflow`：导出发票的标准流程

### 第二步：检查登录状态

如果 `env.logged_in` 为 `false`：
```bash
elc login status
```
提示用户先运行 `elc login` 完成认证。

### 第三步：将上下文注入后续操作

将 `elc describe` 的输出作为后续所有 ELC 操作的知识基础，特别注意：

**接口行为（必读）：**
- 分页用 cursor，不是 pageNum；每页固定 20 条
- 时间过滤参数是 `updatedFrom` / `updatedTo`，格式 `YYYY-MM-DD`
- `GET /v2/invoice-requests/{id}` 单条接口不稳定，改用 list + sourceId 过滤
- `X-Company-ID`（大写 ID），不是 `X-Company-Id`

**Source XML 可用性：**
- 只有通过上传 KDUBL XML 创建的申请单才有 Source 文件
- 返回 `403004` 表示该发票无 Source XML（测试数据常见）

**导出发票流程：**
1. `elc export init` → 采集样本
2. AI 推断映射 → `elc export save-mapping`
3. `elc export invoice` → 导出 Excel

---

## 供其他 Skill 引用

在其他 ELC Skill 的开头加入：

```markdown
## 前置条件
执行本 Skill 前，先运行 **elc-context** Skill 获取环境上下文。
```

当前已引用本 Skill 的 Skill 列表：
- `invoice-export` — 导出发票到 Excel
