from __future__ import annotations

from config import load_config
from services.collector import DailyCollector
from services.mailer import Mailer
from utils.logger import setup_logger


def run_once() -> dict:
    config = load_config()
    logger = setup_logger(config.log_file)
    collector = DailyCollector(config, logger)
    mailer = Mailer(config, logger)

    try:
        result = collector.collect()
        pending_items = result["pending_items"]
        logger.info(
            "本次任务完成：原始 %s 条，去重后 %s 条，新增 %s 条，待发送 %s 条",
            result["raw_count"],
            result["dedup_count"],
            result["new_count"],
            len(pending_items),
        )

        sent = mailer.send_digest(result["report_date"], pending_items)
        if sent:
            collector.mark_sent(pending_items)
            logger.info("已标记 %s 条记录为已发送。", len(pending_items))
        else:
            logger.warning("本次邮件未成功发送，记录将保留为未发送状态。")

        return result | {"sent": sent}
    finally:
        collector.close()


if __name__ == "__main__":
    run_once()
