from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _default_nju_sources() -> list[dict[str, Any]]:
    return [
        {
            "name": "南京大学官网首页",
            "url": "https://www.nju.edu.cn/",
            "source": "南京大学官网",
            "source_type": "nju",
            "include_keywords": ["新闻", "通知", "公告", "活动", "讲座", "比赛", "科研", "招生", "就业", "学工", "教务"],
            "max_items": 20,
            "detail_fetch_limit": 6,
        },
        {
            "name": "南京大学教务处",
            "url": "https://jw.nju.edu.cn/",
            "source": "南京大学教务处",
            "source_type": "nju",
            "include_keywords": ["通知", "教务", "选课", "课程", "讲座", "实践", "活动", "公告"],
            "max_items": 18,
            "detail_fetch_limit": 6,
        },
        {
            "name": "南京大学招生就业",
            "url": "https://www.nju.edu.cn/zsjy/zs.htm",
            "source": "南京大学招生就业",
            "source_type": "nju",
            "include_keywords": ["招生", "就业", "招聘", "宣讲", "选调", "通知", "公告"],
            "max_items": 15,
            "detail_fetch_limit": 5,
        },
        {
            "name": "南京大学创新创业与成果转化办公室",
            "url": "https://ndsc.nju.edu.cn/",
            "source": "南京大学创新创业与成果转化办公室",
            "source_type": "nju",
            "include_keywords": ["创新", "创业", "成果转化", "申报", "基金", "通知", "公告"],
            "max_items": 15,
            "detail_fetch_limit": 5,
        },
        {
            "name": "南京大学新生学院通知公告",
            "url": "https://xsxy.nju.edu.cn/sylm/tzgg/",
            "source": "南京大学新生学院",
            "source_type": "nju",
            "include_keywords": ["通知", "活动", "讲座", "实践", "比赛", "文化节", "学工"],
            "max_items": 15,
            "detail_fetch_limit": 5,
        },
        {
            "name": "共青团南京大学委员会",
            "url": "https://tuanwei.nju.edu.cn/",
            "source": "共青团南京大学委员会",
            "source_type": "nju",
            "include_keywords": ["活动", "竞赛", "挑战杯", "志愿", "社会实践", "通知", "公告"],
            "max_items": 15,
            "detail_fetch_limit": 5,
        },
    ]


def _default_competition_sources() -> list[dict[str, Any]]:
    return [
        {
            "name": "挑战杯官网",
            "url": "https://www.tiaozhanbei.net/",
            "source": "挑战杯官网",
            "source_type": "competition",
            "seed_keywords": ["挑战杯", "大学生", "竞赛"],
            "include_keywords": ["挑战杯", "竞赛", "大学生", "创新", "创业", "科技作品"],
            "category_hint": "创新创业类",
            "always_relevant": True,
            "max_items": 20,
            "detail_fetch_limit": 6,
        },
        {
            "name": "全国大学生数学建模竞赛",
            "url": "https://www.mcm.edu.cn/",
            "source": "全国大学生数学建模竞赛官网",
            "source_type": "competition",
            "seed_keywords": ["数学建模", "竞赛"],
            "include_keywords": ["数学建模", "竞赛", "通知", "报名", "结果", "申报"],
            "category_hint": "程序设计/技术类",
            "always_relevant": True,
            "max_items": 20,
            "detail_fetch_limit": 6,
        },
        {
            "name": "中国国际大学生创新大赛",
            "url": "https://cy.ncss.cn/",
            "source": "中国国际大学生创新大赛",
            "source_type": "competition",
            "seed_keywords": ["创新创业大赛", "互联网+", "大学生创新大赛"],
            "include_keywords": ["大赛", "创新", "创业", "通知", "报名", "征集", "实践"],
            "category_hint": "创新创业类",
            "always_relevant": False,
            "max_items": 18,
            "detail_fetch_limit": 5,
        },
        {
            "name": "中国大学生在线",
            "url": "https://www.univs.cn/",
            "source": "中国大学生在线",
            "source_type": "competition",
            "seed_keywords": ["大学生"],
            "include_keywords": ["大学生", "竞赛", "比赛", "活动", "志愿", "实践", "征文", "创新创业"],
            "category_hint": "文体/综合活动类",
            "always_relevant": False,
            "max_items": 18,
            "detail_fetch_limit": 5,
        },
        {
            "name": "中国研究生创新实践系列大赛",
            "url": "https://cpipc.acge.org.cn/",
            "source": "中国研究生创新实践系列大赛",
            "source_type": "competition",
            "seed_keywords": ["创新实践", "科研竞赛"],
            "include_keywords": ["创新", "实践", "竞赛", "大赛", "征集", "申报"],
            "category_hint": "学术科研类",
            "always_relevant": True,
            "max_items": 18,
            "detail_fetch_limit": 5,
        },
    ]


