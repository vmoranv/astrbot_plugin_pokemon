# 数据库表单设计

本文档描述了插件使用的 SQLite 数据库的表结构设计。

## `db/game_main.db` 设计：

该数据库主要存储游戏的静态元数据和核心配置。

-   `pet_dictionary` # 宠物字典表
    -   `race_id` (INTEGER PRIMARY KEY), # 种族ID `name` (TEXT), # 名称 `evo_level` (INTEGER), # 进化等级 `evolution_stage` (INTEGER), # 进化阶段 
    -   `base_hp` (INTEGER), # 基础HP `base_attack` (INTEGER), # 基础攻击 `base_defence` (INTEGER), # 基础防御 `base_special_attack` (INTEGER), # 基础特攻 `base_special_defence` (INTEGER), # 基础特防 `base_speed` (INTEGER), # 基础速度
    -   `catch_rate` (INTEGER), # 捕捉率 `growth_rate` (TEXT), # 成长率 `attribute_id1` (INTEGER), # 属性1ID `attribute_id2` (INTEGER), # 属性2ID
    -   `height` (REAL), # 身高 `weight` (REAL), # 体重 `description` (TEXT) # 描述
    -   PRIMARY KEY (`race_id`)
-   `pet_system` # 宠物系统相关配置或全局数据表
    -   `system_id` (INTEGER), # 系统ID `system_name` (TEXT), # 系统名称 `system_description` (TEXT), # 系统描述 `system_effect` (TEXT) # 系统效果
    -   PRIMARY KEY (`system_id`)
-   `attributes` # 属性克制表
    -   `attribute_id` (INTEGER PRIMARY KEY), # 属性ID `attribute_name` (TEXT), # 属性名称
    -   `attacking_id` (INTEGER), # 克制属性 `defending_id` (INTEGER), # 微弱属性
    -   `super_effective_id` (INTEGER), # 绝对克制属性 `none_effective_id` (INTEGER), # 无效属性 
    -   PRIMARY KEY (`attribute_id`)
-   `pet_learnable_skills` # 宠物技能学习表
    -   `race_id` (INTEGER), # 种族ID `skill_id` (INTEGER), # 技能ID `learn_method` (TEXT), # 学习方法 `learn_level` (INTEGER), # 学习等级
    -   PRIMARY KEY (`race_id`, `skill_id`, `learn_method`)
-   `skills` # 技能数据表
    -   `skill_id` (INTEGER PRIMARY KEY), # 技能ID `name` (TEXT), # 技能名称 `type` (TEXT), # 技能类型 `power` (INTEGER), # 技能威力
    -   `accuracy` (INTEGER), # 技能命中率 `critical_rate` (INTEGER), # 技能暴击率 `pp` (INTEGER), # 技能PP `category` (TEXT), # 技能分类 `priority` (INTEGER), # 技能优先级 `target_type` (TEXT), # 技能目标类型 
    -   `effect_logic_key` (TEXT), # 效果逻辑键 `description` (TEXT) # 描述
    -   PRIMARY KEY (`skill_id`)
-   `status_effects` # pet状态效果数据表
    -   `status_effect_id` (INTEGER PRIMARY KEY), # 状态效果ID `name` (TEXT), # 状态效果名称 `description` (TEXT), # 状态效果描述 `effect_logic_key` (TEXT), # 效果逻辑键 `length` (INTEGER) # pet状态效果持续回合
    -   PRIMARY KEY (`status_effect_id`)
-   `field_effects` # 场地效果数据表
    -   `field_effect_id` (INTEGER PRIMARY KEY), # 场地效果ID `name` (TEXT), # 场地效果名称 `description` (TEXT), # 场地效果描述 `effect_logic_key` (TEXT), # 效果逻辑键 `length` (INTEGER) # 场地效果持续回合
    -   PRIMARY KEY (`field_effect_id`)
-   `items` # 道具数据表
    -   `item_id` (INTEGER PRIMARY KEY), # 道具ID `name` (TEXT), # 道具名称 `description` (TEXT), # 道具描述 `effect_type` (TEXT), # 道具效果类型 `use_target` (TEXT), # 道具使用目标 `use_effect` (TEXT), # 道具使用效果 `price` (INTEGER), # 道具价格
    -   PRIMARY KEY (`item_id`)
