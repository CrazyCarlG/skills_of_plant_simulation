                                                                                    
  1. Planner / Architect — 接收需求,拆解任务,设计实现方案(如本仓库的 Plan agent)。                                 
  2. Code Generator / Writer — 实际写代码、补全代码、写新文件/新方法。                                             
  3. Code Reviewer — 对 diff/PR 做独立审查,挑 bug / 性能 / 安全 / 设计问题(如 code-reviewer)。                     
  4. Tester / Verifier — 跑测试、build、lint,产出 PASS/FAIL 证据(如 verification)。                                
  5. Debugger / Fixer — 读报错、修 bug、回滚验证。      
  6. Refactorer / Simplifier — 清理冗余、提升复用、瘦身(如 simplify)。
  7. Searcher / Explorer — 在代码库里找文件、找调用、读上下文(如 Explore)。
  8. Documenter — 写/更新文档、注释、README、API 说明。
  9. Skill / Tool Manager — 决定"这种情况该调哪个 skill / tool",优化工具调用策略(如 skills-optimizer)。
  10. Knowledge / Memory Curator — 沉淀经验、维护领域知识库、做跨 session 合成(如
  plant-simulation-knowledge-synthesizer)。
  11. Domain Expert — 负责垂直领域知识(本仓库的 plant-simulation-expert / student / experience-curator)。