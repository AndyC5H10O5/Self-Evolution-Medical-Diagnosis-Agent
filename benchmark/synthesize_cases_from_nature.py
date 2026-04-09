from __future__ import annotations

import argparse
import json
import random
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent


TARGET_SKILLS = [
    "acne",
    "cough",
    "fatigue",
    "fever",
    "headache",
    "insomnia",
    "tinnitus",
    "vomiting",
]

# 每个症状：可进化字段 25 条，分配 9/8/8；每字段正例 6 条（其余负例）
EVOLVABLE_FIELD_COUNTS = [9, 8, 8]
POSITIVE_PER_FIELD = 6
# 控制 train/test 的正向 slot 重合度，避免 coverage 过高
POSITIVE_SLOT_VARIETY = 4
CASES_PER_SKILL = 50
EVOLVABLE_CASES_PER_SKILL = 25


SKILL_SCHEMA: dict[str, dict[str, Any]] = {
    "acne": {
        "evolvable": {
            "皮损类型": {
                "base_options": ["粉刺", "丘疹", "脓疱"],
                "positive_options": ["囊肿样", "结节样", "闭口样", "开口样", "炎性丘疹", "粉瘤样"],
            },
            "诱发因素": {
                "base_options": ["熬夜", "压力大", "饮食油辣"],
                "positive_options": ["口罩闷热", "高糖饮食", "护肤不当", "经期波动", "频繁化妆", "睡眠紊乱"],
            },
            "伴随问题": {
                "base_options": ["疼痛", "瘙痒", "色沉"],
                "positive_options": ["反复破溃", "局部发热", "触痛明显", "油脂增多", "瘢痕倾向", "红肿渗出"],
            },
        },
        "nonevolvable": {
            "发生部位": ["额头", "面颊", "下巴"],
            "病程": ["近期爆发", "反复多年", "周期性加重"],
            "处理方式": ["未处理", "自行外用药", "口服药"],
        },
        "keywords": [
            "acne",
            "pimple",
            "zit",
            "blackhead",
            "whitehead",
            "skin lesion",
            "spot",
            "skin",
            "rash",
            "boil",
            "carbuncle",
            "follicul",
        ],
    },
    "cough": {
        "evolvable": {
            "咳嗽类型": {
                "base_options": ["干咳", "刺激性咳"],
                "positive_options": ["阵发性咳", "犬吠样咳", "晨起咳", "夜间咳", "痉挛性咳", "胸闷性咳"],
            },
            "痰液情况": {
                "base_options": ["无痰", "白痰", "黄痰"],
                "positive_options": ["泡沫痰", "黏丝痰", "脓性痰", "铁锈色痰", "血痰丝", "清稀痰"],
            },
            "伴随症状": {
                "base_options": ["发热", "咽痛", "气短"],
                "positive_options": ["胸痛", "喘鸣", "鼻塞", "流涕", "声音嘶哑", "夜汗"],
            },
        },
        "nonevolvable": {
            "持续时间": ["1周内", "1-3周", "3周以上"],
            "诱发因素": ["受凉后", "运动后", "闻刺激气味后"],
            "缓解情况": ["喝水后缓解", "止咳药缓解", "雾化后缓解"],
        },
        "keywords": ["cough", "phlegm", "sputum", "throat", "bronch", "wheez", "whooping", "laryng"],
    },
    "fatigue": {
        "evolvable": {
            "伴随症状": {
                "base_options": ["心悸", "气短", "发热"],
                "positive_options": ["头晕", "肌无力", "食欲差", "盗汗", "体重减轻", "注意力差"],
            },
            "生活因素": {
                "base_options": ["压力大", "久坐少动", "饮食不规律"],
                "positive_options": ["长期加班", "昼夜颠倒", "运动不足", "过度节食", "频繁出差", "照护负担"],
            },
            "睡眠状态": {
                "base_options": ["睡眠充足", "入睡困难", "易醒"],
                "positive_options": ["浅睡多梦", "早醒难眠", "睡后疲惫", "夜间惊醒", "睡眠断续", "鼾声明显"],
            },
        },
        "nonevolvable": {
            "疲劳程度": ["轻度", "中度", "重度"],
            "持续时间": ["几天", "1-4周", "1月以上"],
            "缓解情况": ["休息后缓解", "周末缓解", "补充营养后缓解"],
        },
        "keywords": ["fatigue", "tired", "exhaust", "weak", "weakness", "energy", "letharg", "sleepy"],
    },
    "fever": {
        "evolvable": {
            "体温范围": {
                "base_options": ["37.3-38℃", "38-39℃", "39℃以上"],
                "positive_options": ["低热波动", "超高热", "午后热峰", "夜间高热", "反复低热", "寒战高热"],
            },
            "伴随症状": {
                "base_options": ["咳嗽", "咽痛", "腹泻"],
                "positive_options": ["皮疹", "寒战", "肌痛", "头痛", "呕吐", "关节痛"],
            },
            "暴露风险": {
                "base_options": ["接触病人", "旅行后", "基础病"],
                "positive_options": ["聚集暴露", "海鲜生食", "虫咬史", "境外停留", "动物接触", "院感暴露"],
            },
        },
        "nonevolvable": {
            "持续时间": ["当天开始", "2-3天", "一周以上"],
            "发热规律": ["持续高热", "午后低热", "夜间明显"],
            "退热情况": ["退热药有效", "短暂退热", "物理降温有效"],
        },
        "keywords": ["fever", "temperature", "chills", "flu", "infection", "pyrexia", "febrile", "high temp"],
    },
    "headache": {
        "evolvable": {
            "头痛部位": {
                "base_options": ["单侧", "双侧", "后枕部"],
                "positive_options": ["前额部", "颞部", "眼眶后", "顶部", "全头部", "枕颈部"],
            },
            "头痛性质": {
                "base_options": ["搏动样", "压迫样", "头部沉重"],
                "positive_options": ["电击样", "针刺样", "撕裂样", "胀裂样", "紧箍样", "灼痛样"],
            },
            "伴随症状": {
                "base_options": ["恶心", "呕吐", "畏光"],
                "positive_options": ["畏声", "眩晕", "视物模糊", "流泪", "鼻塞", "颈僵"],
            },
        },
        "nonevolvable": {
            "起病时间与频率": ["首次", "反复发作", "首次"],
            "诱因": ["熬夜", "压力", "饮酒"],
            "缓解因素": ["休息", "止痛药", "休息"],
        },
        "keywords": ["headache", "migraine", "head pain", "head hurts", "temple pain", "skull", "head ache"],
    },
    "insomnia": {
        "evolvable": {
            "睡眠问题类型": {
                "base_options": ["入睡困难", "易醒", "早醒"],
                "positive_options": ["浅睡多梦", "入睡即醒", "夜惊醒", "睡后不解乏", "凌晨易醒", "睡眠断续"],
            },
            "白天影响": {
                "base_options": ["轻度疲劳", "注意力下降", "情绪烦躁"],
                "positive_options": ["记忆下降", "工作失误", "反应迟缓", "焦虑加重", "嗜睡乏力", "社交退缩"],
            },
            "可能诱因": {
                "base_options": ["压力大", "熬夜", "咖啡因"],
                "positive_options": ["倒班", "电子屏暴露", "情感事件", "慢性疼痛", "噪音干扰", "长期午睡"],
            },
        },
        "nonevolvable": {
            "持续时长": ["几天", "1-4周", "1-3月"],
            "每周频次": ["偶发", "每周1-2次", "每周3次以上"],
            "自我处理": ["未处理", "调整作息", "助眠药物"],
        },
        "keywords": ["insomnia", "sleep", "awake", "cannot sleep", "wakeup", "sleeping", "sleepless", "sleep apnea"],
    },
    "tinnitus": {
        "evolvable": {
            "耳鸣性质": {
                "base_options": ["嗡嗡声", "蝉鸣声", "电流声"],
                "positive_options": ["尖锐鸣响", "低频轰鸣", "脉冲样", "金属声", "间歇爆鸣", "风噪样"],
            },
            "伴随症状": {
                "base_options": ["听力下降", "眩晕", "耳闷"],
                "positive_options": ["耳痛", "头痛", "恶心", "平衡差", "焦虑", "失眠"],
            },
            "诱发场景": {
                "base_options": ["噪声后", "熬夜后", "情绪紧张后"],
                "positive_options": ["洗澡后", "安静环境", "运动后", "乘车后", "咖啡后", "感冒后"],
            },
        },
        "nonevolvable": {
            "耳鸣侧别": ["左侧", "右侧", "双侧"],
            "持续时间": ["突发", "几天内", "数周"],
            "对生活影响": ["轻微", "影响睡眠", "影响工作"],
        },
        "keywords": ["tinnitus", "ringing", "ear noise", "ear ringing", "buzzing ear", "ear sound", "ear", "hearing", "vertigo"],
    },
    "vomiting": {
        "evolvable": {
            "呕吐性质": {
                "base_options": ["食物残渣", "黄绿色液体", "咖啡色"],
                "positive_options": ["泡沫样", "黑渣样", "酸水样", "胆汁样", "血丝样", "黏液样"],
            },
            "伴随症状": {
                "base_options": ["腹痛", "腹泻", "发热"],
                "positive_options": ["头晕", "乏力", "脱水", "心悸", "食欲差", "寒战"],
            },
            "与进食关系": {
                "base_options": ["饭后明显", "空腹明显", "夜间明显"],
                "positive_options": ["闻味即吐", "油腻后吐", "进食即吐", "晨起恶心", "晚餐后吐", "饮水后吐"],
            },
        },
        "nonevolvable": {
            "呕吐频次": ["偶发", "每天1-2次", "每天3次以上"],
            "脱水表现": ["口干", "尿少", "乏力"],
            "缓解情况": ["休息后缓解", "止吐药缓解", "补液后缓解"],
        },
        "keywords": ["vomit", "vomiting", "nausea", "throw up", "emesis", "retch", "sick", "regurgitate"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Synthesize benchmark cases from Nature xlsx.")
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "data source" / "HealthSearchQA - Nature.xlsx",
        help="Path to xlsx source.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20260406,
        help="Random seed.",
    )
    parser.add_argument(
        "--train-out",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "train_synth_v1.jsonl",
    )
    parser.add_argument(
        "--test-out",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "test_synth_v1.jsonl",
    )
    parser.add_argument(
        "--stats-out",
        type=Path,
        default=PROJECT_ROOT / "benchmark" / "cases" / "synth_stats_v1.json",
    )
    return parser.parse_args()


def _read_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    path = "xl/sharedStrings.xml"
    if path not in zf.namelist():
        return []
    root = ET.fromstring(zf.read(path))
    strings: list[str] = []
    for si in root.iter(ns + "si"):
        value = "".join(t.text or "" for t in si.iter(ns + "t"))
        strings.append(value)
    return strings


def _sheet_values(zf: zipfile.ZipFile, sheet_path: str, shared_strings: list[str]) -> list[list[str]]:
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    root = ET.fromstring(zf.read(sheet_path))
    rows: list[list[str]] = []
    for row in root.iter(ns + "row"):
        values: list[str] = []
        for cell in row.iter(ns + "c"):
            ctype = cell.attrib.get("t")
            v = cell.find(ns + "v")
            if v is None:
                values.append("")
                continue
            raw = v.text or ""
            if ctype == "s" and raw.isdigit():
                idx = int(raw)
                values.append(shared_strings[idx] if 0 <= idx < len(shared_strings) else "")
            else:
                values.append(raw)
        if values:
            rows.append(values)
    return rows


def read_questions_from_xlsx(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"xlsx not found: {path}")
    with zipfile.ZipFile(path) as zf:
        shared = _read_shared_strings(zf)
        sheet_paths = ["xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml"]
        questions: list[str] = []
        for sp in sheet_paths:
            if sp not in zf.namelist():
                continue
            rows = _sheet_values(zf, sp, shared)
            for row in rows:
                text = (row[0] if row else "").strip()
                if text:
                    questions.append(text)
    # 去重保序
    seen: set[str] = set()
    deduped: list[str] = []
    for q in questions:
        if q not in seen:
            deduped.append(q)
            seen.add(q)
    return deduped


def pick_questions_for_skills(questions: list[str], rnd: random.Random) -> tuple[dict[str, list[str]], dict[str, int]]:
    buckets: dict[str, list[str]] = {k: [] for k in TARGET_SKILLS}
    direct_hits: dict[str, int] = {k: 0 for k in TARGET_SKILLS}
    fallback: list[str] = []
    for q in questions:
        ql = q.lower()
        best_skill = ""
        best_score = 0
        for skill in TARGET_SKILLS:
            score = sum(1 for token in SKILL_SCHEMA[skill]["keywords"] if token in ql)
            if score > best_score:
                best_score = score
                best_skill = skill
        if best_skill and best_score > 0:
            buckets[best_skill].append(q)
            direct_hits[best_skill] += 1
        else:
            fallback.append(q)

    for skill in TARGET_SKILLS:
        if len(buckets[skill]) < CASES_PER_SKILL:
            need = CASES_PER_SKILL - len(buckets[skill])
            pool = fallback[:] if fallback else questions[:]
            rnd.shuffle(pool)
            buckets[skill].extend(pool[:need])
    return buckets, direct_hits


def _sanitize_option(text: str) -> str:
    out = re.sub(r"[()（）/\\|,，;；:：\n\r\t]", "", text)
    out = re.sub(r"\s+", "", out).strip()
    if len(out) < 2:
        out = (out + "表现")[:4]
    if len(out) > 12:
        out = out[:12]
    return out


def _question_inspiration(question: str) -> str:
    q = question.strip()
    if not q:
        return "这两天"
    ql = q.lower()
    if any(k in ql for k in ["night", "sleep", "insomnia", "midnight"]):
        return "晚上更明显"
    if any(k in ql for k in ["eat", "food", "meal", "diet", "vomit", "stomach"]):
        return "饭后更明显"
    if any(k in ql for k in ["work", "stress", "anxiety", "tired", "fatigue"]):
        return "最近压力大时"
    if any(k in ql for k in ["cold", "fever", "cough", "throat"]):
        return "最近受凉后"
    return "最近"


def _build_user_turn(field_label: str, option: str, source_question: str, *, positive: bool) -> str:
    option_clean = _sanitize_option(option)
    lead = _question_inspiration(source_question)
    if positive:
        return f"{lead}，我这个{field_label}更像{option_clean}"
    return f"{lead}，我就是{option_clean}"


def _build_case(
    *,
    case_id: str,
    skill_key: str,
    field_label: str,
    user_turn: str,
    candidate_option: str,
    gold_need_evolve: bool,
    gold_slot: str,
    source_question: str,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "skill_key": skill_key,
        "field_label": field_label,
        "user_turn": user_turn,
        "candidate_option": _sanitize_option(candidate_option),
        "last_assistant_question_field": field_label,
        "gold_need_evolve": bool(gold_need_evolve),
        "gold_slot": _sanitize_option(gold_slot),
        "source_question": source_question,
    }


def synthesize_cases(questions_by_skill: dict[str, list[str]], rnd: random.Random) -> list[dict[str, Any]]:
    all_cases: list[dict[str, Any]] = []

    for skill in TARGET_SKILLS:
        skill_conf = SKILL_SCHEMA[skill]
        evolvable_items = list(skill_conf["evolvable"].items())
        nonevo_items = list(skill_conf["nonevolvable"].items())
        question_pool = questions_by_skill[skill][:]
        rnd.shuffle(question_pool)

        case_index = 1
        q_index = 0

        # 1) evolvable related: 25
        for (field_label, field_conf), total_count in zip(evolvable_items, EVOLVABLE_FIELD_COUNTS):
            positives = POSITIVE_PER_FIELD
            negatives = total_count - positives
            base_options = field_conf["base_options"]
            positive_pool = field_conf["positive_options"][:max(POSITIVE_SLOT_VARIETY, 1)]
            if not positive_pool:
                raise ValueError(f"No positive options for {skill}:{field_label}")

            for i in range(positives):
                question = question_pool[q_index % len(question_pool)]
                q_index += 1
                option = positive_pool[i % len(positive_pool)]
                user_turn = _build_user_turn(field_label, option, question, positive=True)
                case = _build_case(
                    case_id=f"{skill}_c{case_index:03d}",
                    skill_key=skill,
                    field_label=field_label,
                    user_turn=user_turn,
                    candidate_option=option,
                    gold_need_evolve=True,
                    gold_slot=option,
                    source_question=question,
                )
                all_cases.append(case)
                case_index += 1

            for i in range(negatives):
                question = question_pool[q_index % len(question_pool)]
                q_index += 1
                base = base_options[i % len(base_options)]
                user_turn = _build_user_turn(field_label, base, question, positive=False)
                case = _build_case(
                    case_id=f"{skill}_c{case_index:03d}",
                    skill_key=skill,
                    field_label=field_label,
                    user_turn=user_turn,
                    candidate_option=base,
                    gold_need_evolve=False,
                    gold_slot=base,
                    source_question=question,
                )
                all_cases.append(case)
                case_index += 1

        # 2) non-evolvable: 25
        nonevo_total = CASES_PER_SKILL - EVOLVABLE_CASES_PER_SKILL
        for i in range(nonevo_total):
            field_label, options = nonevo_items[i % len(nonevo_items)]
            question = question_pool[q_index % len(question_pool)]
            q_index += 1
            option = options[i % len(options)]
            user_turn = _build_user_turn(field_label, option, question, positive=False)
            case = _build_case(
                case_id=f"{skill}_c{case_index:03d}",
                skill_key=skill,
                field_label=field_label,
                user_turn=user_turn,
                candidate_option=option,
                gold_need_evolve=False,
                gold_slot=option,
                source_question=question,
            )
            all_cases.append(case)
            case_index += 1

        if case_index - 1 != CASES_PER_SKILL:
            raise ValueError(f"Skill {skill} generated {case_index - 1} cases, expected {CASES_PER_SKILL}")

    return all_cases


def stratified_split(cases: list[dict[str, Any]], rnd: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_skill_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        by_skill_group[case["skill_key"]].append(case)

    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []

    for skill in TARGET_SKILLS:
        rows = by_skill_group[skill]
        if len(rows) != CASES_PER_SKILL:
            raise ValueError(f"Skill {skill} has {len(rows)} cases, expected {CASES_PER_SKILL}")

        # 在 skill 内按 (field_label, gold_need_evolve) 分层，
        # 降低 train/test 对同一 slot 的强绑定，避免总覆盖率过高。
        bucket: dict[tuple[str, bool], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            bucket[(row["field_label"], bool(row["gold_need_evolve"]))].append(row)

        train_skill: list[dict[str, Any]] = []
        test_skill: list[dict[str, Any]] = []
        for _, group_rows in bucket.items():
            rnd.shuffle(group_rows)
            cut = int(round(len(group_rows) * 0.7))
            if len(group_rows) >= 2:
                cut = max(1, min(len(group_rows) - 1, cut))
            train_skill.extend(group_rows[:cut])
            test_skill.extend(group_rows[cut:])

        # 修正到每症状 35/15
        rnd.shuffle(train_skill)
        rnd.shuffle(test_skill)
        while len(train_skill) > 35:
            test_skill.append(train_skill.pop())
        while len(train_skill) < 35:
            train_skill.append(test_skill.pop())

        train.extend(train_skill)
        test.extend(test_skill)

    rnd.shuffle(train)
    rnd.shuffle(test)
    return train, test


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def build_stats(
    all_cases: list[dict[str, Any]],
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    direct_hits: dict[str, int],
) -> dict[str, Any]:
    stats: dict[str, Any] = {
        "total_cases": len(all_cases),
        "train_cases": len(train),
        "test_cases": len(test),
        "by_skill": {},
        "validation": {},
    }

    by_skill: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_cases:
        by_skill[row["skill_key"]].append(row)

    for skill in TARGET_SKILLS:
        rows = by_skill[skill]
        evolvable_fields = set(SKILL_SCHEMA[skill]["evolvable"].keys())
        evo_rows = [r for r in rows if r["field_label"] in evolvable_fields]
        field_stats: dict[str, Any] = {}
        for field in evolvable_fields:
            fr = [r for r in rows if r["field_label"] == field]
            field_stats[field] = {
                "count": len(fr),
                "positive": sum(1 for r in fr if r["gold_need_evolve"]),
                "negative": sum(1 for r in fr if not r["gold_need_evolve"]),
            }
        stats["by_skill"][skill] = {
            "total": len(rows),
            "source_direct_hits": int(direct_hits.get(skill, 0)),
            "source_fallback_used": max(0, 50 - int(direct_hits.get(skill, 0))),
            "evolvable_related": len(evo_rows),
            "non_evolvable_related": len(rows) - len(evo_rows),
            "positive_total": sum(1 for r in rows if r["gold_need_evolve"]),
            "field_stats": field_stats,
            "train_count": sum(1 for r in train if r["skill_key"] == skill),
            "test_count": sum(1 for r in test if r["skill_key"] == skill),
        }

    validations = {
        "total_400": len(all_cases) == 400,
        "each_skill_50": all(stats["by_skill"][s]["total"] == 50 for s in TARGET_SKILLS),
        "each_skill_evolvable_25": all(stats["by_skill"][s]["evolvable_related"] == 25 for s in TARGET_SKILLS),
        "each_skill_train_35_test_15": all(
            stats["by_skill"][s]["train_count"] == 35 and stats["by_skill"][s]["test_count"] == 15
            for s in TARGET_SKILLS
        ),
        "each_evo_field_8_or_9": all(
            fs["count"] in {8, 9}
            for s in TARGET_SKILLS
            for fs in stats["by_skill"][s]["field_stats"].values()
        ),
        "each_evo_field_positive_6": all(
            fs["positive"] == 6
            for s in TARGET_SKILLS
            for fs in stats["by_skill"][s]["field_stats"].values()
        ),
    }
    stats["validation"] = validations
    stats["validation_passed"] = all(validations.values())
    return stats


def main() -> None:
    args = parse_args()
    rnd = random.Random(args.seed)

    questions = read_questions_from_xlsx(args.xlsx)
    if len(questions) < 400:
        raise ValueError(f"Source questions too few: {len(questions)}")

    questions_by_skill, direct_hits = pick_questions_for_skills(questions, rnd)
    all_cases = synthesize_cases(questions_by_skill, rnd)
    train, test = stratified_split(all_cases, rnd)
    stats = build_stats(all_cases, train, test, direct_hits)

    _write_jsonl(args.train_out, train)
    _write_jsonl(args.test_out, test)
    args.stats_out.parent.mkdir(parents=True, exist_ok=True)
    args.stats_out.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[synth] source_questions={len(questions)}")
    print(f"[synth] train={len(train)} test={len(test)} total={len(all_cases)}")
    print(f"[synth] train_out={args.train_out}")
    print(f"[synth] test_out={args.test_out}")
    print(f"[synth] stats_out={args.stats_out}")
    print(f"[synth] validation_passed={stats['validation_passed']}")


if __name__ == "__main__":
    main()
