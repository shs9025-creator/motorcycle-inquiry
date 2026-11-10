import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 로컬 환경 .env 로드 (Vercel 배포 시에는 Vercel의 Environment Variables가 우선)
load_dotenv()

app = FastAPI(title="Motorcycle Inquiry API")

# CORS 허용 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InquiryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    phone: str = Field(..., min_length=9, max_length=20)
    region: str = Field(...)
    brand: str = Field(...)
    model: str = Field(..., min_length=1, max_length=100)
    condition: str = Field(...)  # 신차, 중고차, 무관
    payment_method: str = Field(...)  # 현금 일시불, 카드 할부, 파이낸셜/캐피탈
    trade_in: str = Field(...)  # 대차 없음, 대차 희망
    trade_in_model: Optional[str] = None
    urgency: str = Field(...)  # 즉시 출고, 1~2주 이내, 1개월 이내, 시세 확인
    delivery_method: str = Field(...)  # 매장 방문, 전국 탁송
    contact_time: str = Field(...)  # 언제든 가능, 오전, 오후, 저녁, 문자/카톡 우선
    message: Optional[str] = None
    bot_honey: Optional[str] = None  # 스팸 봇 방지용 Honeypot 필드


def send_inquiry_email(data: InquiryRequest):
    gmail_user = os.getenv("GMAIL_USER") or os.getenv("GMAIL_ADDRESS")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        raise HTTPException(
            status_code=500,
            detail="이메일 설정(GMAIL_USER 또는 GMAIL_APP_PASSWORD)이 누락되었습니다."
        )

    # 공백 제거 처리 (앱 비밀번호는 16자리 문자열)
    clean_pass = gmail_pass.replace(" ", "").strip()
    clean_user = gmail_user.strip()

    # 한국 시간(KST) 생성
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    # 긴급도 강조 텍스트
    urgency_badge = "🔥 [즉시출고 희망]" if "즉시" in data.urgency else f"[{data.urgency}]"

    subject = f"[바이크 구매문의] {data.name} 고객님 - {data.brand} {data.model} {urgency_badge}"

    # HTML 메일 템플릿
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background-color: #f4f6f8; margin: 0; padding: 24px; color: #1e293b; }}
        .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
        .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); color: #ffffff; padding: 24px; text-align: center; }}
        .header h2 {{ margin: 0; font-size: 22px; font-weight: 700; }}
        .header p {{ margin: 6px 0 0; font-size: 14px; color: #94a3b8; }}
        .content {{ padding: 24px; }}
        .badge {{ display: inline-block; background-color: #ef4444; color: #ffffff; font-size: 13px; font-weight: bold; padding: 4px 10px; border-radius: 20px; margin-bottom: 16px; }}
        .section-title {{ font-size: 15px; font-weight: 700; color: #0284c7; border-bottom: 2px solid #e0f2fe; padding-bottom: 6px; margin: 20px 0 10px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-bottom: 12px; }}
        th {{ width: 28%; text-align: left; padding: 8px 10px; background-color: #f8fafc; color: #64748b; font-weight: 600; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 8px 10px; color: #1e293b; border-bottom: 1px solid #e2e8f0; }}
        .call-btn {{ display: inline-block; background-color: #0284c7; color: #ffffff !important; text-decoration: none; font-weight: bold; padding: 10px 18px; border-radius: 8px; margin-top: 8px; }}
        .memo-box {{ background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 12px 16px; font-size: 14px; line-height: 1.6; border-radius: 4px; }}
        .footer {{ padding: 16px 24px; background-color: #f1f5f9; text-align: center; font-size: 12px; color: #64748b; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="header">
          <h2>🏍️ 신규 바이크 구매 문의</h2>
          <p>접수일시: {now_kst}</p>
        </div>
        <div class="content">
          <span class="badge">{urgency_badge}</span>
          
          <div class="section-title">1. 고객 기본 정보</div>
          <table>
            <tr><th>고객 성함</th><td><strong>{data.name}</strong> 님</td></tr>
            <tr>
              <th>연락처</th>
              <td>
                <a href="tel:{data.phone}" style="color:#0284c7; font-weight:bold; font-size:16px;">{data.phone}</a>
                <br>
                <a href="tel:{data.phone}" class="call-btn">📞 지금 바로 전화 걸기</a>
              </td>
            </tr>
            <tr><th>거주 지역</th><td>{data.region}</td></tr>
            <tr><th>통화 희망 시간</th><td><strong>{data.contact_time}</strong></td></tr>
          </table>

          <div class="section-title">2. 관심 차량 정보</div>
          <table>
            <tr><th>브랜드</th><td>{data.brand}</td></tr>
            <tr><th>희망 모델</th><td><strong style="font-size:16px; color:#0f172a;">{data.model}</strong></td></tr>
            <tr><th>차량 상태</th><td>{data.condition}</td></tr>
            <tr><th>수령 방식</th><td>{data.delivery_method}</td></tr>
          </table>

          <div class="section-title">3. 구매 조건 & 일정</div>
          <table>
            <tr><th>결제 방식</th><td><strong>{data.payment_method}</strong></td></tr>
            <tr><th>출고 희망일</th><td><strong style="color:#dc2626;">{data.urgency}</strong></td></tr>
            <tr><th>기존 바이크 대차</th><td>{data.trade_in} {f'({data.trade_in_model})' if data.trade_in_model else ''}</td></tr>
          </table>

          <div class="section-title">4. 추가 문의 및 요청사항</div>
          <div class="memo-box">
            {data.message.replace(chr(10), '<br>') if data.message and data.message.strip() else '추가 작성 내용 없음'}
          </div>
        </div>
        <div class="footer">
          본 메일은 오토바이 랜딩페이지 구매 문의 폼을 통해 자동 발송되었습니다.
        </div>
      </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"바이크 문의 알림 <{clean_user}>"
    msg["To"] = clean_user
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(clean_user, clean_pass)
            server.sendmail(clean_user, clean_user, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=500,
            detail="Gmail 인증에 실패했습니다. 이메일 주소 및 16자리 앱 비밀번호를 확인해 주세요."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"이메일 발송 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "Inquiry API is running"}


@app.post("/api/inquiry")
def submit_inquiry(req: InquiryRequest):
    # 스팸 봇 필터링: 사용자에게 안 보이는 honeypot 필드에 값이 채워진 경우
    if req.bot_honey:
        return {"status": "success", "message": "접수되었습니다."}

    send_inquiry_email(req)
    return {"status": "success", "message": "구매 문의가 성공적으로 접수되었습니다. 신속히 안내 연락드리겠습니다!"}
