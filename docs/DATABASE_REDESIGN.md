# 数据库重构设计方案

## 一、现有问题分析

### 1.1 现有设计回顾

**当前集合 (基于`开发计划.md`)**
```
users - 用户档案
content - 学习内容(句子/对话/单词)
progress - 学习进度
vocab - 生词本
plans - 学习计划
orders - 订单意向
events - 埋点事件
wishlists - 愿望单
```

### 1.2 不适应新设计的问题

| 集合 | 问题 | 影响 |
|------|------|------|
| **content** | 未区分"通用内容"vs"场景包" | 无法支持场景化组织 |
| **progress** | 粒度过粗,缺少对话级进度 | 无法计算场景就绪度 |
| **plans** | 缺少评估结果/场景优先级字段 | 无法生成智能计划 |
| **vocab** | SRS字段简单,缺少遗忘曲线 | 复习算法受限 |
| - | **缺少评估相关集合** | 无法存储测试题/结果 |
| - | **缺少同步机制** | 无法支持多端 |
| - | **缺少设备管理** | 无法追踪同步状态 |

---

## 二、重构目标

### 2.1 核心原则

1. **向后兼容**: 保留现有`content/vocab`集合,通过新集合扩展
2. **场景优先**: 数据组织以场景为中心
3. **同步友好**: 所有实体包含版本号和时间戳
4. **性能优化**: 合理冗余,减少JOIN查询
5. **扩展性**: 预留字段支持未来功能

### 2.2 新增核心概念

```
场景包 (Scenario Pack)
  └─ 包含多个对话 (Dialogues)
      └─ 每个对话包含多个句子 (Sentences)

评估会话 (Assessment Session)
  └─ 包含多道题目 (Questions)
      └─ 每题有答题记录 (Answers)

学习计划 (Learning Plan)
  └─ 包含多个场景任务 (Scenario Tasks)
      └─ 每个任务有每日安排 (Daily Activities)
```

---

## 三、重构后的数据库设计

### 3.1 核心集合

#### **`users` (保留,扩展)**

```json
{
  "_id": "openid_123",
  "openid": "openid_123",
  "unionid": "unionid_456",
  "nick": "张三",
  "avatar": "https://cdn.../avatar.jpg",

  "created_at": "2025-09-20T10:00:00Z",
  "last_login": "2025-10-03T20:30:00Z",

  // 新增: 订阅状态
  "subscription": {
    "status": "free",  // free | trial | pro
    "pro_until": null,
    "plan_type": null,
    "trial_started_at": null
  },

  // 新增: 学习偏好
  "preferences": {
    "daily_goal_minutes": 30,
    "notification_enabled": true,
    "notification_times": ["09:00", "20:00"],
    "difficulty_preference": "adaptive"  // easy | adaptive | challenging
  },

  // 新增: 统计摘要(冗余,提升查询性能)
  "stats": {
    "total_study_minutes": 350,
    "total_scenarios_completed": 5,
    "total_vocab_mastered": 120,
    "current_streak": 7,
    "longest_streak": 12,
    "last_study_date": "2025-10-03"
  },

  // 新增: 评估结果
  "latest_assessment": {
    "assessment_id": "assess_20251003",
    "overall_level": "B1",
    "completed_at": "2025-10-03T10:30:00Z",
    "weak_areas": ["grammar", "listening"]
  },

  // 同步字段
  "_version": 15,
  "_updated_at": "2025-10-03T20:30:00Z",
  "_synced": true
}
```

**索引**
```json
[
  { "keys": { "openid": 1 }, "options": { "unique": true } },
  { "keys": { "unionid": 1 } },
  { "keys": { "last_login": -1 } }
]
```

---

#### **`scenarios` (新增)**

场景包元数据

