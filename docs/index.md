# Templates 目录索引与流程说明

本文档汇总 `templates/` 目录下所有 HTML 模板的用途、所处流程位置、关键路由与依赖，便于开发、联调与验收。

- 入口与同意：index.html, warning.html, consent.html
- 受试者信息：demographic.html
- 练习阶段（Practice）：practice/*
- 正式任务：instruction.html, task_a.html, task_b.html
- 阅读后评分：task_c1.html, task_c2.html, task_c3.html, task_c4.html
- 自由回忆：k2.html
- 字母比对：let_comp_one_inst.html, let_comp_one.html, let_comp_two_inst.html, let_comp_two.html
- 测验与收尾：questions.html, vocab.html, done.html
- 工具与诊断：timer.html, settings.html, task_setting.html

---

## 全局依赖与约定
- 倒计时：多数任务页从 `session.remainingTime`、`session.redirectPage` 读取，加载 `static/js/countdown.js`。
- 静态按钮图片：`static/images/start_button.gif`、`nextpage_button.gif`、`next_button.gif`、`done_button.gif`。
- 路由命名空间：正式任务多在 `core.*`，练习流程在 `practice.*`。
- 常见模板变量：
  - 选题页：`topicResult`/`topic_result`（标题）、`subtopics`（子主题列表）、`visited_subtop`（已访问集合）。
  - 阅读页：`passResult['passText']`、`passOrder`。
  - 评分页：`fid`、`passID`、`action_url`、`qid`（c1/c2/c3/c4）。

---

## 流程总览（高层）
1) index → consent → demographic → practice/prac_instruction → prac_a → prac_b → prac_c1/c2/c3 → prac_k2 → instruction（进入正式）
2) instruction → task_a（选主题/子主题）→ task_b（阅读）→ task_c1 → task_c2 → task_c3 →（可选）task_c4 → k2 →（字母比对/测验）→ questions/vocab → done

> 练习与正式流程结构一致；练习阶段的评分页也复用正式评分路由（c1/c2/c3）。

---

## 入口与同意
- templates/index.html
  - 目的：入口页，分屏两个 iframe。
  - 上方：`core.warning`；下方：`core.consent`。
- templates/warning.html
  - 目的：提醒勿刷新、勿前进后退。
- templates/consent.html
  - 目的：研究同意书与 MTurk Worker ID 采集。
  - 提交：`core.demographic`（POST）。
  - 校验：必须勾选“同意”。

## 受试者信息
- templates/demographic.html
  - 目的：收集年龄、性别、教育年限、母语/习得年龄、族裔与种族等。
  - 提交：`practice.prac_instruction`（POST）。
  - 校验：HTML required 与简单 JS。

---

## 练习阶段（Practice）
- templates/practice/prac_instruction.html
  - 目的：练习说明，展示三条 0–100 评分示意。
  - 提交：`practice.prac_a?fid=begin`（POST）。
- templates/practice/prac_a.html
  - 目的：练习选题页，展示主题与子主题卡片；未访问的子主题可点击。
  - 跳转：`practice.prac_b?subtop=...&passOrd=01&lastPage=a`。
  - 倒计时：`session.remainingTime`、`session.redirectPage` + `countdown.js`。
- templates/practice/prac_b.html
  - 目的：练习阅读页；显示 `passResult['passText']`。
  - 导航：
    - “Go to OTHER TOPIC” → `core.task_c1?fid=back`
    - “Read NEXT ARTICLE” → `core.task_c1?fid=same`（受 `passOrder` 控制）
- templates/practice/prac_c1.html / prac_c2.html / prac_c3.html
  - 目的：三条评分问卷（与正式 C1–C3 一致）。
  - 提交：分别至 `core.task_c1`、`core.task_c2`、`action_url`；提交 `fid`、`qid`、等隐藏字段。
- templates/practice/prac_k2.html
  - 目的：练习自由回忆（K2）。
  - 提交：`core.instruction`（进入正式说明页）。

---

## 正式任务：说明与选题/阅读
- templates/instruction.html
  - 目的：正式说明页，含三条评分示意。
  - 提交：`core.task_a?fid=begin`（POST）。
- templates/task_a.html
  - 目的：正式选题页；呈现主题与子主题卡片。
  - 跳转：`core.task_b?subtop=...&passOrd=01&lastPage=a`。
  - 倒计时：与练习相同（从 session）。
- templates/task_b.html
  - 目的：正式阅读页，展示 `passResult['passText']`。
  - 导航：
    - “Go to OTHER TOPIC” → `core.task_c1?fid=back`
    - 或 “Read NEXT ARTICLE” → `core.task_c1?fid=same`（依据 `passOrder`）。

---

## 正式任务：阅读后评分（C1–C4）
- templates/task_c1.html
  - 题目：1. How easy was this article to read?
  - 提交：`core.task_c1?fid={{fid}}`（POST），`qid=c1`。
- templates/task_c2.html
  - 题目：2. Including the other articles..., how much new information...?
  - 提交：`core.task_c2?fid={{fid}}`（POST），`qid=c2`。
- templates/task_c3.html
  - 题目：3. How much did you learn from this particular article?
  - 提交：`action_url`（由后端注入），包含 `fid`、`passID`、`qid=c3`。
- templates/task_c4.html
  - 题目：4. How much do you learn about Donation and Medical Transplants?
  - 提交：`action_url`（由后端注入），`qid=c4`。

> 四个评分页共同点：使用滑条（0–100）、只读文本框显示当前值、提交前 JS 非空校验。

---

## 自由回忆（K2）
- templates/k2.html
  - 目的：受试者用文本描述学习到的知识点（按主题/子主题）。
  - 变量：`topicTitle`、`trimSubtop`、`action_url`。
  - 提交：`action_url`（通常进入字母比对或测验）。

---

## 字母比对（Letter Comparison）
- templates/let_comp_one_inst.html
  - 目的：第一轮字母比对说明；GET 前往 `core.let_comp_one`。
- templates/let_comp_one.html
  - 目的：第一轮 10 题，S/D 二选一（左右字符串是否一致）。
  - 提交：`core.let_comp_two_inst`（POST）。
- templates/let_comp_two_inst.html
  - 目的：第二轮字母比对说明；POST 前往 `core.let_comp_two`。
- templates/let_comp_two.html
  - 目的：第二轮 10 题，S/D 二选一。
  - 提交：`core.let_comp_two`（POST；通常后端处理后进入后续环节）。

---

## 测验与收尾
- templates/questions.html
  - 目的：多选理解题（MCQ）列表（Bootstrap 卡片风格）。
  - 变量：`pass_title`、`questions`（含 questionID/text/choiceA-D）、`existing_answers`（预填）。
  - 提交：`core.done`（POST）。
- templates/vocab.html
  - 目的：词汇测试（15 题 × 6 选项，含“不确定”）。
  - 提交：`action_url`（POST）。
- templates/done.html
  - 目的：展示学习到的概念数与 MTurk 回执码。
  - 变量：`bonusWordsCnt`、`final_code`。

---

## 工具与诊断
- templates/timer.html
  - 目的：独立倒计时页面（可嵌入/iframe），变量：`remaining_time`、`redirect_page`。
- templates/settings.html
  - 目的：调试页（继承 base.html）；显示 `sid`、`uid`、`topID`、`conID`、`taskDone`、`conDone`。
- templates/task_setting.html
  - 目的：简要显示当前 `topID`。

---

## 路由引用速览（按出现顺序）
- `core.warning`，`core.consent`，`core.demographic`
- `practice.prac_instruction`，`practice.prac_a`，`practice.prac_b`
- `core.instruction`，`core.task_a`，`core.task_b`
- `core.task_c1`，`core.task_c2`（`task_c3/task_c4` 通过 `action_url` 传入）
- `core.let_comp_one`，`core.let_comp_two_inst`，`core.let_comp_two`
- `core.done`

---

## 备注与建议
- `passResult['passText']` 以 `|safe` 渲染，需确保后端内容已消毒，避免 XSS 风险。
- 题目校验：模板中多处仅校验首题/核心字段，建议在后端再次做完整必填校验。
- 倒计时跳转：`RedirectPage` 由后端注入（session/上下文），与 `countdown.js` 协同。

如需补充流程图（Mermaid）或与 Flask 路由对应关系的更详细表格，请告知。

---

## 流程图（Mermaid）

```mermaid
flowchart TD
  A[Index/index.html] --> W[Warning (core.warning)\nwarning.html]
  A --> C[Consent (core.consent)\nconsent.html]
  C --> D[Demographic (core.demographic)\ndemographic.html]

  D --> PI[Practice Instruction (practice.prac_instruction)\npractice/prac_instruction.html]
  PI --> PA[Practice A (practice.prac_a)\npractice/prac_a.html]
  PA -->|选择子主题| PB[Practice B (practice.prac_b)\npractice/prac_b.html]
  PB -->|Go OTHER TOPIC| PC1B[评分 C1 (core.task_c1?fid=back)\npractice/prac_c1.html]
  PB -->|Read NEXT| PC1S[评分 C1 (core.task_c1?fid=same)\npractice/prac_c1.html]
  PC1B --> PC2[评分 C2 (core.task_c2)\npractice/prac_c2.html]
  PC1S --> PC2
  PC2 --> PC3[评分 C3 (action_url)\npractice/prac_c3.html]
  PC3 --> PK2[Practice K2 (practice→core.instruction)\npractice/prac_k2.html]

  PK2 --> INS[Instruction (core.instruction)\ninstruction.html]
  INS --> TA[Task A (core.task_a)\ntask_a.html]
  TA -->|选择子主题| TB[Task B (core.task_b)\ntask_b.html]
  TB -->|Go OTHER TOPIC| C1B[评分 C1 (core.task_c1?fid=back)\ntask_c1.html]
  TB -->|Read NEXT| C1S[评分 C1 (core.task_c1?fid=same)\ntask_c1.html]
  C1B --> C2[评分 C2 (core.task_c2)\ntask_c2.html]
  C1S --> C2
  C2 --> C3[评分 C3 (action_url)\ntask_c3.html]
  C3 --> C4{可选 C4\naction_url\n task_c4.html}
  C3 --> K2[K2 自由回忆\naction_url\n k2.html]
  C4 --> K2

  K2 --> L1I[Let Comp 1 Inst (core.let_comp_one)\nlet_comp_one_inst.html]
  L1I --> L1[Let Comp 1 (core.let_comp_two_inst)\nlet_comp_one.html]
  L1 --> L2I[Let Comp 2 Inst (core.let_comp_two)\nlet_comp_two_inst.html]
  L2I --> L2[Let Comp 2 (core.let_comp_two)\nlet_comp_two.html]

  L2 --> Q[Comprehension Questions (render-route)\nquestions.html]
  Q --> DONE[Done (core.done)\ndone.html]
  L2 --> V[Vocabulary (render-route)\nvocab.html]
  V --> DONE
```

说明：部分节点使用 `action_url`/“render-route”表示由后端动态决定的提交或呈现路由。

---

## 路由与模板变量速查表

| 路由 | 模板 | 方法 | 作用 | 关键模板变量（输入/上下文） |
|---|---|---|---|---|
| `core.warning` | `warning.html` | GET | 顶部提醒 | 无 |
| `core.consent` | `consent.html` | GET | 同意书页 | 无 |
| `core.demographic` | `demographic.html` | POST(from consent) / GET(render) | 收集受试者信息 | 无（表单本地校验） |
| `practice.prac_instruction` | `practice/prac_instruction.html` | GET / POST(from demographic) | 练习说明页 | 无 |
| `practice.prac_a` | `practice/prac_a.html` | GET / POST(fid=begin) | 练习选题 | `topic_result`、`subtopics`、`visited_subtop`、`session.remainingTime`、`session.redirectPage` |
| `practice.prac_b` | `practice/prac_b.html` | GET | 练习阅读 | `passResult['passText']`、`passOrder`、`session.remainingTime`、`session.redirectPage` |
| `core.task_c1` | `task_c1.html` / `practice/prac_c1.html` | GET(render)/POST(submit) | 评分1：阅读难易 | `fid`（隐藏域/查询参） |
| `core.task_c2` | `task_c2.html` / `practice/prac_c2.html` | GET/POST | 评分2：信息新颖度 | `fid` |
| 动态 `action_url` | `task_c3.html` / `practice/prac_c3.html` | POST | 评分3：本篇学习量 | `fid`、`passID`（隐藏域）、`qid=c3` |
| 动态 `action_url` | `task_c4.html` | POST | 评分4：总体学习量 | `fid`、`qid=c4` |
| `core.instruction` | `instruction.html` | GET / POST(from prac_k2) | 正式说明 | 无 |
| `core.task_a` | `task_a.html` | GET / POST(fid=begin) | 正式选题 | `topicResult`、`subtopics`、`visited_subtop`、`session.remainingTime`、`session.redirectPage` |
| `core.task_b` | `task_b.html` | GET | 正式阅读 | `passResult['passText']`、`passOrder`、`session.remainingTime`、`session.redirectPage` |
| `core.let_comp_one` | `let_comp_one_inst.html`(next) / `let_comp_one.html`(render) | GET / POST(next) | 字母比对1（说明→作答） | 作答页收集 `lc1`..`lc10` |
| `core.let_comp_two_inst` | `let_comp_one.html`(submit target) | POST | 进入字母比对第二轮说明 | - |
| `core.let_comp_two` | `let_comp_two_inst.html`(next) / `let_comp_two.html`(render/submit) | GET/POST | 字母比对2 | 作答页收集 `lc11`..`lc20` |
| 渲染路由（未命名） | `questions.html` | GET | 理解题（MCQ） | `pass_title`、`questions[*]`、`existing_answers` |
| 提交 `core.done` | `questions.html` | POST | 提交理解题并收尾 | - |
| 渲染路由（未命名） | `vocab.html` | GET | 词汇测试 | `action_url`（提交目的地） |
| 动态 `action_url` | `vocab.html` | POST | 提交词汇测试 | 单题 `voc1`..`voc15` |
| `core.done` | `done.html` | GET | 完成页（显示回执码等） | `bonusWordsCnt`、`final_code` |
| 工具 | `timer.html` | GET | 独立倒计时 | `remaining_time`、`redirect_page` |
| 工具/诊断 | `settings.html` | GET | 状态诊断 | `sid`、`uid`、`topID`、`conID`、`taskDone`、`conDone` |
| 工具 | `task_setting.html` | GET | 显示当前 `topID` | `topID` |

注：上表中“渲染路由（未命名）/action_url”为模板通过注入变量决定的路由；实际项目中请在 `app.py` 中确认对应 endpoint 名称与方法。
