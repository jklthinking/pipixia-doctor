ipixia-doctor/
├── SKILL.md / README.md / PRD.md   # 文档
├── scripts/doctor.py               # 统一CLI入口
├── scripts/agent_snapshot.py       # Agent快照与恢复（v5.1）
├── scripts/rx_learner.py           # 药方自学习引擎（v5.1）
├── scripts/{doctor_check,prescription_match,repair_plan,doctor_record,case_search,feishu_route,validate_skill}.py
├── references/                     # 药方库/安全策略/测试用例
├── skills/                         # 子Skill（hermes-check/prescription-match/repair-plan/case-record/case-search/feishu-route）
└── .doctor/cases/                  # 病历存档
```

## 安全策略

| 等级 | 操作类型 | 默认行为 |
|------|---------|---------|
| L0 | 只读检查 | 自动执行 |
| L1 | 低风险写入（如补缺失模板） | 先询问 |
| L2 | 中风险（安装依赖/改配置/授权） | 展示影响后询问 |
| L3 | 高风险（删除/覆盖/重置/涉隐私） | 默认不执行 |

> **硬边界**: 不收集 Cookie/Token/密码/私钥，不绕过登录/CAPTCHA/反爬，不静默删除/覆盖/重置。


---

## 工作流

- [ ] 1. 确认用户需求和诊断场景
- [ ] 2. 加载Agent配置和运行日志
- [ ] 3. 执行健康诊断（插件/工具/记忆/安全）
- [ ] 4. 生成诊断报告和修复建议
- [ ] 5. 验证修复效果


---

## 技术架构

- **诊断引擎**: 多维度Agent健康检查（插件完整性/工具调用/记忆一致性/安全策略）
- **自愈机制**: 检测→定位→修复→验证闭环
- **数据管线**: 日志采集→模式匹配→异常检测→报告生成
- **API接口**: Python SDK + CLI工具 + Hermes Agent集成

## 2026-07-03 运行时增强

- 新增检索过滤注入探针，拦截未知过滤键、空值和危险过滤片段。
- 验证：新增模块通过 py_compile 和定向 pytest，代码不依赖外部服务。

## 2026-07-03 产品收敛门禁

- 新增 `scripts/product_convergence_gate.py`：从远端干净 clone 后可运行 `python3 scripts/product_convergence_gate.py --json`，检查 SKILL/README、入口文件、smoke 目标、测试与外部融合引用是否自洽。
- 新增 `tests/test_product_convergence_gate.py`：确保门禁在产品仓库中真实可执行，避免后续增强只停留在孤岛模块。

## 一键开箱交付

本仓库提供标准一键入口：

- `install.sh`：用户的一条命令安装与冒烟入口。
- `scripts/setup.py`：安装声明依赖并串联 doctor。
- `scripts/doctor.py`：检查 README、SKILL、入口脚本、package scripts 与产品收敛门禁。
- `scripts/smoke.py`：运行 doctor、产品收敛门禁与 Python 编译级冒烟。
- `tests/test_one_click_open_box.py`：契约测试，防止 README 写了但脚本缺失。


## Lark Coding Agent Bridge 融合增强

- 皮皮虾医生新增 Bridge Repair Advisor：stream idle、workspace missing、Codex JSONL drift、profile crosstalk 修复建议。
- 新增模块：`diagnostics/resurrection_bridge_repair.py`
- 来源模式：飞书/Lark 消息入口、本地 Claude/Codex 执行、会话 fingerprint、profile 隔离与安全门禁。

## Generic orchestration repair plans

Adds deterministic repair planning for drift, stale pending events, poison events, missing flow logs, and broken confirmation states.