```json
{
  "_id": "scenario_airport_checkin",
  "title": "机场办理值机",
  "title_en": "Airport Check-in",
  "description": "学习如何在机场柜台办理登机手续,包括托运行李、选择座位等",

  "category": "tourism",
  "sub_category": "airport",
  "tags": ["travel", "airport", "essential"],

  // 难度范围
  "level_range": {
    "min": "A2",
    "max": "B2"
  },

  // 优先级配置
  "priority_tier": "high",  // high | medium | low
  "is_essential": true,     // 是否必学场景
  "usage_frequency": "very_high",

  // 学习预估
  "estimated_duration": 45,  // 分钟
  "dialogue_count": 5,
  "vocab_count": 30,
  "practice_count": 3,

  // 完成标准
  "completion_criteria": {
    "dialogue_listen_min": 3,
    "follow_read_score_min": 0.75,
    "vocab_mastery_ratio": 0.8,
    "practice_pass_count": 2
  },

  // 依赖关系
  "prerequisites": [],  // 建议先学的场景
  "related_scenarios": ["airport_security", "boarding"],

  // 元数据
  "cover_image": "https://cdn.../airport_checkin.jpg",
  "icon": "airport",
  "color": "#1890ff",

  // 统计数据(定时更新)
  "stats": {
    "user_count": 1234,
    "avg_completion_rate": 0.87,
    "avg_time_to_master": 38,  // 分钟
    "avg_rating": 4.6
  },

  "created_at": "2025-09-01T00:00:00Z",
  "updated_at": "2025-10-01T00:00:00Z",
  "is_active": true
}
```

**索引**
```json
[
  { "keys": { "category": 1, "sub_category": 1 } },
  { "keys": { "priority_tier": 1, "is_essential": -1 } },
  { "keys": { "tags": 1 } }
]
```

---

#### **`scenario_dialogues` (新增)**

场景内的对话内容

```json
{
  "_id": "dialog_airport_checkin_basic",
  "scenario_id": "scenario_airport_checkin",
  "sequence": 1,  // 场景内排序

  "title": "基础值机对话",
  "level": "A2",
  "difficulty": 0.3,  // 0-1

  // 对话内容
  "dialogue": [
    {
      "speaker": "staff",
      "speaker_name": "柜台工作人员",
      "text": "Good morning. Passport and ticket, please.",
      "translation": "早上好。请出示护照和机票。",
      "audio_url": "https://cdn.../dialog_001_line_001.mp3",
      "duration": 3.5
    },
    {
      "speaker": "learner",
      "speaker_name": "你",
      "text": "Here you are.",
      "translation": "给您。",
      "audio_url": "https://cdn.../dialog_001_line_002.mp3",
      "duration": 1.2
    }
  ],

  // 完整音频
  "full_audio_url": "https://cdn.../dialog_001_full.mp3",
  "full_duration": 25,

  // 关键短语
  "key_phrases": [
    {
      "phrase": "Here you are",
      "translation": "给您",
      "usage": "递交物品时使用",
      "example": "Here's your boarding pass."
    }
  ],

  // 词汇引用
  "vocabulary_ids": [
    "vocab_boarding_pass",
    "vocab_passport",
    "vocab_baggage"
  ],

  // 语法点
  "grammar_points": [
    {
      "pattern": "Could I have...?",
      "explanation": "礼貌请求",
      "example": "Could I have a window seat?"
    }
  ],

  "created_at": "2025-09-01T00:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "scenario_id": 1, "sequence": 1 } },
  { "keys": { "level": 1 } }
]
```

---

#### **`vocabulary` (新增,替代旧vocab)**

全局词汇库

```json
{
  "_id": "vocab_boarding_pass",
  "word": "boarding pass",
  "phonetic_us": "/ˈbɔːrdɪŋ pæs/",
  "phonetic_uk": "/ˈbɔːdɪŋ pɑːs/",

  "translations": {
    "zh": "登机牌",
    "ja": "搭乗券",
    "ko": "탑승권"
  },

  "part_of_speech": "noun",
  "level": "A2",

  "definitions": [
    {
      "meaning": "A document provided by an airline during check-in, giving a passenger permission to board the airplane.",
      "example": "Don't forget to show your boarding pass at the gate."
    }
  ],

  // 关联场景
  "scenarios": ["airport_checkin", "boarding"],

  // 音频
  "audio_url": "https://cdn.../vocab_boarding_pass.mp3",

  // 图片
  "image_url": "https://cdn.../boarding_pass.jpg",

  // 词频统计
  "frequency": "high",
  "usage_count": 5678,

  "created_at": "2025-09-01T00:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "word": 1 }, "options": { "unique": true } },
  { "keys": { "level": 1 } },
  { "keys": { "scenarios": 1 } }
]
```

---

#### **`user_vocabulary` (新增)**

用户的个人生词本(SRS数据)