-   `events` # 事件数据表
    -   `event_id` (INTEGER PRIMARY KEY), # 事件ID `name` (TEXT), # 事件名称 `description` (TEXT), # 事件描述 `reward_item_id` (INTEGER) # 奖励道具ID
    -   `dialog_id` (INTEGER), # 对话ID `pet_id` (INTEGER), # 宠物ID
    -   PRIMARY KEY (`event_id`)
-   `npcs` # NPC表
    -   `npc_id` (INTEGER PRIMARY KEY), # NPCID `pet_id` (INTEGER), # 宠物ID `name` (TEXT), # 名称 `interaction_type` (TEXT), # 交互类型 `initial_dialog_id` (INTEGER), # 初始对话ID
    -   PRIMARY KEY (`npc_id`)
-   `dialogs` # 对话数据表
    -   `dialog_id` (INTEGER PRIMARY KEY), # 对话ID `text` (TEXT), # 对话内容 `next_dialog_id` (INTEGER), # 下一个对话ID
    -   `option1_text` (TEXT), # 选项1文本 `option1_next_dialog_id` (INTEGER), # 选项1下一个对话ID
    -   `option2_text` (TEXT), # 选项2文本 `option2_next_dialog_id` (INTEGER), # 选项2下一个对话ID
    -   PRIMARY KEY (`dialog_id`)
-   `tasks` # 任务表
    -   `task_id` (INTEGER PRIMARY KEY), # 任务ID `name` (TEXT), # 任务名称 `description` (TEXT), # 任务描述
    -   `reward_money` (INTEGER), # 奖励金钱 `reward_item_id` (INTEGER), # 奖励道具ID `reward_item_quantity` (INTEGER), # 奖励道具数量
    -   `prerequisite_task_id` (INTEGER), # 前置任务ID `start_dialog_id` (INTEGER), # 开始对话ID `completion_dialog_id` (INTEGER), # 完成对话ID
    -   PRIMARY KEY (`task_id`)
-   `achievements` # 成就表
    -   `achievement_id` (INTEGER PRIMARY KEY), # 成就ID `name` (TEXT), # 成就名称 `description` (TEXT), # 成就描述
    -   PRIMARY KEY (`achievement_id`)
-   `maps` # 地图数据表
    -   `map_id` (INTEGER PRIMARY KEY), # 地图ID `name` (TEXT), # 名称 `description` (TEXT), # 描述 `encounter_rate` (REAL), # 遇敌率 `background_image_path` (TEXT) # 背景图片路径
    -   `npc_id` (INTEGER), # NPCID `common_pet_id` (INTEGER), # 常见宠物ID `common_pet_rate` (REAL), # 常见宠物率 `rare_pet_id` (INTEGER), # 稀有宠物ID `rare_pet_rate` (REAL), # 稀有宠物率 `rare_pet_time` (INTEGER) # 稀有宠物时间
    -   PRIMARY KEY (`map_id`)
-   `shops` # 商店表
    -   `shop_id` (INTEGER PRIMARY KEY), # 商店ID `name` (TEXT), # 名称 `npc_id` (INTEGER), # NPCID `shop_type` (TEXT), # 商店类型 `item_id` (INTEGER), # 道具ID
    -   PRIMARY KEY (`shop_id`)

## `db/game_record.db` 设计：

该数据库主要存储玩家的动态数据和游戏记录。

-   `battle_records` # 战斗记录表
    -   `battle_id` (INTEGER PRIMARY KEY), # 战斗ID `player1_id` (INTEGER), # 玩家1ID `player2_id` (INTEGER), # 玩家2ID
    -   `start_time` (DATETIME), # 开始时间 `end_time` (DATETIME), # 结束时间 `winner_id` (INTEGER), # 胜利者ID `preload_effect_id` (INTEGER), # 预加载特效ID
    -   `skill_target_id` (INTEGER), # 技能目标ID `skill_id` (INTEGER), # 技能ID `status_effect_id` (INTEGER), # 状态效果ID
    -   `field_effect_id` (INTEGER), # 场地效果ID `item_id` (INTEGER), # 道具ID
    -   PRIMARY KEY (`battle_id`)
