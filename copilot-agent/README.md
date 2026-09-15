自动建模 copilot 必备 agent                                                                                      
                                                                                                                   
  A. 编排层0. Orchestrator / Pipeline Controller                                                                   

  - 串起下面1→9;负责失败回退、人工 confirm、阶段门(Phase Gate);纯流程调度,不直接建模。

  B. 需求与领域层

  1. Requirement Analyst(需求分析师)
  - 把用户自然语言 / Excel / 工艺卡 / 现有图纸转成结构化 spec:场景类型(离散制造 / 装配 / 仓储 / AGV /
  物流)、实体(MU 类型)、工序(Station链)、资源(工人 / AGV / 机床)、KPI(吞吐 / WIP / 利用率)、边界条件。
  - 输出:requirement-spec.json(供建模架构师消费)。

  2. Domain Knowledge Agent(PS 领域知识)
  - 内置 Plant Simulation 对象库全清单(MaterialFlow / Resources / InformationFlow / MUs / UserInterface 5 大类 +
  CranesAndMore / HBW3D 等 ApplicationObjects);
  - 内置 SimTalk 语言规范、Quirk 行为、属性绑定规则;
  - 内置标准建模范式(Factory51 的 Frame + Interface派生类模式、Small Parts Production 的子 Frame 自包含模式)。

  C. 架构与设计层

  3. Modeling Architect(建模架构师)
  - 选建模范式:离散事件 / 连续流 / 推式 / 拉式 / 资源协作;
  - 设计文件夹结构:Models/(实例)+ UserObjects/(自定义类)+ ApplicationObjects/(库引用)+ 标准库 5 大根;
  - 设计类继承树 3 层:Built-in → 库基础类 → 自定义根类 → 派生类 → 实例;
  -选标准对象组合(Conveyor vs Track、Station vs ParallelStation、Buffer vs Store);
  - 定义 Interface 边界(每个子 Frame 一对 Entry/Exit Interface);
  - 选 SimTalk 模式(Init / Reset / EntranceCtrl / ExitCtrl / push-pull / $Failures / Broker绑定);
  - 只输出架构方案,不建模型——这是关键分层,不能与执行者合并。

  4. Object & Method Designer(对象与方法设计师)
  - 把架构方案落地成具体对象清单(每个 Frame 里放什么对象、对象类型、参数初值);
  - 列出待写的方法清单(Init / Reset / 各 EntranceCtrl / 各 ExitCtrl / 各业务方法);
  - 输出"对象-方法-参数"三栏表,供代码生成器消费。

  D. 代码生成与执行层

  5. SimTalk Code Generator(SimTalk 代码生成器)
  - 按方法清单生成 SimTalk 源码;
  - 必须内置 Quirk 处理:str→num 转换、<- 不可用作表达式、stopuntil 拉式模式、Buffer 容量上限、@.toStr 链路、Method
  引用 vs 直接调用、$Failures 分布函数选型;
  - 输出严格符合 SimTalk 2.x 语法,不写"伪代码"——必须真能编译。

  6. Model Builder / Executor(模型执行器)
  - 真正写进 Plant Simulation——经 TCP / COM桥(如 SimtalkClaude socket / OPC)操作 PS 进程;
  - 写完必 readback验证(避免 silent fail);
  - 操作清单:Create Frame / Create Class / Create Object / Set Property / Create Method / Write Method Source /
  Link Interface;
  - 不能跳过任何步骤;PS 的二进制 .spp 不能手工编辑,只能经桥接。

  E. 验证与迭代层

  7. Validator / Verifier(验证者)
  - 编译检查(SimTalk 语法);
  - Init 烟测:Source.createMU → 流过所有 Station → Drain.delete;
  - KPI 对照:与需求 spec 比对(throughput / WIP / utilization);
  - 检查已知反模式(Station 上挂 Method 但未触发 EntranceCtrl、Broker 未绑、Worker 未注册);
  - 输出 PASS / FAIL + 证据(运行截图 / 日志 / 统计数据)。

  8. Debugger / Refiner(调试与精修)
  - 读 SimTalk 编译错 / 运行异常 / Quirk 警告;
  - 定位根因(对象选错 / 属性配错 / Init 链断 / Quirk 未规避);
  - 生成 patch + 回滚预案;
  - 回到6 重写 → 7 复验,直到 PASS。

  F. 沉淀与文档层

  9. Documentation Generator(文档生成器)
  - 输出架构图(对象树 / 类继承树 / 数据流);
  - 写 user guide(怎么改参数 / 怎么跑实验);
  - 生成 KPI dashboard 配置;
  - 不写代码,只解释。

  10. Memory Curator / Pattern Reuser(记忆策展)
  - 把每次自动建模的 (需求 → 架构 → SimTalk pattern) 沉成模板;
  - 未来同类需求(比如又是"AGV + 立体仓库")直接套模板,跳过 1-4 步;
  - 这是从"工具"到"产品"的关键 agent。

  G. 横切支撑(可选但强烈推荐)

  - 11. Code Reviewer:对生成的 SimTalk 做独立 review,挑 Quirk 风险 / API 误用 / 命名规范;
  - 12. Skill Optimizer:扫桥接 log,发现 silent fail / timeout / 选错 skill,持续优化执行器;
  - 13. Domain Explainer(知识答疑):user 中途问"为什么用 Station不用 ParallelStation / Buffer
  容量上限是多少"时即时答——这是 consult角色,跟执行严格隔离。

  关键分层纪律- 3(架构)≠ 6(执行):架构师不能直接调桥,否则会被"已写了一半再改架构"锁死;

  - 5(代码生成)≠ 6(执行):代码生成是纯文本,执行是 PS 进程操作;中间必须经过"代码静态 lint"(Quirk 检查器)再下发;
  - 7(验证)独立:不能由6 自己说"我跑了一下没崩就 OK"——PS 的 silent fail / Quirk 经常通过运行时才暴露;
  - 10(记忆)是 long-term 杠杆:没有它,每次都从零设计,copilot 永远是工具;有了它,copilot 才变成"越用越准"的领域
  copilot。

  跟"普通代码 copilot"的差异

  ┌────────────┬─────────────────────┬──────────────────────────────────────────────┐
  │    维度    │  普通代码 copilot   │      Plant Simulation 自动建模 copilot       │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ 输出形态   │ 文本文件(.py / .ts) │ 二进制 + 桥接状态(.spp + PS进程内存对象)     │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ 执行验证   │ pytest / npm test   │ 必须跑 PS 实例 + 收 Stat / TimeSpan 真实数据 │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ 架构选型   │ 框架选型 / 模块拆分 │ 范式选型(离散/连续/推/拉)+ 类继承树3 层      │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ Quirk 处理 │ 语言 Quirk(很常见)  │ 桥接 Quirk + SimTalk Quirk(silent fail 频发) │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ 用户交互   │ 文件 diff           │ 3D 场景可视化 + KPI dashboard                │
  ├────────────┼─────────────────────┼──────────────────────────────────────────────┤
  │ 沉淀价值   │ code snippet        │ 可复用建模模板(整个 Init链 + Frame 结构)     │
  └────────────┴─────────────────────┴──────────────────────────────────────────────┘