```json
{
  "_id": "uv_user123_boarding_pass",
  "user_id": "openid_123",
  "vocabulary_id": "vocab_boarding_pass",

  // 冗余字段(提升查询性能)
  "word": "boarding pass",
  "translation": "登机牌",

  // SRS算法字段
  "srs": {
    "level": 3,  // 0-7, SuperMemo SM-2算法
    "ease_factor": 2.5,
    "interval_days": 7,
    "next_review_at": "2025-10-10T09:00:00Z",
    "last_review_at": "2025-10-03T20:00:00Z",
    "total_reviews": 5,
    "correct_count": 4,
    "accuracy": 0.8
  },

  // 学习状态
  "status": "learning",  // new | learning | mastered | archived
  "mastered_at": null,

  // 来源场景
  "learned_from": {
    "scenario_id": "scenario_airport_checkin",
    "dialogue_id": "dialog_airport_checkin_basic",
    "added_at": "2025-10-01T10:00:00Z"
  },

  // 用户笔记
  "notes": "机场值机必备",
  "tags": ["urgent", "travel"],

  // 同步字段
  "_version": 8,
  "_updated_at": "2025-10-03T20:00:00Z",
  "_synced": true,

  "created_at": "2025-10-01T10:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "vocabulary_id": 1 }, "options": { "unique": true } },
  { "keys": { "user_id": 1, "srs.next_review_at": 1 } },
  { "keys": { "user_id": 1, "status": 1 } }
]
```

---

#### **`assessment_questions` (新增)**

评估题库

```json
{
  "_id": "q_listen_b1_airport_001",
  "type": "listening",  // listening | reading | vocabulary | grammar
  "level": "B1",
  "difficulty": 0.65,  // IRT难度参数

  // 所属场景
  "scenario_id": "scenario_airport_checkin",
  "skill_tested": "detail_listening",

  // 题目内容
  "content": {
    "audio_url": "https://cdn.../q_listen_b1_airport_001.mp3",
    "duration": 25,
    "transcript": "Excuse me, which gate is the flight to London?",

    "question": "What information does the passenger need?",
    "question_zh": "乘客需要什么信息?",

    "options": [
      "Boarding time",
      "Gate number",
      "Seat number",
      "Baggage claim"
    ],
    "correct_index": 1,

    "explanation": "The passenger asks 'which gate', so they need the gate number.",
    "explanation_zh": "乘客问'哪个登机口',所以需要登机口号码。"
  },

  // 题目元数据(定时更新)
  "metadata": {
    "usage_count": 1234,
    "avg_accuracy": 0.72,
    "avg_time_spent": 15,  // 秒
    "last_calibrated": "2025-10-01T00:00:00Z"
  },

  "is_active": true,
  "created_at": "2025-09-01T00:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "type": 1, "level": 1, "difficulty": 1 } },
  { "keys": { "scenario_id": 1 } }
]
```

---

#### **`assessments` (新增)**

评估会话记录

```json
{
  "_id": "assess_user123_20251003",
  "user_id": "openid_123",
  "started_at": "2025-10-03T10:00:00Z",
  "completed_at": "2025-10-03T10:09:30Z",
  "duration_secs": 570,
  "status": "completed",  // in_progress | completed | abandoned

  // 评估结果
  "results": {
    "overall_level": "B1",
    "ability_score": 0.15,  // IRT能力值 (-3到3)
    "confidence": 0.85,

    "dimensions": {
      "listening": { "level": "B2", "accuracy": 0.83, "ability": 0.5 },
      "reading": { "level": "B1", "accuracy": 0.75, "ability": 0.1 },
      "vocabulary": { "level": "B1", "accuracy": 0.67, "ability": 0.0 },
      "grammar": { "level": "A2", "accuracy": 0.50, "ability": -0.3 }
    },

    "weak_areas": ["grammar", "vocabulary"],
    "strong_areas": ["listening"]
  },

  // 答题记录
  "questions": [
    {
      "question_id": "q_vocab_b1_001",
      "type": "vocabulary",
      "level": "B1",
      "difficulty": 0.6,
      "is_correct": true,
      "time_spent": 12,
      "answer_selected": 2
    }
  ],

  // 推荐
  "recommendations": {
    "suggested_scenarios": ["business_meeting", "hotel_checkin"],
    "focus_areas": ["grammar_basics", "business_vocabulary"],
    "estimated_study_days": 14
  },

  "_version": 1,
  "_updated_at": "2025-10-03T10:09:30Z",
  "created_at": "2025-10-03T10:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "completed_at": -1 } },
  { "keys": { "status": 1 } }
]
```

---

