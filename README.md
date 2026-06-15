# WOD-like SLG MVP

这是依据 `docs/mvp_design.md` 实现的单机类 WOD 冒险小队 MVP 原型。

## 已实现核心闭环

- 30 天局制、每日 2 次远征机会。
- 副本生命周期、词缀、公开情报、侦察情报、战后复盘情报。
- 4 人上阵、6 个初始角色、3×3 阵型、撤退策略与目标优先级。
- 自动回合战斗：速度排序、命中 / 闪避、伤害类型、毒 / 流血 / 诅咒 / 燃烧 / 破甲 / 眩晕等状态。
- 多层副本、层间 HP / 状态 / 技能次数传递。
- 战报：摘要、每层概览、输出 / 承伤 / 治疗 / 状态 / 技能统计、失败原因、机制发现、回合详情。
- 成长与资源：经验升级、金币 / 材料、装备掉落、装备耐久、商店、招募。
- JSON 存档与调试接口。

## 本地运行

### 1. Python / uv 环境

推荐使用 `uv` 管理后端环境：

```powershell
uv venv --python 3.11
uv sync
```

激活环境：

```powershell
.\.venv\Scripts\activate
```

也可以不手动激活，直接用 `uv run ...` 执行命令。

### 2. 后端

```powershell
uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

API 文档：<http://127.0.0.1:8000/docs>

如果已经执行过前端构建，也可以直接访问：<http://127.0.0.1:8000/>

### 3. 前端

```powershell
cd frontend
npm install
npm run dev
```

访问：<http://127.0.0.1:5173>

### 4. 构建前端

```powershell
cd frontend
npm run build
```

构建产物位于 `frontend/dist`，后端会在启动时自动挂载该目录。

## 验证

```powershell
uv run pytest
cd frontend
npm run build
```

## 关键目录

```text
backend/app/main.py                 FastAPI API 入口
backend/app/services/game_service.py 读写存档并组织玩家动作
backend/game_core/engine.py         纯规则核心：世界刷新、战斗、奖励、战报
backend/data/*.json                 数据驱动内容表
backend/data/presets/wod_default    当前默认玩法 preset：职业 / 技能 / 装备 / 敌人 / 副本 / 词缀
backend/saves/save_001.json         MVP JSON 存档
pyproject.toml                      uv / Python 项目配置
uv.lock                             uv 锁文件
frontend/src/App.tsx                React MVP 玩法检验台
frontend/src/api/client.ts          前端 API 客户端
docs/mvp_design.md                  原 MVP 设计文档副本
```
