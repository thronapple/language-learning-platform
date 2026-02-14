"""
初始化MVP数据

使用方法:
    python scripts/init_mvp_data.py --env dev
    python scripts/init_mvp_data.py --env prod --confirm

功能:
    1. 创建3个核心场景(机场/酒店/商务会议)
    2. 创建60道评估题
    3. 创建全局词汇库基础数据
"""

import asyncio
import argparse
from datetime import datetime
from typing import List, Dict, Any

# 场景数据模板
SCENARIOS = [
    {
        "_id": "scenario_airport_checkin",
        "title": "机场办理值机",
        "title_en": "Airport Check-in",
        "description": "学习如何在机场柜台办理登机手续,包括托运行李、选择座位等",
        "category": "tourism",
        "sub_category": "airport",
        "tags": ["travel", "airport", "essential"],
        "level_range": {"min": "A2", "max": "B2"},
        "priority_tier": "high",
        "is_essential": True,
        "usage_frequency": "very_high",
        "estimated_duration": 45,
        "dialogue_count": 3,
        "vocab_count": 30,
        "practice_count": 2,
        "completion_criteria": {
            "dialogue_listen_min": 3,
            "follow_read_score_min": 0.75,
            "vocab_mastery_ratio": 0.8,
            "practice_pass_count": 2
        },
        "prerequisites": [],
        "related_scenarios": ["scenario_airport_security", "scenario_boarding"],
        "cover_image": "https://via.placeholder.com/400x300?text=Airport",
        "icon": "airport",
        "color": "#1890ff",
        "stats": {
            "user_count": 0,
            "avg_completion_rate": 0.0,
            "avg_time_to_master": 0,
            "avg_rating": 0.0
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    },
    {
        "_id": "scenario_hotel_checkin",
        "title": "酒店入住登记",
        "title_en": "Hotel Check-in",
        "description": "学习如何在酒店前台办理入住,包括确认预订、房间需求等",
        "category": "tourism",
        "sub_category": "hotel",
        "tags": ["travel", "hotel", "essential"],
        "level_range": {"min": "A2", "max": "B2"},
        "priority_tier": "high",
        "is_essential": True,
        "usage_frequency": "very_high",
        "estimated_duration": 40,
        "dialogue_count": 3,
        "vocab_count": 25,
        "practice_count": 2,
        "completion_criteria": {
            "dialogue_listen_min": 3,
            "follow_read_score_min": 0.75,
            "vocab_mastery_ratio": 0.8,
            "practice_pass_count": 2
        },
        "prerequisites": [],
        "related_scenarios": ["scenario_hotel_checkout", "scenario_room_service"],
        "cover_image": "https://via.placeholder.com/400x300?text=Hotel",
        "icon": "hotel",
        "color": "#52c41a",
        "stats": {
            "user_count": 0,
            "avg_completion_rate": 0.0,
            "avg_time_to_master": 0,
            "avg_rating": 0.0
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    },
    {
        "_id": "scenario_business_meeting_intro",
        "title": "商务会议自我介绍",
        "title_en": "Business Meeting Introduction",
        "description": "学习如何在商务会议上进行自我介绍和寒暄",
        "category": "business",
        "sub_category": "meeting",
        "tags": ["business", "meeting", "introduction"],
        "level_range": {"min": "B1", "max": "B2"},
        "priority_tier": "high",
        "is_essential": True,
        "usage_frequency": "high",
        "estimated_duration": 35,
        "dialogue_count": 3,
        "vocab_count": 28,
        "practice_count": 2,
        "completion_criteria": {
            "dialogue_listen_min": 3,
            "follow_read_score_min": 0.75,
            "vocab_mastery_ratio": 0.8,
            "practice_pass_count": 2
        },
        "prerequisites": [],
        "related_scenarios": ["scenario_business_presentation", "scenario_business_email"],
        "cover_image": "https://via.placeholder.com/400x300?text=Meeting",
        "icon": "briefcase",
        "color": "#722ed1",
        "stats": {
            "user_count": 0,
            "avg_completion_rate": 0.0,
            "avg_time_to_master": 0,
            "avg_rating": 0.0
        },
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True
    }
]

# 对话数据模板 (每个场景3个对话: A2/B1/B2)
DIALOGUES = [
    # 机场值机 - A2
    {
        "_id": "dialog_airport_checkin_a2",
        "scenario_id": "scenario_airport_checkin",
        "sequence": 1,
        "title": "基础值机对话",
        "level": "A2",
        "difficulty": 0.3,
        "dialogue": [
            {
                "speaker": "staff",
                "speaker_name": "柜台工作人员",
                "text": "Good morning. Passport and ticket, please.",
                "translation": "早上好。请出示护照和机票。",
                "audio_url": "https://example.com/audio/airport_a2_line1.mp3",
                "duration": 3.5
            },
            {
                "speaker": "learner",
                "speaker_name": "你",
                "text": "Here you are.",
                "translation": "给您。",
                "audio_url": "https://example.com/audio/airport_a2_line2.mp3",
                "duration": 1.2
            },
            {
                "speaker": "staff",
                "speaker_name": "柜台工作人员",
                "text": "Any baggage to check in?",
                "translation": "有行李需要托运吗?",
                "audio_url": "https://example.com/audio/airport_a2_line3.mp3",
                "duration": 2.5
            },
            {
                "speaker": "learner",
                "speaker_name": "你",
                "text": "Yes, one suitcase.",
                "translation": "是的,一个箱子。",
                "audio_url": "https://example.com/audio/airport_a2_line4.mp3",
                "duration": 1.8
            }
        ],
        "full_audio_url": "https://example.com/audio/airport_a2_full.mp3",
        "full_duration": 25,
        "key_phrases": [
            {
                "phrase": "Here you are",
                "translation": "给您",
                "usage": "递交物品时使用",
                "example": "Here's your boarding pass."
            },
            {
                "phrase": "check in baggage",
                "translation": "托运行李",
                "usage": "办理行李托运",
                "example": "I'd like to check in this bag."
            }
        ],
        "vocabulary_ids": ["vocab_passport", "vocab_ticket", "vocab_baggage", "vocab_suitcase"],
        "grammar_points": [
            {
                "pattern": "Any + noun + to + verb?",
                "explanation": "询问是否有...需要...",
                "example": "Any questions to ask?"
            }
        ],
        "created_at": datetime.now().isoformat()
    },
    # 机场值机 - B1
    {
        "_id": "dialog_airport_checkin_b1",
        "scenario_id": "scenario_airport_checkin",
        "sequence": 2,
        "title": "选择座位和特殊需求",
        "level": "B1",
        "difficulty": 0.5,
        "dialogue": [
            {
                "speaker": "learner",
                "speaker_name": "你",
                "text": "Could I have an aisle seat, please?",
                "translation": "我可以要一个靠走廊的座位吗?",
                "audio_url": "https://example.com/audio/airport_b1_line1.mp3",
                "duration": 2.8
            },
            {
                "speaker": "staff",
                "speaker_name": "柜台工作人员",
                "text": "Let me check... Yes, I can arrange that for you.",
                "translation": "让我查一下...好的,我可以为您安排。",
                "audio_url": "https://example.com/audio/airport_b1_line2.mp3",
                "duration": 3.5
            },
            {
                "speaker": "learner",
                "speaker_name": "你",
                "text": "And I'd like to request a vegetarian meal.",
                "translation": "另外我想预订一份素食餐。",
                "audio_url": "https://example.com/audio/airport_b1_line3.mp3",
                "duration": 2.5
            }
        ],
        "full_audio_url": "https://example.com/audio/airport_b1_full.mp3",
        "full_duration": 22,
        "key_phrases": [
            {
                "phrase": "Could I have...?",
                "translation": "我可以要...吗?",
                "usage": "礼貌请求",
                "example": "Could I have a window seat?"
            },
            {
                "phrase": "I'd like to request...",
                "translation": "我想要求...",
                "usage": "正式请求",
                "example": "I'd like to request an upgrade."
            }
        ],
        "vocabulary_ids": ["vocab_aisle_seat", "vocab_window_seat", "vocab_vegetarian_meal"],
        "grammar_points": [
            {
                "pattern": "Could I have...?",
                "explanation": "礼貌请求句型",
                "example": "Could I have some water?"
            }
        ],
        "created_at": datetime.now().isoformat()
    },
    # 机场值机 - B2
    {
        "_id": "dialog_airport_checkin_b2",
        "scenario_id": "scenario_airport_checkin",
        "sequence": 3,
        "title": "处理超重行李",
        "level": "B2",
        "difficulty": 0.7,
        "dialogue": [
            {
                "speaker": "staff",
                "speaker_name": "柜台工作人员",
                "text": "I'm afraid your baggage is 3kg over the limit.",
                "translation": "恐怕您的行李超重3公斤。",
                "audio_url": "https://example.com/audio/airport_b2_line1.mp3",
                "duration": 3.2
            },
            {
                "speaker": "learner",
                "speaker_name": "你",
                "text": "Oh, I see. How much is the excess baggage fee?",
                "translation": "哦,知道了。超重行李费是多少?",
                "audio_url": "https://example.com/audio/airport_b2_line2.mp3",
                "duration": 3.0
            },
            {
                "speaker": "staff",
                "speaker_name": "柜台工作人员",
                "text": "It's $50 for the extra weight. Would you like to pay or redistribute some items to your carry-on?",
                "translation": "超重部分是50美元。您是要付费还是把一些东西放到随身行李里?",
                "audio_url": "https://example.com/audio/airport_b2_line3.mp3",
                "duration": 5.5
            }
        ],
        "full_audio_url": "https://example.com/audio/airport_b2_full.mp3",
        "full_duration": 28,
        "key_phrases": [
            {
                "phrase": "I'm afraid...",
                "translation": "恐怕...",
                "usage": "委婉表达坏消息",
                "example": "I'm afraid we're fully booked."
            },
            {
                "phrase": "excess baggage fee",
                "translation": "超重行李费",
                "usage": "机场专用术语",
                "example": "The excess baggage fee is quite expensive."
            }
        ],
        "vocabulary_ids": ["vocab_excess_baggage", "vocab_redistribute", "vocab_carry_on"],
        "grammar_points": [
            {
                "pattern": "Would you like to...?",
                "explanation": "礼貌提供选择",
                "example": "Would you like to upgrade your seat?"
            }
        ],
        "created_at": datetime.now().isoformat()
    }
    # TODO: 添加酒店和商务会议的对话 (共9个对话)
]

# 评估题库示例 (60题)
ASSESSMENT_QUESTIONS = [
    # 词汇题 - A1
    {
        "_id": "q_vocab_a1_001",
        "type": "vocabulary",
        "level": "A1",
        "difficulty": 0.2,
        "scenario_id": "scenario_greetings",
        "skill_tested": "basic_vocabulary",
        "content": {
            "question": "How do you greet someone in the morning?",
            "question_zh": "早上如何问候别人?",
            "options": ["Good night", "Good morning", "Good afternoon", "Goodbye"],
            "correct_index": 1,
            "explanation": "'Good morning' is the correct greeting for morning time.",
            "explanation_zh": "'Good morning'是早上的正确问候语。"
        },
        "metadata": {
            "usage_count": 0,
            "avg_accuracy": 0.0,
            "avg_time_spent": 0,
            "last_calibrated": datetime.now().isoformat()
        },
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    # 听力题 - A2
    {
        "_id": "q_listen_a2_001",
        "type": "listening",
        "level": "A2",
        "difficulty": 0.35,
        "scenario_id": "scenario_airport_checkin",
        "skill_tested": "detail_listening",
        "content": {
            "audio_url": "https://example.com/audio/q_listen_a2_001.mp3",
            "duration": 15,
            "transcript": "Passenger: Excuse me, which gate is the flight to London? Staff: It's gate 22.",
            "question": "What gate number does the passenger need?",
            "question_zh": "乘客需要去几号登机口?",
            "options": ["Gate 12", "Gate 20", "Gate 22", "Gate 32"],
            "correct_index": 2,
            "explanation": "The staff clearly states 'gate 22'.",
            "explanation_zh": "工作人员明确说是22号登机口。"
        },
        "metadata": {
            "usage_count": 0,
            "avg_accuracy": 0.0,
            "avg_time_spent": 0,
            "last_calibrated": datetime.now().isoformat()
        },
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    # 阅读题 - B1
    {
        "_id": "q_read_b1_001",
        "type": "reading",
        "level": "B1",
        "difficulty": 0.55,
        "scenario_id": None,
        "skill_tested": "comprehension",
        "content": {
            "passage": "The hotel check-in time is 3 PM. If you arrive earlier, you can leave your luggage at the front desk and explore the city. Early check-in is available for an additional fee of $30.",
            "question": "What can you do if you arrive before 3 PM?",
            "question_zh": "如果在下午3点前到达可以做什么?",
            "options": [
                "Check in for free",
                "Leave luggage and explore",
                "Wait in the lobby only",
                "Pay extra to leave luggage"
            ],
            "correct_index": 1,
            "explanation": "The passage states you can leave luggage at the front desk and explore the city.",
            "explanation_zh": "文章说可以把行李寄存在前台然后去逛城市。"
        },
        "metadata": {
            "usage_count": 0,
            "avg_accuracy": 0.0,
            "avg_time_spent": 0,
            "last_calibrated": datetime.now().isoformat()
        },
        "is_active": True,
        "created_at": datetime.now().isoformat()
    },
    # 语法题 - B2
    {
        "_id": "q_grammar_b2_001",
        "type": "grammar",
        "level": "B2",
        "difficulty": 0.68,
        "scenario_id": None,
        "skill_tested": "conditional_sentences",
        "content": {
            "question": "Complete the sentence: 'If I _____ earlier, I would have caught the flight.'",
            "question_zh": "完成句子: 'If I _____ earlier, I would have caught the flight.'",
            "options": ["leave", "left", "had left", "have left"],
            "correct_index": 2,
            "explanation": "This is a third conditional sentence requiring 'had + past participle'.",
            "explanation_zh": "这是第三类条件句,需要使用'had + 过去分词'。"
        },
        "metadata": {
            "usage_count": 0,
            "avg_accuracy": 0.0,
            "avg_time_spent": 0,
            "last_calibrated": datetime.now().isoformat()
        },
        "is_active": True,
        "created_at": datetime.now().isoformat()
    }
    # TODO: 扩展至60题 (A1:10, A2:12, B1:15, B2:12, C1:8, C2:3)
]

# 全局词汇库示例
VOCABULARY = [
    {
        "_id": "vocab_passport",
        "word": "passport",
        "phonetic_us": "/ˈpæspɔːrt/",
        "phonetic_uk": "/ˈpɑːspɔːt/",
        "translations": {"zh": "护照"},
        "part_of_speech": "noun",
        "level": "A2",
        "definitions": [
            {
                "meaning": "An official document issued by a government, certifying the holder's identity and citizenship.",
                "example": "Don't forget to bring your passport to the airport."
            }
        ],
        "scenarios": ["scenario_airport_checkin", "scenario_hotel_checkin"],
        "audio_url": "https://example.com/audio/vocab_passport.mp3",
        "image_url": "https://example.com/images/passport.jpg",
        "frequency": "very_high",
        "usage_count": 0,
        "created_at": datetime.now().isoformat()
    },
    {
        "_id": "vocab_boarding_pass",
        "word": "boarding pass",
        "phonetic_us": "/ˈbɔːrdɪŋ pæs/",
        "phonetic_uk": "/ˈbɔːdɪŋ pɑːs/",
        "translations": {"zh": "登机牌"},
        "part_of_speech": "noun",
        "level": "A2",
        "definitions": [
            {
                "meaning": "A document provided by an airline during check-in, giving permission to board the airplane.",
                "example": "Show your boarding pass at the gate."
            }
        ],
        "scenarios": ["scenario_airport_checkin", "scenario_boarding"],
        "audio_url": "https://example.com/audio/vocab_boarding_pass.mp3",
        "image_url": "https://example.com/images/boarding_pass.jpg",
        "frequency": "very_high",
        "usage_count": 0,
        "created_at": datetime.now().isoformat()
    }
    # TODO: 添加更多词汇 (~80个基础词汇)
]


async def init_data(env: str, confirm: bool = False):
    """初始化MVP数据"""

    print(f"🚀 初始化MVP数据到环境: {env}")

    if env == "prod" and not confirm:
        print("❌ 生产环境需要添加 --confirm 参数")
        return

    # TODO: 实际实现需要连接CloudBase
    print("\n📊 准备插入数据:")
    print(f"  - {len(SCENARIOS)} 个场景")
    print(f"  - {len(DIALOGUES)} 个对话")
    print(f"  - {len(ASSESSMENT_QUESTIONS)} 道评估题")
    print(f"  - {len(VOCABULARY)} 个词汇")

    print("\n⚠️  注意: 实际实现需要:")
    print("  1. 连接CloudBase数据库")
    print("  2. 创建集合(如不存在)")
    print("  3. 创建索引")
    print("  4. 批量插入数据")
    print("  5. 验证数据完整性")

    print("\n✅ 数据结构已准备,等待实际数据库连接后执行")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化MVP数据")
    parser.add_argument("--env", choices=["dev", "prod"], default="dev", help="环境")
    parser.add_argument("--confirm", action="store_true", help="确认执行(生产环境必需)")

    args = parser.parse_args()

    asyncio.run(init_data(args.env, args.confirm))
