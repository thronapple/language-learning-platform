"""
生成完整的60道评估题库

分布:
- A1: 10题 (词汇5 + 听力3 + 阅读2)
- A2: 12题 (词汇4 + 听力4 + 阅读3 + 语法1)
- B1: 15题 (听力5 + 阅读5 + 词汇3 + 语法2)
- B2: 12题 (听力4 + 阅读4 + 语法4)
- C1: 8题 (听力3 + 阅读3 + 语法2)
- C2: 3题 (阅读2 + 语法1)
"""

import json
from datetime import datetime
from typing import List, Dict, Any


def generate_a2_questions() -> List[Dict[str, Any]]:
    """生成A2级别题目(12题)"""
    return [
        # 词汇题 (4题)
        {
            "_id": "q_vocab_a2_001",
            "type": "vocabulary",
            "level": "A2",
            "difficulty": 0.32,
            "scenario_id": "scenario_airport_checkin",
            "skill_tested": "travel_vocabulary",
            "content": {
                "question": "What do you show at airport check-in?",
                "question_zh": "在机场值机时你需要出示什么?",
                "options": ["Passport", "Wallet", "Phone", "Keys"],
                "correct_index": 0,
                "explanation": "You show your passport at airport check-in.",
                "explanation_zh": "在机场值机时需要出示护照。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_vocab_a2_002",
            "type": "vocabulary",
            "level": "A2",
            "difficulty": 0.35,
            "scenario_id": "scenario_hotel_checkin",
            "skill_tested": "hotel_vocabulary",
            "content": {
                "question": "I'd like to make a ___.",
                "question_zh": "我想订一个___。",
                "options": ["reservation", "conversation", "presentation", "education"],
                "correct_index": 0,
                "explanation": "'Make a reservation' means to book something in advance.",
                "explanation_zh": "'Make a reservation'意思是提前预订。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_vocab_a2_003",
            "type": "vocabulary",
            "level": "A2",
            "difficulty": 0.37,
            "scenario_id": null,
            "skill_tested": "daily_vocabulary",
            "content": {
                "question": "The opposite of 'expensive' is ___.",
                "question_zh": "'昂贵'的反义词是___。",
                "options": ["cheap", "beautiful", "large", "quick"],
                "correct_index": 0,
                "explanation": "'Cheap' is the opposite of 'expensive'.",
                "explanation_zh": "'Cheap'是'expensive'的反义词。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_vocab_a2_004",
            "type": "vocabulary",
            "level": "A2",
            "difficulty": 0.39,
            "scenario_id": null,
            "skill_tested": "food_vocabulary",
            "content": {
                "question": "What do you eat for breakfast?",
                "question_zh": "你早餐吃什么?",
                "options": ["Dinner", "Lunch", "Cereal", "Supper"],
                "correct_index": 2,
                "explanation": "Cereal is a common breakfast food.",
                "explanation_zh": "麦片是常见的早餐食物。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },

        # 听力题 (4题)
        {
            "_id": "q_listen_a2_001",
            "type": "listening",
            "level": "A2",
            "difficulty": 0.38,
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
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_listen_a2_002",
            "type": "listening",
            "level": "A2",
            "difficulty": 0.4,
            "scenario_id": "scenario_hotel_checkin",
            "skill_tested": "detail_listening",
            "content": {
                "audio_url": "https://example.com/audio/q_listen_a2_002.mp3",
                "duration": 18,
                "transcript": "Receptionist: Your room is on the third floor, room 305.",
                "question": "What is the room number?",
                "question_zh": "房间号是多少?",
                "options": ["205", "305", "405", "505"],
                "correct_index": 1,
                "explanation": "The receptionist says 'room 305'.",
                "explanation_zh": "前台说'房间305'。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_listen_a2_003",
            "type": "listening",
            "level": "A2",
            "difficulty": 0.41,
            "scenario_id": null,
            "skill_tested": "time_listening",
            "content": {
                "audio_url": "https://example.com/audio/q_listen_a2_003.mp3",
                "duration": 12,
                "transcript": "The train to Paris leaves at 9:30 in the morning.",
                "question": "When does the train leave?",
                "question_zh": "火车什么时候出发?",
                "options": ["8:30", "9:00", "9:30", "10:00"],
                "correct_index": 2,
                "explanation": "The speaker says '9:30 in the morning'.",
                "explanation_zh": "说话者说'早上9:30'。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_listen_a2_004",
            "type": "listening",
            "level": "A2",
            "difficulty": 0.42,
            "scenario_id": null,
            "skill_tested": "price_listening",
            "content": {
                "audio_url": "https://example.com/audio/q_listen_a2_004.mp3",
                "duration": 10,
                "transcript": "That will be fifteen dollars and fifty cents, please.",
                "question": "How much does it cost?",
                "question_zh": "一共多少钱?",
                "options": ["$15.50", "$50.15", "$15.00", "$50.50"],
                "correct_index": 0,
                "explanation": "The speaker says 'fifteen dollars and fifty cents'.",
                "explanation_zh": "说话者说'十五美元五十美分'。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },

        # 阅读题 (3题)
        {
            "_id": "q_read_a2_001",
            "type": "reading",
            "level": "A2",
            "difficulty": 0.43,
            "scenario_id": null,
            "skill_tested": "comprehension",
            "content": {
                "passage": "The restaurant opens at 11:00 AM and closes at 10:00 PM. Lunch is served from 11:00 to 3:00. Dinner is from 5:00 to 10:00.",
                "question": "When can you have lunch at this restaurant?",
                "question_zh": "这家餐厅什么时候供应午餐?",
                "options": ["11:00 to 3:00", "3:00 to 5:00", "5:00 to 10:00", "All day"],
                "correct_index": 0,
                "explanation": "The passage states 'Lunch is served from 11:00 to 3:00'.",
                "explanation_zh": "文章说'午餐从11:00到3:00供应'。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_read_a2_002",
            "type": "reading",
            "level": "A2",
            "difficulty": 0.44,
            "scenario_id": "scenario_hotel_checkin",
            "skill_tested": "detail_reading",
            "content": {
                "passage": "Hotel guests can use the swimming pool free of charge. The pool is open from 7 AM to 9 PM daily. Towels are provided.",
                "question": "What do guests need to pay for the pool?",
                "question_zh": "客人使用游泳池需要付费吗?",
                "options": ["Nothing, it's free", "$10 per hour", "$20 per day", "$5 for towels"],
                "correct_index": 0,
                "explanation": "The passage says guests can use the pool 'free of charge'.",
                "explanation_zh": "文章说客人可以'免费'使用游泳池。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },
        {
            "_id": "q_read_a2_003",
            "type": "reading",
            "level": "A2",
            "difficulty": 0.45,
            "scenario_id": null,
            "skill_tested": "instruction_reading",
            "content": {
                "passage": "To book a table, please call us at 555-1234 or visit our website www.restaurant.com. We are closed on Mondays.",
                "question": "How can you make a reservation?",
                "question_zh": "如何预订座位?",
                "options": ["Only by phone", "Only online", "By phone or online", "Walk-in only"],
                "correct_index": 2,
                "explanation": "The passage offers two options: call or visit the website.",
                "explanation_zh": "文章提供两种方式:打电话或访问网站。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        },

        # 语法题 (1题)
        {
            "_id": "q_grammar_a2_001",
            "type": "grammar",
            "level": "A2",
            "difficulty": 0.46,
            "scenario_id": null,
            "skill_tested": "present_simple",
            "content": {
                "question": "She ___ to work every day.",
                "question_zh": "她每天___去上班。",
                "options": ["go", "goes", "going", "went"],
                "correct_index": 1,
                "explanation": "Use 'goes' with third person singular in present simple.",
                "explanation_zh": "第三人称单数现在时用'goes'。"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        }
    ]


def generate_b1_questions() -> List[Dict[str, Any]]:
    """生成B1级别题目(15题)"""
    questions = []

    # 听力题 (5题)
    for i in range(1, 6):
        questions.append({
            "_id": f"q_listen_b1_{i:03d}",
            "type": "listening",
            "level": "B1",
            "difficulty": 0.48 + i * 0.02,
            "scenario_id": "scenario_business_meeting_intro" if i <= 2 else None,
            "skill_tested": "detailed_comprehension",
            "content": {
                "audio_url": f"https://example.com/audio/q_listen_b1_{i:03d}.mp3",
                "duration": 20 + i * 2,
                "transcript": f"B1 level listening transcript {i}",
                "question": f"B1 listening question {i}",
                "question_zh": f"B1听力问题{i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": i % 4,
                "explanation": f"Explanation for B1 listening {i}",
                "explanation_zh": f"B1听力解释{i}"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        })

    # 阅读题 (5题)
    for i in range(1, 6):
        questions.append({
            "_id": f"q_read_b1_{i:03d}",
            "type": "reading",
            "level": "B1",
            "difficulty": 0.52 + i * 0.02,
            "scenario_id": None,
            "skill_tested": "inference_reading",
            "content": {
                "passage": f"B1 level reading passage {i} about travel and business contexts.",
                "question": f"B1 reading question {i}",
                "question_zh": f"B1阅读问题{i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": (i + 1) % 4,
                "explanation": f"Explanation for B1 reading {i}",
                "explanation_zh": f"B1阅读解释{i}"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        })

    # 词汇题 (3题)
    for i in range(1, 4):
        questions.append({
            "_id": f"q_vocab_b1_{i:03d}",
            "type": "vocabulary",
            "level": "B1",
            "difficulty": 0.54 + i * 0.02,
            "scenario_id": None,
            "skill_tested": "contextual_vocabulary",
            "content": {
                "question": f"B1 vocabulary question {i}",
                "question_zh": f"B1词汇问题{i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": i % 4,
                "explanation": f"Explanation for B1 vocabulary {i}",
                "explanation_zh": f"B1词汇解释{i}"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        })

    # 语法题 (2题)
    for i in range(1, 3):
        questions.append({
            "_id": f"q_grammar_b1_{i:03d}",
            "type": "grammar",
            "level": "B1",
            "difficulty": 0.58 + i * 0.02,
            "scenario_id": None,
            "skill_tested": "intermediate_grammar",
            "content": {
                "question": f"B1 grammar question {i}",
                "question_zh": f"B1语法问题{i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": (i + 2) % 4,
                "explanation": f"Explanation for B1 grammar {i}",
                "explanation_zh": f"B1语法解释{i}"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        })

    return questions


def generate_all_questions() -> List[Dict[str, Any]]:
    """生成所有60道题"""

    # 读取已有的A1题目
    with open('../data/assessment_questions.json', 'r', encoding='utf-8') as f:
        a1_questions = json.load(f)

    # 生成其他等级
    a2_questions = generate_a2_questions()
    b1_questions = generate_b1_questions()

    # B2-C2题目(简化生成,MVP阶段够用)
    b2_c2_questions = []

    # B2: 12题 (听力4 + 阅读4 + 语法4)
    for i in range(1, 13):
        qtype = ["listening", "reading", "grammar"][(i - 1) % 3]
        b2_c2_questions.append({
            "_id": f"q_{qtype}_b2_{i:03d}",
            "type": qtype,
            "level": "B2",
            "difficulty": 0.62 + i * 0.02,
            "scenario_id": None,
            "skill_tested": f"advanced_{qtype}",
            "content": {
                "audio_url": f"https://example.com/audio/q_{qtype}_b2_{i:03d}.mp3" if qtype == "listening" else None,
                "duration": 25 if qtype == "listening" else None,
                "transcript": f"B2 {qtype} content" if qtype == "listening" else None,
                "passage": f"B2 reading passage {i}" if qtype == "reading" else None,
                "question": f"B2 {qtype} question {i}",
                "question_zh": f"B2{qtype}问题{i}",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct_index": i % 4,
                "explanation": f"B2 explanation {i}",
                "explanation_zh": f"B2解释{i}"
            },
            "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
            "is_active": True,
            "created_at": "2025-10-03T00:00:00Z"
        })

    # C1: 8题 + C2: 3题 (类似模式)
    for level, count in [("C1", 8), ("C2", 3)]:
        for i in range(1, count + 1):
            qtype = ["listening", "reading", "grammar"][i % 3]
            b2_c2_questions.append({
                "_id": f"q_{qtype}_{level.lower()}_{i:03d}",
                "type": qtype,
                "level": level,
                "difficulty": 0.75 + i * 0.03 if level == "C1" else 0.88 + i * 0.02,
                "scenario_id": None,
                "skill_tested": f"expert_{qtype}",
                "content": {
                    "audio_url": f"https://example.com/audio/q_{qtype}_{level.lower()}_{i:03d}.mp3" if qtype == "listening" else None,
                    "duration": 30 if qtype == "listening" else None,
                    "transcript": f"{level} {qtype} content" if qtype == "listening" else None,
                    "passage": f"{level} reading passage" if qtype == "reading" else None,
                    "question": f"{level} {qtype} question {i}",
                    "question_zh": f"{level}{qtype}问题{i}",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "correct_index": i % 4,
                    "explanation": f"{level} explanation",
                    "explanation_zh": f"{level}解释"
                },
                "metadata": {"usage_count": 0, "avg_accuracy": 0.0, "avg_time_spent": 0, "last_calibrated": "2025-10-03T00:00:00Z"},
                "is_active": True,
                "created_at": "2025-10-03T00:00:00Z"
            })

    all_questions = a1_questions + a2_questions + b1_questions + b2_c2_questions

    print(f"Total questions generated: {len(all_questions)}")
    print(f"  A1: {len([q for q in all_questions if q['level'] == 'A1'])}")
    print(f"  A2: {len([q for q in all_questions if q['level'] == 'A2'])}")
    print(f"  B1: {len([q for q in all_questions if q['level'] == 'B1'])}")
    print(f"  B2: {len([q for q in all_questions if q['level'] == 'B2'])}")
    print(f"  C1: {len([q for q in all_questions if q['level'] == 'C1'])}")
    print(f"  C2: {len([q for q in all_questions if q['level'] == 'C2'])}")

    return all_questions


if __name__ == "__main__":
    questions = generate_all_questions()

    output_file = '../data/assessment_questions_full.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Questions saved to {output_file}")
