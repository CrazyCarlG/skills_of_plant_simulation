---
last_updated: 2026-09-10
dimension: 02-user-expectation-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_student-agent-evaluation.md
skills_touched: []
models_touched: []
---

# student agent = 反射型学习者(60-65% 理解度),不是工程型学习者

## 症状
- plant-simulation-student 在 13 个 session 全部产出大量 Method/类层级/ICN 反射层笔记,但 0 次实跑仿真。
- 跨 5 篇笔记抽样统计:"未深读" baseline 22 次 / "未明文" 6 次 / 真正深读 baseline 0 篇。
- student 0 次触发 `EventController.start` 验证 MU 移动、Destination 命中、Statistic 累积。
- student 提"🆕 Novel" 14 个 ICN 重构 finding,但 `01-plant-simulation-knowledge/` 未支持 → 需 curator / synthesizer 验证真伪。
- student Quirk 编号违规:13 篇笔记引用 Quirk #1-#26,但 `quirks-canonical.md` 实际只有 #6/#7/#13。

## 根因
- student agent prompt 定义的姿态是"读代码 / 跑查询 / 试参数 / 用户引导下改完回滚",强调"反射层"而非"运行时验证"。
- student 默认**只读**,需要用户明确说"演示给我看 / 改完回滚给我看"才可写 → 反射型学习的强化。
- student 自己反思"需 GUI F8 查看"的实际含义是 baseline 深读 + 实跑仿真,但默认 workflow 不强制这两项。

## Workaround / 结论
- **改进建议 6 条**(给 student 自己下次 session):
  1. **baseline 深读优先**:`01-plant-simulation-help/objects/<name>/README.md` + `attributes/` + `methods/` 全文
  2. **Quirk 协议遵守**:❸铁律"找不到 → 不写编号"严格执行
  3. **实跑仿真验证**:不要只 dump 源码,要 EventController 启动 + observe MU 移动 + 检查 Destination 命中
  4. **Operator self-review 诚实**:Result: partial 时明确标注"未达 X / 未完成 Y"
  5. **cross-session 综合要做 baseline 校验**:"PS 2.0 ICN 重构"等系统级 finding 必须有 `01-plant-simulation-knowledge/` 支持
  6. **反思 student 自己说"需 GUI F8 查看"的实际含义** — 真正弥补行动:baseline 深读 + 实跑仿真
- **教学节奏**:用户切换 expert 后要求"评估 student 真的理解了 PS 吗" → 期望是 360 度诚实评估 + 改进路径,不是 polite review。
- **decision 不要 hard-block**:不强求 student 重做 session,只给路径建议;不强求 curator/synthesizer 立刻行动,只标评审项。

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_student-agent-evaluation.md`(完整评估报告)
- 关联 finding:student 14 个 🆕 Novel ICN → `2026-09-10_ps20-icn-refactor-14-new-names.md`(P1, 待沉淀)
- 关联 finding:5 个 Station.OnPull meta-analysis → `2026-09-10_station-onpull-spectrum-5-models.md`

## 反思
"反射型 vs 工程型"是学习者姿态的核心区分;expert / curator / synthesizer 协作时,应该把 student 的反射层 finding 当候选 hypothesis(待运行时验证),不是已 verified knowledge。
