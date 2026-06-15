# Preset 配置说明

每个 preset 是一个完整玩法包，目录结构建议如下：

```text
backend/data/presets/<preset_id>/
  preset.json             # 预设清单与玩法入口
  classes.json            # 职业、八维属性、成长、职业技能列表
  skills.json             # 技能数值、目标规则、法力消耗、状态效果
  equipment.json          # 装备池、职业限制、属性/抗性/特效
  enemies.json            # 敌人模板与敌方技能
  dungeon_templates.json  # 副本主题、层、奖励池、词缀池
  affixes.json            # 副本词缀与机制
```

## 启用方式

默认启用 `wod_default`。如需切换 preset，在启动后端前设置环境变量：

```powershell
$env:WOD_PRESET_ID = "my_preset"
uv run uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

也可以在 `backend/data/presets/my_preset/preset.json` 中配置 `files` 指向任意相对路径或绝对路径。

## 可配置项

- `class_ui`：职业图标、颜色、前/中/后排定位、默认目标策略，以及新角色的默认战术：
  - `default_skill_mode`：`balanced` / `aggressive` / `conserve`。
  - `default_initiative_skill`：默认选用的先攻速度公式技能；为空时使用默认速度公式。
  - `default_opening_skill_priority`：每层开场尝试释放的开场技能列表。
  - `default_skill_priority`：普通回合中优先尝试的技能列表；为空则走 `skill_ai` 职业 AI。
  - `default_defense_skill_by_type`：按 `physical` / `ranged` / `magic` / `fire` / `poison` / `curse` / `bleed` 配置被攻击前的防御响应技能。
- `starter_roster`：新游戏初始角色。
- `starter_formations`：新游戏初始双队阵型。
- `starter_equipment`：新游戏初始装备和归属角色。
- `recruit_pool` / `recruit_names`：酒馆招募职业池与姓名池。
- `skill_ai`：职业自动施法优先级，按顺序匹配第一条可用规则。
- `files`：将职业、技能、装备、敌人、副本、词缀表全部纳入 preset。

## 先攻技能与速度公式

技能可以配置为先攻技能：

```json
{
  "type": "passive",
  "tags": ["initiative"],
  "speed_formula": {
    "label": "快速搭箭",
    "normal_speed_weight": 0.15,
    "attribute_weights": { "perception": 0.45, "dexterity": 0.25, "agility": 0.15 },
    "level_weight": 0.12,
    "flat": 0
  }
}
```

先攻技能是“可选的战术项”，不是学会后自动生效。角色的 `tactics.initiative_skill` 为空时，最终 `speed` 使用默认速度公式（常规速度）；选中某个已学会的先攻技能后，最终 `speed` 才切换为该技能的 `speed_formula`。前端战术页会提供“默认速度公式”和所有已学会先攻技能供选择。

调试接口：

- `GET /game/presets`：查看可用 preset。
- `GET /game/preset`：查看当前 preset 展开的全部内容表。