#### **`learning_plans` (新增,替代plans)**

学习计划

```json
{
  "_id": "plan_user123_20251003",
  "user_id": "openid_123",
  "created_at": "2025-10-03T11:00:00Z",
  "status": "active",  // active | completed | paused | expired

  // 目标设定
  "goal": {
    "type": "business_trip",
    "description": "德国商务出差",
    "target_date": "2025-10-17",
    "days_available": 14,
    "daily_minutes": 30
  },

  // 评估基线
  "baseline_assessment": {
    "assessment_id": "assess_user123_20251003",
    "overall_level": "B1",
    "weak_areas": ["grammar", "listening"]
  },

  // 场景选择
  "selected_scenarios": [
    {
      "scenario_id": "scenario_airport_checkin",
      "priority": 0.95,
      "allocated_minutes": 60,
      "target_readiness": 0.9,
      "current_readiness": 0.45,
      "status": "in_progress",
      "scheduled_days": [1, 2, 5, 8, 12]
    }
  ],

  // 每日计划
  "daily_plans": [
    {
      "day": 1,
      "date": "2025-10-03",
      "tasks": [
        {
          "scenario_id": "scenario_airport_checkin",
          "dialogue_id": "dialog_airport_checkin_basic",
          "duration": 20,
          "activities": [
            { "type": "listen", "times": 2, "duration": 6 },
            { "type": "follow_read", "times": 3, "duration": 9 },
            { "type": "vocab_review", "count": 5, "duration": 5 }
          ],
          "completed": true,
          "completed_at": "2025-10-03T20:30:00Z",
          "actual_duration": 22
        }
      ],
      "total_planned": 30,
      "total_actual": 22,
      "completion_rate": 1.0,
      "checked_in": true
    }
  ],

  // 整体进度
  "overall_progress": {
    "total_scenarios": 8,
    "completed_scenarios": 2,
    "in_progress_scenarios": 3,
    "avg_readiness": 0.58,
    "total_minutes_studied": 150,
    "days_elapsed": 5,
    "days_remaining": 9,
    "on_track": true
  },

  // 连续打卡
  "streak": {
    "current": 5,
    "longest": 7,
    "last_checkin": "2025-10-03"
  },

  // 动态调整记录
  "adjustments": [
    {
      "date": "2025-10-05",
      "reason": "scenario_behind_schedule",
      "scenario_id": "scenario_hotel_checkin",
      "action": "boosted_priority",
      "old_priority": 0.75,
      "new_priority": 0.90
    }
  ],

  "_version": 18,
  "_updated_at": "2025-10-03T20:30:00Z",
  "_synced": true
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "status": 1 } },
  { "keys": { "user_id": 1, "created_at": -1 } }
]
```

---

#### **`scenario_progress` (新增)**

用户场景学习进度

```json
{
  "_id": "sp_user123_airport_checkin",
  "user_id": "openid_123",
  "scenario_id": "scenario_airport_checkin",
  "plan_id": "plan_user123_20251003",

  "started_at": "2025-10-03T10:00:00Z",
  "last_practiced": "2025-10-05T20:30:00Z",
  "status": "in_progress",  // not_started | in_progress | completed | mastered

  // 对话进度
  "dialogue_progress": [
    {
      "dialogue_id": "dialog_airport_checkin_basic",
      "listen_count": 5,
      "follow_read_attempts": 8,
      "best_score": 0.88,
      "last_score": 0.85,
      "avg_score": 0.82,
      "mastered": true,
      "first_practiced": "2025-10-03T10:05:00Z",
      "last_practiced": "2025-10-05T20:00:00Z"
    }
  ],

  // 词汇进度
  "vocabulary_progress": {
    "total": 30,
    "learned": 25,
    "mastered": 18,
    "review_due": 7,
    "next_review_at": "2025-10-06T09:00:00Z"
  },

  // 练习结果
  "practice_results": [
    {
      "practice_id": "prac_dialogue_completion_001",
      "type": "dialogue_completion",
      "passed": true,
      "score": 0.9,
      "completed_at": "2025-10-05T20:25:00Z"
    }
  ],

  // 就绪度计算
  "readiness": 0.78,
  "readiness_breakdown": {
    "dialogue_completion": 0.85,
    "follow_read_quality": 0.82,
    "vocab_mastery": 0.75,
    "practice_pass_rate": 1.0
  },

  "completed": false,
  "completed_at": null,

  // 时间统计
  "time_spent": {
    "total_minutes": 65,
    "listen": 20,
    "follow_read": 30,
    "vocab_review": 10,
    "practice": 5
  },

  "_version": 12,
  "_updated_at": "2025-10-05T20:30:00Z",
  "_synced": true,

  "created_at": "2025-10-03T10:00:00Z"
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "scenario_id": 1 }, "options": { "unique": true } },
  { "keys": { "user_id": 1, "status": 1 } },
  { "keys": { "plan_id": 1 } }
]
```

