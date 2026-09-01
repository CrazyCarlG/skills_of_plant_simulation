### 2026-09-01 by @plant-simulation-experience-curator — `simtalk_run` 单语句限制:`for/next` / `if/then/end` block 全部 "Syntax error near 'print'";必须外层 shell 循环 + 多次 send

- **症状**:在一次 `simtalk_run` 调用里塞多语句 / 控制流,全部报 `Syntax error near 'print'`(错误指向第一行内的 print 关键字):
  ```bash
  python3 simtalk_send.py run '
    var obj : any := str_to_obj(".X")
    for i := 1 to obj.NumChildren:
      print obj.node(i).Name + "|" + obj.node(i).InternalClassType
    next
  '
  # → Syntax error near 'print' (虽然语法本身正确)
  ```
  - 同样失败:`if x > 0 then print "yes"; end`(block form)
  - 同样失败:`var a := 1; var b := 2; print a + b`(多 var 赋值)
- **根因**:`simtalk_run` 的服务端 handler 把整个 `<sim_code>` 当作**单条 SimTalk statement** parse,而不是一段完整的 SimTalk 脚本。SimTalk 自身的 parser 接受多语句 + 控制流,但 bridge 的 wrapper method 在传入时**先做 statement-boundary 切分**(`;` 分号)→ 多语句变成多个 wrapper method 调用,但中间任何一条 statement 包含 `for/next` / `if/end` block 时,block 自身是 1 个 statement,**而 wrapper 把整个 `<sim_code>` 包成 1 个 statement**——block 嵌入就被 parser 拒。
- **Workaround / 结论**:

  ```bash
  # canonical 模式:外层 shell for-loop + 每次 send 一个最小语句
  python3 simtalk_send.py run 'print "###START###"'
  for i in $(seq 1 N); do
      python3 simtalk_send.py run "
        var n := str_to_obj(\".X\").node(${i});
        print \"${i}| \" + n.Name + \"| \" + n.InternalClassType
      " | tee -a dump.txt
  done
  python3 simtalk_send.py run 'print "###END###"'
  ```

  **判定 / 快速试错**:
  - 把 `<sim_code>` 在外部用 `printf` + chr(10) 拼成一个**只有 sequential prints / single statement** 的字符串 → 99% 能跑通
  - 任何 `for/next` / `if/then/end` / `while/next` block → 必须外层 shell 包
  - 多 `var x := ...; var y := ...` 也可能崩(实测 reproduce 不一致,**safe pattern** = 单 var 或全 table 形式)

- **tags**:`simtalk-run`, `single-statement`, `for-next-block-rejected`, `if-end-block-rejected`, `shell-loop-canonical`, `wrapper-statement-boundary`, `silent-failure-mode-8`
- **see also**:`simtalkclaude-v1-and-v2.md §经验 Log exp-005 (.execute() 不刷 .Program 缓存)`;`02-bridge-tool/simtalkclaude-protocol.md §3.1 simtalk_run action`;`skills/local-simtalk-execution/references/lifelines.md §2 simtalk_run 协议`(目前没明确写"单语句"约束);`skills/local-simtalk-execution/log/2026-08-28_agv-50008-discovery.md` Step 4 + §"What this run validated / learned" #1

> 这条经验教会我:
> - **bridge 的 `simtalk_run` ≠ Python `exec()`**:exec 接受任意长字符串,bridge 必须 1 statement。这是 bridge 设计者为了"安全 + 简单"做的限制,但**没有文档化**给 agent。
> - **"单语句" + "simtalk_hasError" 是个强力组合**:`simtalk_hasError("多语句 <body>")` 验证"body 自身语法对",然后 bridge-side `simtalk_run` 单语句 wrapper 跑。
> - **canonical batch pattern**:
>   1. `simtalk_run 'print "###START###"'`
>   2. `for i in $(seq 1 N): simtalk_run '<1-statement per i>'`
>   3. `simtalk_run 'print "###END###"'`
>   4. `readlog` 解析 START/END 之间的输出