-   `player_records` # 玩家记录表
    -   `player_id` (INTEGER PRIMARY KEY), # 玩家ID `location_id` (INTEGER), # 位置ID `last_login_time` (DATETIME), # 最后登录时间
    -   `money` (INTEGER), # 金钱 `item_id` (INTEGER), # 道具ID `item_quantity` (INTEGER), # 道具数量
    -   PRIMARY KEY (`player_id`)
-   `player_repository` # 玩家仓库表
    -   `player_id` (INTEGER), # 玩家ID `pet_id` (INTEGER), # 宠物ID `race_id` (INTEGER), # 种族ID
    -   PRIMARY KEY (`player_id`, `pet_id`)
-   `player_party` # 玩家队伍表
    -   `player_id` (INTEGER), # 玩家ID `pet_id` (INTEGER), # 宠物ID
    -   PRIMARY KEY (`player_id`, `pet_id`)
-   `pokemon_instances` # 宠物实例表
    -   `pet_id` (INTEGER PRIMARY KEY), # 宠物ID `race_id` (INTEGER), # 种族ID `nickname` (TEXT), # 昵称
    -   `level` (INTEGER), # 等级 `exp` (INTEGER), # 经验 `current_hp` (INTEGER), # 当前HP `max_hp` (INTEGER), # 最大HP
    -   `attack` (INTEGER), # 攻击 `defence` (INTEGER), # 防御 `special_attack` (INTEGER), # 特攻
    -   `special_defence` (INTEGER), # 特防 `speed` (INTEGER), # 速度
    -   `nature_id` (INTEGER), # 性格ID `ability_id` (INTEGER), # 能力ID
    -   `caught_date` (DATETIME), # 捕捉日期
    -   `skill1_id` (INTEGER), # 技能1ID `skill2_id` (INTEGER), # 技能2ID `skill3_id` (INTEGER), # 技能3ID `skill4_id` (INTEGER), # 技能4ID
    -   `skill1_pp` (INTEGER), # 技能1PP `skill2_pp` (INTEGER), # 技能2PP `skill3_pp` (INTEGER), # 技能3PP `skill4_pp` (INTEGER), # 技能4PP
    -   `is_in_party` (BOOLEAN) # 是否在队伍中
-   `player_quest_progress` # 玩家任务进度表
    -   `player_id` (INTEGER), # 玩家ID `task_id` (INTEGER), # 任务ID `status` (TEXT), # 任务状态
    -   PRIMARY KEY (`player_id`, `task_id`)
-   `player_achievements` # 玩家成就表
    -   `player_id` (INTEGER), # 玩家ID `achievement_id` (INTEGER), # 成就ID `unlock_date` (DATETIME), # 解锁日期
    -   PRIMARY KEY (`player_id`, `achievement_id`)
-   `friends` # 好友表
    -   `player_id` (INTEGER), # 玩家ID `friend_id` (INTEGER), # 好友ID `friendship_date` (DATETIME), # 好友关系建立日期
    -   `friendship_level` (INTEGER), # 好友关系等级
    -   PRIMARY KEY (`player_id`, `friend_id`)

## 索引:

-   `game_main.db`:
    -   `pet_dictionary`: `race_id` (PRIMARY KEY), `name`, `attribute_id1`, `attribute_id2`
    -   `attributes`: `attribute_id` (PRIMARY KEY), `attribute_name`
    -   `items`: `item_id` (PRIMARY KEY), `name`
    -   `maps`: `map_id` (PRIMARY KEY), `name`
    -   `skills`: `skill_id` (PRIMARY KEY), `name`
    -   `status_effects`: `status_effect_id` (PRIMARY KEY), `name`
    -   `field_effects`: `field_effect_id` (PRIMARY KEY), `name`
    -   `dialogs`: `dialog_id` (PRIMARY KEY)
    -   `npcs`: `npc_id` (PRIMARY KEY), `map_id`
    -   `shops`: `shop_id` (PRIMARY KEY), `npc_id`
    -   `shop_items`: `shop_id`, `item_id` (PRIMARY KEY)
    -   `encounters`: `map_id`, `race_id` (PRIMARY KEY)
    -   `evolutions`: `race_id`, `evolves_to_race_id` (PRIMARY KEY)
    -   `pet_learnable_skills`: `race_id`, `skill_id`, `learn_method` (PRIMARY KEY)