---

#### **`sync_changes` (新增)**

多端同步变更日志

```json
{
  "_id": "sync_12345",
  "user_id": "openid_123",
  "entity_type": "user_vocabulary",
  "entity_id": "uv_user123_boarding_pass",
  "action": "update",  // create | update | delete

  "version": 12,
  "updated_at": "2025-10-03T20:30:15.123Z",
  "updated_by": "device_iphone_abc",

  "data": {
    "word": "boarding pass",
    "srs": { "level": 3, "next_review_at": "2025-10-05T09:00:00Z" }
  },

  "tombstone": false,
  "synced_devices": ["device_iphone_abc"],

  "created_at": "2025-10-03T20:30:15.123Z"
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "version": 1 } },
  { "keys": { "user_id": 1, "entity_type": 1, "entity_id": 1 } },
  { "keys": { "created_at": 1 }, "options": { "expireAfterSeconds": 2592000 } }
]
```

---

#### **`user_devices` (新增)**

用户设备管理

```json
{
  "_id": "device_iphone_abc123",
  "user_id": "openid_123",
  "device_id": "abc123",
  "device_type": "ios",  // ios | android | web | desktop
  "device_name": "iPhone 13",
  "device_model": "iPhone14,5",

  "last_sync_at": "2025-10-03T20:30:00Z",
  "last_sync_version": 15,

  "registered_at": "2025-09-20T10:00:00Z",
  "last_active_at": "2025-10-03T20:35:00Z",

  "is_active": true
}
```

**索引**
```json
[
  { "keys": { "user_id": 1, "device_id": 1 }, "options": { "unique": true } },
  { "keys": { "last_active_at": -1 } }
]
```

---

### 3.2 保留集合(兼容性)

#### **`content` (保留,逐步废弃)**

```json
{
  "_id": "content_001",
  "type": "sentence",
  "text": "Good morning.",
  "audio_url": "https://cdn.../good_morning.mp3",
  "level": "A1",

  // 新增: 关联场景
  "migrated_to": {
    "scenario_id": "scenario_greetings",
    "dialogue_id": "dialog_greetings_basic"
  },

  "_deprecated": true
}
```

#### **`events` (保留)**

埋点事件日志,无需改动

```json
{
  "_id": "event_123456",
  "user_id": "openid_123",
  "event": "scenario_completed",
  "props": {
    "scenario_id": "scenario_airport_checkin",
    "readiness": 0.92,
    "time_spent": 65
  },
  "ts": "2025-10-03T20:30:00Z"
}
```

#### **`orders`/`wishlists` (保留)**

订单和愿望单,无需改动

---

## 四、数据迁移方案

### 4.1 迁移策略

**双写模式(Dual Write)**
```
新数据 → 同时写入新旧集合
旧数据 → 异步批量迁移
读取 → 优先新集合,兜底旧集合
```

### 4.2 迁移脚本

**Step 1: 创建新集合**
```python
# scripts/migrate_create_collections.py

async def create_new_collections():
    collections = [
        "scenarios",
        "scenario_dialogues",
        "vocabulary",
        "user_vocabulary",
        "assessment_questions",
        "assessments",
        "learning_plans",
        "scenario_progress",
        "sync_changes",
        "user_devices"
    ]

    for coll in collections:
        await db.create_collection(coll)
        print(f"✓ Created collection: {coll}")

    await create_indexes()
```

**Step 2: 迁移content → scenarios + dialogues**
```python
# scripts/migrate_content_to_scenarios.py

async def migrate_content():
    # 按场景分组旧content
    old_contents = await db.collection("content").find({})

    scenarios_map = group_by_scenario(old_contents)

    for scenario_key, contents in scenarios_map.items():
        # 创建scenario
        scenario = create_scenario_from_contents(contents)
        scenario_id = await db.collection("scenarios").insert(scenario)

        # 创建dialogues
        for idx, content in enumerate(contents):
            dialogue = create_dialogue_from_content(content, scenario_id, idx)
            await db.collection("scenario_dialogues").insert(dialogue)

        print(f"✓ Migrated scenario: {scenario_id}")
```

