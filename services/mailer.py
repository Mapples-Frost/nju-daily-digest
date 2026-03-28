from __future__ import annotations

import html
import smtplib
import time
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config
from services.classifier import CATEGORY_ORDER


def group_items_by_category(items: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {category: [] for category in CATEGORY_ORDER}
    for item in items:
        grouped.setdefault(item.get("category") or "其他", []).append(item)
    return {category: entries for category, entries in grouped.items() if entries}


def build_email_subject(report_date: str) -> str:
    return f"【每日汇总】南大最新消息与大学生竞赛信息 - {report_date}"


def build_email_html(report_date: str, items: list[dict]) -> str:
    if not items:
        return f"""
        <html>
          <body style="font-family: Arial, 'Microsoft YaHei', sans-serif; color: #222;">
            <h2>每日汇总 - {html.escape(report_date)}</h2>
            <p>今日无新增内容。</p>
          </body>
        </html>
        """.strip()

    grouped = group_items_by_category(items)
    sections: list[str] = []
    for category in CATEGORY_ORDER:
        if category not in grouped:
            continue
        blocks: list[str] = []
        for item in grouped[category]:
            title = html.escape(item.get("title", ""))
            url = html.escape(item.get("url", ""))
            published_at_text = html.escape(item.get("published_at_text", "未知"))
            source = html.escape(item.get("source", "未知来源"))
            summary = html.escape(item.get("summary", "") or "暂无摘要")
            keywords = "、".join(item.get("matched_keywords", []))
            keywords_html = f"<div style='color:#666;font-size:13px;'>关键词：{html.escape(keywords)}</div>" if keywords else ""
            blocks.append(
                f"""
                <div style="margin: 0 0 18px 0; padding: 14px; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff;">
                  <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">
                    <a href="{url}" style="color: #0f4c81; text-decoration: none;">{title}</a>
                  </div>
                  <div style="color:#666;font-size:13px;margin-bottom:4px;">发布时间：{published_at_text}</div>
                  <div style="color:#666;font-size:13px;margin-bottom:4px;">来源：{source}</div>
                  {keywords_html}
                  <div style="margin-top:8px;line-height:1.7;color:#222;">{summary}</div>
                </div>
                """.strip()
            )
        sections.append(
            f"""
            <section style="margin-bottom: 28px;">
              <h3 style="border-left: 4px solid #0f766e; padding-left: 10px; color: #0f172a;">{html.escape(category)}（{len(grouped[category])}）</h3>
              {''.join(blocks)}
            </section>
            """.strip()
        )

    return f"""
    <html>
      <body style="font-family: Arial, 'Microsoft YaHei', sans-serif; color: #222; background: #f8fafc; padding: 24px;">
        <div style="max-width: 900px; margin: 0 auto; background: #f8fafc;">
          <h2 style="color: #111827;">每日汇总 - {html.escape(report_date)}</h2>
          <p style="color: #475569;">共整理 {len(items)} 条未发送内容，按分类展示如下。</p>
          {''.join(sections)}
        </div>
      </body>
    </html>
    """.strip()


def build_plain_text(report_date: str, items: list[dict]) -> str:
    if not items:
        return f"每日汇总 - {report_date}\n\n今日无新增内容。"

    lines = [f"每日汇总 - {report_date}", ""]
    grouped = group_items_by_category(items)
    for category in CATEGORY_ORDER:
        if category not in grouped:
            continue
        lines.append(f"{category}（{len(grouped[category])}）")
        for item in grouped[category]:
            lines.append(f"- {item.get('title')}")
            lines.append(f"  发布时间：{item.get('published_at_text')}")
            lines.append(f"  来源：{item.get('source')}")
            lines.append(f"  链接：{item.get('url')}")
            lines.append(f"  摘要：{item.get('summary')}")
        lines.append("")
    return "\n".join(lines).strip()


class Mailer:
    def __init__(self, config: Config, logger) -> None:
        self.config = config
        self.logger = logger

    def send_digest(self, report_date: str, items: list[dict]) -> bool:
        if not self.config.smtp_host or not self.config.smtp_user or not self.config.smtp_password:
            self.logger.error("SMTP 配置不完整，已跳过邮件发送。")
            return False

        subject = build_email_subject(report_date)
        html_body = build_email_html(report_date, items)
        plain_text = build_plain_text(report_date, items)

        message = MIMEMultipart("alternative")
        message["From"] = self.config.smtp_user
        message["To"] = ", ".join(self.config.email_to)
        message["Subject"] = str(Header(subject, "utf-8"))
        message.attach(MIMEText(plain_text, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        for attempt in range(1, self.config.mail_retry_count + 1):
            try:
                if self.config.smtp_use_ssl:
                    with smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
                        server.login(self.config.smtp_user, self.config.smtp_password)
                        server.sendmail(self.config.smtp_user, self.config.email_to, message.as_string())
                else:
                    with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port, timeout=30) as server:
                        server.ehlo()
                        if self.config.smtp_use_tls:
                            server.starttls()
                            server.ehlo()
                        server.login(self.config.smtp_user, self.config.smtp_password)
                        server.sendmail(self.config.smtp_user, self.config.email_to, message.as_string())
                self.logger.info("邮件发送成功：%s", subject)
                return True
            except Exception as exc:  # pragma: no cover
                self.logger.error(
                    "邮件发送失败（第 %s/%s 次）：%s",
                    attempt,
                    self.config.mail_retry_count,
                    exc,
                )
                if attempt < self.config.mail_retry_count:
                    time.sleep(self.config.mail_retry_interval_seconds)
        return False
