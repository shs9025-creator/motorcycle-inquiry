import http.server
import json
import os
import smtplib
import socketserver
import urllib.parse
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), "public")

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

load_env()

def send_inquiry_mail(data):
    gmail_user = os.getenv("GMAIL_USER") or os.getenv("GMAIL_ADDRESS")
    gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_user or not gmail_pass:
        raise ValueError("GMAIL_USER 또는 GMAIL_APP_PASSWORD가 설정되지 않았습니다.")

    clean_user = gmail_user.strip()
    clean_pass = gmail_pass.replace(" ", "").strip()

    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

    urgency = data.get("urgency", "상담 희망")
    urgency_badge = "🔥 [즉시출고 희망]" if "즉시" in urgency else f"[{urgency}]"

    name = data.get("name", "고객")
    brand = data.get("brand", "")
    model = data.get("model", "")
    phone = data.get("phone", "")
    region = data.get("region", "")
    condition = data.get("condition", "")
    payment_method = data.get("payment_method", "")
    trade_in = data.get("trade_in", "")
    trade_in_model = data.get("trade_in_model", "")
    delivery_method = data.get("delivery_method", "")
    contact_time = data.get("contact_time", "")
    message = data.get("message", "")

    subject = f"[바이크 구매문의] {name} 고객님 - {brand} {model} {urgency_badge}"

    trade_in_text = f"{trade_in} ({trade_in_model})" if trade_in_model else trade_in

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
            <tr><th>고객 성함</th><td><strong>{name}</strong> 님</td></tr>
            <tr>
              <th>연락처</th>
              <td>
                <a href="tel:{phone}" style="color:#0284c7; font-weight:bold; font-size:16px;">{phone}</a>
                <br>
                <a href="tel:{phone}" class="call-btn">📞 지금 바로 전화 걸기</a>
              </td>
            </tr>
            <tr><th>거주 지역</th><td>{region}</td></tr>
            <tr><th>통화 희망 시간</th><td><strong>{contact_time}</strong></td></tr>
          </table>

          <div class="section-title">2. 관심 차량 정보</div>
          <table>
            <tr><th>브랜드</th><td>{brand}</td></tr>
            <tr><th>희망 모델</th><td><strong style="font-size:16px; color:#0f172a;">{model}</strong></td></tr>
            <tr><th>차량 상태</th><td>{condition}</td></tr>
            <tr><th>수령 방식</th><td>{delivery_method}</td></tr>
          </table>

          <div class="section-title">3. 구매 조건 & 일정</div>
          <table>
            <tr><th>결제 방식</th><td><strong>{payment_method}</strong></td></tr>
            <tr><th>출고 희망일</th><td><strong style="color:#dc2626;">{urgency}</strong></td></tr>
            <tr><th>기존 바이크 대차</th><td>{trade_in_text}</td></tr>
          </table>

          <div class="section-title">4. 추가 문의 및 요청사항</div>
          <div class="memo-box">
            {message.replace(chr(10), '<br>') if message and message.strip() else '추가 작성 내용 없음'}
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

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(clean_user, clean_pass)
        server.sendmail(clean_user, clean_user, msg.as_string())


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        # /api/health 요청 처리
        if self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
            return
        
        # 루트 경로는 index.html 서비스
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/inquiry":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                
                # Honeypot 스팸 체크
                if not data.get("bot_honey"):
                    send_inquiry_mail(data)

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                resp = {"status": "success", "message": "성공적으로 문의가 접수되었습니다."}
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                resp = {"detail": f"메일 전송 실패: {str(e)}"}
                self.wfile.write(json.dumps(resp).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"🚀 [로컬 서버 실행 중] http://localhost:{PORT}")
        httpd.serve_forever()