**Step 3: 迁移vocab → user_vocabulary**
```python
# scripts/migrate_vocab.py

async def migrate_vocab():
    old_vocabs = await db.collection("vocab").find({})

    for old_vocab in old_vocabs:
        # 创建全局vocabulary(如不存在)
        vocab_id = await ensure_global_vocabulary(old_vocab["word"])

        # 创建user_vocabulary
        user_vocab = {
            "_id": f"uv_{old_vocab['user_id']}_{vocab_id}",
            "user_id": old_vocab["user_id"],
            "vocabulary_id": vocab_id,
            "word": old_vocab["word"],
            "translation": old_vocab.get("meaning"),
            "srs": {
                "level": old_vocab.get("srs_level", 0),
                "next_review_at": old_vocab.get("next_review_at"),
                "interval_days": calculate_interval(old_vocab.get("srs_level", 0))
            },
            "status": "learning",
            "created_at": old_vocab.get("created_at"),
            "_version": 1,
            "_synced": False
        }

        await db.collection("user_vocabulary").insert(user_vocab)

    print(f"✓ Migrated {len(old_vocabs)} vocab items")
```

**Step 4: 迁移plans → learning_plans**
```python
# scripts/migrate_plans.py

async def migrate_plans():
    old_plans = await db.collection("plans").find({})

    for old_plan in old_plans:
        new_plan = {
            "_id": f"plan_{old_plan['user_id']}_{old_plan['created_at']}",
            "user_id": old_plan["user_id"],
            "goal": {
                "type": "general_learning",
                "daily_minutes": old_plan.get("quota_items", 30)
            },
            "selected_scenarios": [],
            "daily_plans": [],
            "overall_progress": {
                "total_minutes_studied": 0
            },
            "streak": {
                "current": 0,
                "longest": 0
            },
            "status": "active",
            "created_at": old_plan.get("created_at"),
            "_version": 1
        }

        await db.collection("learning_plans").insert(new_plan)

    print(f"✓ Migrated {len(old_plans)} plans")
```

### 4.3 验证脚本

```python
# scripts/validate_migration.py

async def validate_migration():
    errors = []

    # 检查数据完整性
    old_vocab_count = await db.collection("vocab").count_documents({})
    new_vocab_count = await db.collection("user_vocabulary").count_documents({})

    if old_vocab_count != new_vocab_count:
        errors.append(f"Vocab count mismatch: {old_vocab_count} vs {new_vocab_count}")

    # 检查外键完整性
    orphaned = await db.collection("user_vocabulary").aggregate([
        {
            "$lookup": {
                "from": "vocabulary",
                "localField": "vocabulary_id",
                "foreignField": "_id",
                "as": "vocab"
            }
        },
        { "$match": { "vocab": { "$size": 0 } } }
    ]).to_list(None)

    if orphaned:
        errors.append(f"Found {len(orphaned)} orphaned user_vocabulary records")

    if errors:
        print("❌ Validation failed:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ Validation passed")
        return True
```

---

## 五、API适配

### 5.1 向后兼容层

```python
# app/repositories/compat_layer.py

class CompatibilityRepository:
    """提供旧API的兼容性包装"""

    async def get_vocab_list_legacy(self, user_id: str) -> list[dict]:
        """兼容旧的GET /vocab接口"""
        # 读取新表
        user_vocabs = await self.db.query(
            collection="user_vocabulary",
            filter={"user_id": user_id}
        )

        # 转换为旧格式
        return [
            {
                "word": uv["word"],
                "meaning": uv.get("translation"),
                "srs_level": uv["srs"]["level"],
                "next_review_at": uv["srs"]["next_review_at"]
            }
            for uv in user_vocabs
        ]
```

### 5.2 新API路由

```python
# app/routes/scenarios.py

@router.get("/scenarios")
async def list_scenarios(
    category: str = None,
    level: str = None,
    user: User = Depends(get_current_user)
) -> list[Scenario]:
    """获取场景列表"""
    filters = {"is_active": True}

    if category:
        filters["category"] = category
    if level:
        filters["level_range.min"] = {"$lte": level}
        filters["level_range.max"] = {"$gte": level}

    scenarios = await scenario_repo.find(filters)
    return scenarios


@router.get("/scenarios/{scenario_id}/dialogues")
async def get_scenario_dialogues(
    scenario_id: str,
    user: User = Depends(get_current_user)
) -> list[Dialogue]:
    """获取场景对话"""
    dialogues = await dialogue_repo.find(
        {"scenario_id": scenario_id},
        sort={"sequence": 1}
    )
    return dialogues
```

