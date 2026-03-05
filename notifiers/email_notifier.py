"""
Gmail SMTP를 이용한 이메일 알림 모듈

설정 필요:
1. Google 계정에서 2단계 인증 활성화
2. Google 앱 비밀번호 생성 (myaccount.google.com → 보안 → 앱 비밀번호)
3. GitHub Secrets에 GMAIL_USER, GMAIL_PASSWORD, GMAIL_TO 등록
"""
from __future__ import annotations

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scrapers.base import Deal


class EmailNotifier:
    def __init__(self, smtp_user: str, smtp_password: str, to_email: str):
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.to_email = to_email

    def send(self, deals: list[Deal]) -> None:
        if not deals:
            return

        subject = f"✈️ 항공 특가 알림: {len(deals)}개 새 딜 발견 ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        html_body = self._build_html(deals)
        text_body = self._build_text(deals)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = self.to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, self.to_email, msg.as_string())

        print(f"[이메일] {len(deals)}개 딜 알림 발송 완료 → {self.to_email}")

    def _build_html(self, deals: list[Deal]) -> str:
        # 출처별로 그룹핑
        groups: dict[str, list[Deal]] = {}
        for deal in deals:
            groups.setdefault(deal.source, []).append(deal)

        cards_html = ""
        for source, source_deals in groups.items():
            cards_html += f"""
            <div style="margin-bottom: 32px;">
                <h2 style="
                    color: #1a1a2e;
                    border-left: 4px solid #0066cc;
                    padding-left: 12px;
                    margin-bottom: 16px;
                    font-size: 18px;
                ">{source}</h2>
                <div>
            """
            for deal in source_deals:
                price_badge = (
                    f'<span style="'
                    f'background:#e8f4fd; color:#0066cc; '
                    f'padding:4px 10px; border-radius:12px; '
                    f'font-weight:bold; font-size:13px;">'
                    f'{deal.price}</span>'
                    if deal.price else ""
                )
                dest_text = f"<p style='color:#555; margin:4px 0;'>📍 {deal.destination}</p>" if deal.destination else ""
                deadline_text = f"<p style='color:#888; font-size:12px; margin:4px 0;'>⏰ 마감: {deal.deadline}</p>" if deal.deadline else ""

                cards_html += f"""
                <div style="
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px;
                    margin-bottom: 12px;
                    background: #fafafa;
                ">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                        <h3 style="margin:0; color:#1a1a2e; font-size:15px; flex:1;">
                            <a href="{deal.url}" style="color:#0066cc; text-decoration:none;">{deal.title}</a>
                        </h3>
                        {price_badge}
                    </div>
                    {dest_text}
                    {deadline_text}
                    <p style="margin:8px 0 0; font-size:12px;">
                        <a href="{deal.url}" style="
                            background:#0066cc; color:white;
                            padding:5px 12px; border-radius:4px;
                            text-decoration:none; font-size:12px;
                        ">바로가기 →</a>
                    </p>
                </div>
                """
            cards_html += "</div></div>"

        return f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8"></head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif; max-width: 640px; margin: 0 auto; padding: 20px; color: #1a1a2e;">
            <div style="background: linear-gradient(135deg, #0066cc, #003380); padding: 24px; border-radius: 12px; margin-bottom: 24px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 22px;">✈️ 항공 특가 알림</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 13px;">
                    {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')} 기준 | 총 {len(deals)}개 신규 딜
                </p>
            </div>

            {cards_html}

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 24px 0;">
            <p style="color: #aaa; font-size: 11px; text-align: center;">
                이 알림은 자동으로 발송되었습니다. GitHub Actions로 운영 중입니다.
            </p>
        </body>
        </html>
        """

    def _build_text(self, deals: list[Deal]) -> str:
        lines = [
            f"항공 특가 알림 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"총 {len(deals)}개 신규 딜",
            "=" * 50,
        ]
        for deal in deals:
            lines.append(f"\n[{deal.source}] {deal.title}")
            if deal.price:
                lines.append(f"  가격: {deal.price}")
            if deal.destination:
                lines.append(f"  목적지: {deal.destination}")
            if deal.deadline:
                lines.append(f"  마감: {deal.deadline}")
            lines.append(f"  링크: {deal.url}")
        return "\n".join(lines)
