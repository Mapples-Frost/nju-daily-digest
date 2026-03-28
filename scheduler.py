from __future__ import annotations

import time

import schedule

from app import run_once
from config import load_config
from utils.logger import setup_logger


def main() -> None:
    config = load_config()
    logger = setup_logger(config.log_file)

    def job() -> None:
        logger.info("开始执行定时任务。")
        try:
            run_once()
        except Exception as exc:  # pragma: no cover - 运行时兜底
            logger.exception("定时任务执行失败：%s", exc)

    schedule.every().day.at(config.scheduler_time).do(job)
    logger.info("定时任务已启动，每天 %s 执行一次。", config.scheduler_time)

    if config.scheduler_run_on_startup:
        job()

    while True:
        schedule.run_pending()
        time.sleep(20)


if __name__ == "__main__":
    main()