---

## 六、性能优化

### 6.1 索引策略

**复合索引**
```json
// user_vocabulary: 支持"今日复习"查询
{ "keys": { "user_id": 1, "srs.next_review_at": 1, "status": 1 } }

// scenario_progress: 支持"用户当前学习场景"查询
{ "keys": { "user_id": 1, "status": 1, "last_practiced": -1 } }

// assessments: 支持"用户历史评估"查询
{ "keys": { "user_id": 1, "completed_at": -1 } }
```

### 6.2 数据冗余

**场景进度冗余词汇计数**
```json
{
  "scenario_progress": {
    "vocabulary_progress": {
      "total": 30,        // 冗余,避免JOIN
      "mastered": 18      // 冗余,避免聚合查询
    }
  }
}
```

**用户统计冗余**
```json
{
  "users": {
    "stats": {
      "total_study_minutes": 350,  // 冗余,定时从events聚合
      "current_streak": 7           // 冗余,从plans计算
    }
  }
}
```

### 6.3 缓存策略

```python
# 场景元数据(变化少,缓存1小时)
@cache(ttl=3600)
async def get_scenario(scenario_id: str) -> Scenario:
    return await scenario_repo.get(scenario_id)

# 用户进度(变化频繁,缓存5分钟)
@cache(ttl=300)
async def get_user_progress(user_id: str, scenario_id: str) -> Progress:
    return await progress_repo.get(user_id, scenario_id)
```

---

## 七、回滚方案

### 7.1 回滚策略

**阶段1: 双写期(Week 1-2)**
- 新旧集合同时写入
- 读取优先新集合
- 可随时切回旧集合

**阶段2: 新表主导(Week 3-4)**
- 仅写入新集合
- 读取仅新集合
- 保留旧集合备份

**阶段3: 清理(Week 5+)**
- 归档旧集合
- 删除兼容层代码

### 7.2 回滚脚本

```python
# scripts/rollback_to_old_schema.py

async def rollback():
    # 停止写入新集合
    await toggle_feature_flag("NEW_SCHEMA_ENABLED", False)

    # 重新激活旧路由
    await toggle_feature_flag("LEGACY_API_ENABLED", True)

    print("✓ Rolled back to old schema")
```

---

## 八、验收标准

### 8.1 功能验收

- [ ] 所有新API接口可正常调用
- [ ] 旧API通过兼容层继续工作
- [ ] 数据迁移脚本无错误
- [ ] 验证脚本通过所有检查

### 8.2 性能验收

- [ ] 场景列表查询 < 200ms
- [ ] 用户进度查询 < 150ms
- [ ] 今日复习词汇查询 < 100ms
- [ ] 同步接口延迟 < 500ms

### 8.3 数据一致性

- [ ] 新旧数据数量一致
- [ ] 无孤儿记录
- [ ] 外键引用完整

---

## 九、时间规划

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| **Week 1** | 创建新集合 + 索引 | 1天 |
|  | 迁移脚本开发 | 2天 |
|  | 验证脚本开发 | 1天 |
|  | 执行迁移(灰度) | 1天 |
| **Week 2** | 新API开发 | 3天 |
|  | 兼容层开发 | 1天 |
|  | 集成测试 | 1天 |
| **Week 3** | 前端适配 | 3天 |
|  | 性能优化 | 2天 |
| **Week 4** | 全量发布 | 1天 |
|  | 监控观察 | 4天 |

**总计: 20天**

---

## 十、风险与应对

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|----------|
| 迁移脚本错误导致数据丢失 | 低 | 高 | 分批迁移,每批验证,保留备份 |
| 新表性能不如预期 | 中 | 中 | 灰度发布,对比性能指标,快速回滚 |
| 前端适配周期长 | 中 | 低 | 兼容层保证旧API可用,前端逐步迁移 |
| 同步逻辑复杂度高 | 高 | 中 | MVP先实现轮询,WebSocket后期优化 |

---

**下一步**: 基于此方案生成迁移脚本和新API路由代码