-   `game_record.db`:
    -   `battle_records`: `battle_id` (PRIMARY KEY), `player1_id`, `player2_id`
    -   `player_records`: `player_id` (PRIMARY KEY)
    -   `player_repository`: `player_id`, `pet_id` (PRIMARY KEY)
    -   `player_party`: `player_id`, `pet_id` (PRIMARY KEY)
    -   `pokemon_instances`: `pet_id` (PRIMARY KEY), `race_id`, `owner_id`
    -   `player_quest_progress`: `player_id`, `task_id` (PRIMARY KEY)
    -   `player_achievements`: `player_id`, `achievement_id` (PRIMARY KEY)
    -   `friends`: `player_id`, `friend_id` (PRIMARY KEY)

## 外键约束:

-   `game_main.db`:
    -   `pet_dictionary.attribute_id1` REFERENCES `attributes.attribute_id`
    -   `pet_dictionary.attribute_id2` REFERENCES `attributes.attribute_id`
    -   `attributes.attacking_id` REFERENCES `attributes.attribute_id`
    -   `attributes.defending_id` REFERENCES `attributes.attribute_id`
    -   `attributes.super_effective_id` REFERENCES `attributes.attribute_id`
    -   `attributes.none_effective_id` REFERENCES `attributes.attribute_id`
    -   `encounters.map_id` REFERENCES `maps.map_id`
    -   `encounters.race_id` REFERENCES `pet_dictionary.race_id`
    -   `evolutions.race_id` REFERENCES `pet_dictionary.race_id`
    -   `evolutions.evolves_to_race_id` REFERENCES `pet_dictionary.race_id`
    -   `evolutions.evolution_item_id` REFERENCES `items.item_id`
    -   `pet_learnable_skills.race_id` REFERENCES `pet_dictionary.race_id`
    -   `pet_learnable_skills.skill_id` REFERENCES `skills.skill_id`
    -   `npcs.map_id` REFERENCES `maps.map_id`
    -   `npcs.initial_dialog_id` REFERENCES `dialogs.dialog_id`
    -   `shops.npc_id` REFERENCES `npcs.npc_id`
    -   `shop_items.shop_id` REFERENCES `shops.shop_id`
    -   `shop_items.item_id` REFERENCES `items.item_id`
-   `game_record.db`:
    -   `battle_records.player1_id` REFERENCES `player_records.player_id`
    -   `battle_records.player2_id` REFERENCES `player_records.player_id`
    -   `battle_records.winner_id` REFERENCES `player_records.player_id`
    -   `player_records.location_id` REFERENCES `maps.map_id`
    -   `player_records.current_quest_id` REFERENCES `quests.quest_id`
    -   `player_repository.player_id` REFERENCES `player_records.player_id`
    -   `player_repository.pet_id` REFERENCES `pokemon_instances.pet_id`
    -   `player_party.player_id` REFERENCES `player_records.player_id`
    -   `player_party.pet_id` REFERENCES `pokemon_instances.pet_id`
    -   `pokemon_instances.race_id` REFERENCES `pet_dictionary.race_id`
    -   `pokemon_instances.owner_id` REFERENCES `player_records.player_id`
    -   `pokemon_instances.caught_location` REFERENCES `maps.map_id`
    -   `pokemon_instances.nature_id` REFERENCES `natures.nature_id`
    -   `pokemon_instances.ability_id` REFERENCES `abilities.ability_id`
    -   `pokemon_instances.skill1_id` REFERENCES `skills.skill_id`
    -   `pokemon_instances.skill2_id` REFERENCES `skills.skill_id`
    -   `pokemon_instances.skill3_id` REFERENCES `skills.skill_id`
    -   `pokemon_instances.skill4_id` REFERENCES `skills.skill_id`
    -   `player_quest_progress.player_id` REFERENCES `player_records.player_id`
    -   `player_quest_progress.task_id` REFERENCES `tasks.task_id`
    -   `player_achievements.player_id` REFERENCES `player_records.player_id`
    -   `player_achievements.achievement_id` REFERENCES `achievements.achievement_id`
    -   `friends.player_id` REFERENCES `player_records.player_id`
    -   `friends.friend_id` REFERENCES `player_records.player_id`
