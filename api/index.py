import json
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import urllib.request
import urllib.parse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

load_dotenv()

app = FastAPI(title="Motorcycle Inquiry API with Supabase")

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
    condition: str = Field(...)
    payment_method: str = Field(...)
    trade_in: str = Field(...)
    trade_in_model: Optional[str] = None
    urgency: str = Field(...)
    delivery_method: str = Field(...)
    contact_time: str = Field(...)
    message: Optional[str] = None
    bot_honey: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    status: str
    memo: Optional[str] = None


class AdminLoginRequest(BaseModel):
    password: str


# --- Supabase REST 헬퍼 함수 ---
def get_supabase_config():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    return url, key


def save_to_supabase(data: InquiryRequest):
    url, key = get_supabase_config()
    if not url or not key:
        print("[WARN] Supabase 설정이 없어 DB 저장을 건너뜁니다.")
        return None

    endpoint = f"{url.rstrip('/')}/rest/v1/inquiries"
    payload = {
        "name": data.name,
        "phone": data.phone,
        "region": data.region,
        "brand": data.brand,
        "model": data.model,
        "condition": data.condition,
        "payment_method": data.payment_method,
        "trade_in": data.trade_in,
        "trade_in_model": data.trade_in_model or "",
        "urgency": data.urgency,
        "delivery_method": data.delivery_method,
        "contact_time": data.contact_time,
        "message": data.message or "",
        "status": "신규접수"
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR] Supabase DB 저장 실패: {e}")
        return None


def fetch_inquiries_from_supabase():
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase 설정이 구성되지 않았습니다.")

    endpoint = f"{url.rstrip('/')}/rest/v1/inquiries?select=*&order=created_at.desc"
    req = urllib.request.Request(
        endpoint,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB 조회 실패: {str(e)}")


def update_inquiry_in_supabase(inquiry_id: int, status: str, memo: Optional[str] = None):
    url, key = get_supabase_config()
    if not url or not key:
        raise HTTPException(status_code=500, detail="Supabase 설정이 구성되지 않았습니다.")

    endpoint = f"{url.rstrip('/')}/rest/v1/inquiries?id=eq.{inquiry_id}"
    payload = {"status": status}
    if memo is not None:
        payload["memo"] = memo

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return True
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"상태 업데이트 실패: {str(e)}")


# --- Gmail 발송 함수 ---
def send_inquiry_email(data: InquiryRequest):
    gmail_user = os.getenv("GMAIL_USER") or os.getenv("GMAIL_ADDRESS")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        return  # 이메일 설정 누락 시 조용히 스킵

    clean_pass = gmail_pass.replace(" ", "").strip()
    clean_user = gmail_user.strip()

    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    urgency_badge = "🔥 [즉시출고 희망]" if "즉시" in data.urgency else f"[{data.urgency}]"
    subject = f"[바이크 구매문의] {data.name} 고객님 - {data.brand} {data.model} {urgency_badge}"

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
    except Exception as e:
        print(f"[WARN] 이메일 발송 실패 (DB 저장은 유지): {e}")


# --- 엔드포인트 정의 ---
@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "API with Supabase is running"}


@app.post("/api/inquiry")
def submit_inquiry(req: InquiryRequest):
    if req.bot_honey:
        return {"status": "success", "message": "접수되었습니다."}

    # 1. Supabase DB 저장
    save_to_supabase(req)

    # 2. Gmail 알림 전송
    send_inquiry_email(req)

    return {"status": "success", "message": "구매 문의가 성공적으로 접수되었습니다. 신속히 안내 연락드리겠습니다!"}


# --- 관리자 기능 엔드포인트 ---
def verify_admin_auth(auth_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    admin_pw = os.getenv("ADMIN_PASSWORD", "admin1234")
    if not auth_token or auth_token != admin_pw:
        raise HTTPException(status_code=401, detail="관리자 인증에 실패했습니다.")


@app.post("/api/admin/login")
def admin_login(req: AdminLoginRequest):
    admin_pw = os.getenv("ADMIN_PASSWORD", "admin1234")
    if req.password == admin_pw:
        return {"status": "success", "token": admin_pw}
    raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")


@app.get("/api/admin/inquiries")
def get_inquiries(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    verify_admin_auth(x_admin_token)
    return fetch_inquiries_from_supabase()


@app.patch("/api/admin/inquiries/{inquiry_id}")
def update_inquiry_status(
    inquiry_id: int,
    req: StatusUpdateRequest,
    x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")
):
    verify_admin_auth(x_admin_token)
    update_inquiry_in_supabase(inquiry_id, req.status, req.memo)
    return {"status": "success", "message": "상태가 변경되었습니다."}