def _default_competition_keywords() -> list[str]:
    return [
        "大学生 竞赛",
        "大学生 比赛",
        "创新创业大赛",
        "挑战杯",
        "互联网+",
        "数学建模",
        "程序设计竞赛",
        "英语竞赛",
        "电子设计竞赛",
        "创业比赛",
        "科研竞赛",
        "征文",
        "志愿活动",
        "实践活动",
        "论文征集",
        "实习实践",
    ]


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value.strip())


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value.strip())


def _get_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value.strip() if value is not None else default


def _get_json_list(name: str, default: list[dict[str, Any]]) -> list[dict[str, Any]]:
    value = os.getenv(name)
    if not value:
        return default
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} 不是合法 JSON：{exc}") from exc
    if not isinstance(data, list):
        raise ValueError(f"{name} 必须是 JSON 数组")
    return data


def _get_csv_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(slots=True)
class Config:
    base_dir: Path
    data_dir: Path
    logs_dir: Path
    database_path: Path
    log_file: Path
    timezone: str
    user_agent: str
    request_timeout: int
    request_retries: int
    request_delay_seconds: float
    verify_ssl: bool
    max_items_per_source: int
    detail_fetch_limit_per_source: int
    scheduler_time: str
    scheduler_run_on_startup: bool
    unsent_lookback_days: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_ssl: bool
    email_to: list[str]
    mail_retry_count: int
    mail_retry_interval_seconds: int
    nju_sources: list[dict[str, Any]]
    competition_sources: list[dict[str, Any]]
    competition_keywords: list[str]


def load_config() -> Config:
    data_dir = BASE_DIR / "data"
    logs_dir = BASE_DIR / "logs"
    data_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    return Config(
        base_dir=BASE_DIR,
        data_dir=data_dir,
        logs_dir=logs_dir,
        database_path=BASE_DIR / _get_str("DATABASE_PATH", "data/digest.db"),
        log_file=BASE_DIR / _get_str("LOG_FILE", "logs/app.log"),
        timezone=_get_str("TIMEZONE", "Asia/Shanghai"),
        user_agent=_get_str(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 DailyDigestBot/1.0",
        ),
        request_timeout=_get_int("REQUEST_TIMEOUT", 18),
        request_retries=_get_int("REQUEST_RETRIES", 3),
        request_delay_seconds=_get_float("REQUEST_DELAY_SECONDS", 1.2),
        verify_ssl=_get_bool("VERIFY_SSL", True),
        max_items_per_source=_get_int("MAX_ITEMS_PER_SOURCE", 20),
        detail_fetch_limit_per_source=_get_int("DETAIL_FETCH_LIMIT_PER_SOURCE", 6),
        scheduler_time=_get_str("SCHEDULER_TIME", "08:00"),
        scheduler_run_on_startup=_get_bool("SCHEDULER_RUN_ON_STARTUP", False),
        unsent_lookback_days=_get_int("UNSENT_LOOKBACK_DAYS", 30),
        smtp_host=_get_str("SMTP_HOST", ""),
        smtp_port=_get_int("SMTP_PORT", 465),
        smtp_user=_get_str("SMTP_USER", ""),
        smtp_password=_get_str("SMTP_PASSWORD", ""),
        smtp_use_tls=_get_bool("SMTP_USE_TLS", False),
        smtp_use_ssl=_get_bool("SMTP_USE_SSL", True),
        email_to=_get_csv_list("EMAIL_TO", ["1378696641@qq.com"]),
        mail_retry_count=_get_int("MAIL_RETRY_COUNT", 3),
        mail_retry_interval_seconds=_get_int("MAIL_RETRY_INTERVAL_SECONDS", 8),
        nju_sources=_get_json_list("NJU_SOURCES_JSON", _default_nju_sources()),
        competition_sources=_get_json_list("COMPETITION_SOURCES_JSON", _default_competition_sources()),
        competition_keywords=_get_csv_list("COMPETITION_KEYWORDS", _default_competition_keywords()),
    )
