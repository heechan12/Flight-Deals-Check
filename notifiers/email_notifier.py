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

    def send(self, new_deals: list[Deal], seen_deals: list[Deal] | None = None) -> None:
        if not new_deals:
            return

        seen_deals = seen_deals or []
        subject = (
            f"✈️ 항공 특가 알림: 신규 {len(new_deals)}개"
            + (f" | 재확인 {len(seen_deals)}개" if seen_deals else "")
            + f" ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        )
        html_body = self._build_html(new_deals, seen_deals)
        text_body = self._build_text(new_deals, seen_deals)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.smtp_user
        msg["To"] = self.to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, self.to_email, msg.as_string())

        print(f"[이메일] 신규 {len(new_deals)}개 / 재확인 {len(seen_deals)}개 발송 완료 → {self.to_email}")

    # ------------------------------------------------------------------ #

    def _build_html(self, new_deals: list[Deal], seen_deals: list[Deal]) -> str:
        now_str = datetime.now().strftime('%Y년 %m월 %d일 %H:%M')
        new_section = self._section_html(new_deals, is_new=True)
        seen_section = self._section_html(seen_deals, is_new=False) if seen_deals else ""

        return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', sans-serif; max-width: 640px; margin: 0 auto; padding: 20px; color: #1a1a2e;">

  <!-- 헤더 -->
  <div style="background: linear-gradient(135deg, #0066cc, #003380); padding: 24px; border-radius: 12px; margin-bottom: 28px; text-align: center;">
    <h1 style="color: white; margin: 0; font-size: 22px;">✈️ 항공 특가 알림</h1>
    <p style="color: rgba(255,255,255,0.8); margin: 8px 0 0; font-size: 13px;">
      {now_str} 기준 &nbsp;|&nbsp; 🆕 신규 {len(new_deals)}개
      {f"&nbsp;|&nbsp; ✅ 재확인 {len(seen_deals)}개" if seen_deals else ""}
    </p>
  </div>

  <!-- 신규 딜 -->
  <div style="margin-bottom: 8px;">
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">
      <span style="background:#0066cc; color:white; font-size:12px; font-weight:bold; padding:3px 10px; border-radius:20px;">🆕 신규</span>
      <span style="color:#555; font-size:13px;">{len(new_deals)}개의 새로운 딜이 발견됐습니다</span>
    </div>
    {new_section}
  </div>

  {"<!-- 재확인 딜 -->" if seen_deals else ""}
  {f'''
  <hr style="border:none; border-top:2px dashed #e0e0e0; margin: 28px 0;">
  <div>
    <div style="display:flex; align-items:center; gap:8px; margin-bottom:16px;">
      <span style="background:#6c757d; color:white; font-size:12px; font-weight:bold; padding:3px 10px; border-radius:20px;">✅ 이미 확인한 딜</span>
      <span style="color:#888; font-size:13px;">{len(seen_deals)}개 — 이전 알림에서 이미 발송된 딜입니다</span>
    </div>
    {self._section_html(seen_deals, is_new=False)}
  </div>
  ''' if seen_deals else ""}

  <hr style="border:none; border-top:1px solid #e0e0e0; margin: 28px 0 16px;">
  <p style="color:#bbb; font-size:11px; text-align:center; margin:0;">
    이 알림은 자동으로 발송되었습니다. GitHub Actions로 운영 중입니다.
  </p>
</body>
</html>"""

    def _section_html(self, deals: list[Deal], is_new: bool) -> str:
        # 출처별 그룹핑
        groups: dict[str, list[Deal]] = {}
        for deal in deals:
            groups.setdefault(deal.source, []).append(deal)

        accent   = "#0066cc" if is_new else "#6c757d"
        card_bg  = "#fafafa" if is_new else "#f5f5f5"
        title_color = "#1a1a2e" if is_new else "#666"

        html = ""
        for source, source_deals in groups.items():
            html += f"""
            <div style="margin-bottom:24px;">
              <h2 style="color:{title_color}; border-left:4px solid {accent}; padding-left:12px; margin:0 0 12px; font-size:16px;">{source}</h2>
            """
            for deal in source_deals:
                price_badge = (
                    f'<span style="background:#e8f4fd; color:{accent}; padding:3px 9px; border-radius:12px; font-weight:bold; font-size:12px;">{deal.price}</span>'
                    if deal.price else ""
                )
                dest_text    = f"<p style='color:#666; margin:4px 0; font-size:13px;'>📍 {deal.destination}</p>" if deal.destination else ""
                deadline_text = f"<p style='color:#999; font-size:12px; margin:4px 0;'>⏰ {deal.deadline}</p>" if deal.deadline else ""
                extra_text   = f"<p style='color:#aaa; font-size:11px; margin:4px 0;'>{deal.extra}</p>" if deal.extra else ""

                opacity = "opacity:0.75;" if not is_new else ""
                html += f"""
                <div style="border:1px solid #e0e0e0; border-radius:8px; padding:14px; margin-bottom:10px; background:{card_bg}; {opacity}">
                  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
                    <h3 style="margin:0; color:{title_color}; font-size:14px; flex:1;">
                      <a href="{deal.url}" style="color:{accent}; text-decoration:none;">{deal.title}</a>
                    </h3>
                    {price_badge}
                  </div>
                  {dest_text}{deadline_text}{extra_text}
                  <p style="margin:8px 0 0;">
                    <a href="{deal.url}" style="background:{accent}; color:white; padding:4px 11px; border-radius:4px; text-decoration:none; font-size:12px;">바로가기 →</a>
                  </p>
                </div>
                """
            html += "</div>"
        return html

    def _build_text(self, new_deals: list[Deal], seen_deals: list[Deal]) -> str:
        lines = [
            f"항공 특가 알림 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"신규 {len(new_deals)}개 | 이미 확인한 딜 {len(seen_deals)}개",
            "=" * 50,
            "\n[🆕 신규 딜]",
        ]
        for deal in new_deals:
            lines.append(f"\n[{deal.source}] {deal.title}")
            if deal.price:
                lines.append(f"  가격: {deal.price}")
            if deal.deadline:
                lines.append(f"  날짜: {deal.deadline}")
            lines.append(f"  링크: {deal.url}")

        if seen_deals:
            lines += ["\n" + "=" * 50, "\n[✅ 이미 확인한 딜]"]
            for deal in seen_deals:
                lines.append(f"\n[{deal.source}] {deal.title}")
                if deal.price:
                    lines.append(f"  가격: {deal.price}")
                lines.append(f"  링크: {deal.url}")

        return "\n".join(lines)
