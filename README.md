# 🏍️ 오토바이 구매 문의 랜딩페이지 (Vercel + Python 배포)

고객이 오토바이 구매 문의를 남기면 사장님의 Gmail로 즉시 상세 견적 메일이 발송되는 랜딩페이지입니다.

---

## 📁 프로젝트 구조

```text
gmail_example/
├── api/
│   └── index.py            # FastAPI 백엔드 (Gmail SMTP 발송 및 입력 검증)
├── public/
│   └── index.html          # 반응형 오토바이 구매 문의 랜딩페이지 UI
├── .env.example            # 로컬 환경변수 예시 파일
├── .gitignore              # .env 및 임시 파일 제외
├── requirements.txt        # 파이썬 의존 패키지
├── vercel.json             # Vercel 배포 라우팅 설정
└── README.md
```

---

## 🔑 1. 사전 준비 (Google 앱 비밀번호 발급)

1. [Google 계정 관리 (myaccount.google.com)](https://myaccount.google.com/) 접속
2. **보안** 탭 > **2단계 인증** 활성화
3. 맨 아래 **[앱 비밀번호 (App passwords)]** 클릭
4. 앱 이름 입력 (예: `bike-landing`) 후 **만들기** 클릭
5. 생성된 **16자리 비밀번호** (예: `abcd efgh ijkl mnop`) 복사

---

## 💻 2. 로컬에서 테스트하기

1. **환경변수 파일 생성 (`.env`)**:
   최상위 폴더에 `.env` 파일을 만들고 발급받은 정보 입력:
   ```env
   GMAIL_USER=사장님_이메일@gmail.com
   GMAIL_APP_PASSWORD=16자리앱비밀번호
   ```

2. **패키지 설치 및 실행**:
   ```bash
   pip install -r requirements.txt
   uvicorn api.index:app --reload --port 8000
   ```
   * 브라우저에서 `http://localhost:8000/public/index.html` 또는 라이브 서버를 통해 접속 가능

---

## 🚀 3. Vercel 배포 방법

### 방법 A: Vercel CLI로 배포 (터미널)
```bash
# 1. vercel 설치 (기존에 없는 경우)
npm i -g vercel

# 2. 배포 명령어 실행
vercel
```

### 방법 B: GitHub 연동 배포 (추천)
1. GitHub 저장소(Repository)에 본 프로젝트 코드를 업로드 (Push).
2. [Vercel 대시보드](https://vercel.com/dashboard)에서 **Add New...** > **Project** 클릭.
3. 방금 올린 GitHub 저장소를 선택(Import).
4. **Environment Variables** 설정 섹션에서 다음 2개 값을 등록:
   * `GMAIL_USER` : 사장님의 Gmail 주소
   * `GMAIL_APP_PASSWORD` : 16자리 Google 앱 비밀번호
5. **Deploy** 버튼 클릭! (배포 완료 후 제공되는 도메인으로 즉시 사용 가능)
