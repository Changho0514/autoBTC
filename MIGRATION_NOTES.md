# AutoBTC 마이그레이션 작업 기록

## 작업 일자
2026년 1월 14일

## 작업 목적
1. OpenAI API 의존성 제거 및 Google Gemini API로 교체 (비용 절감)
2. 로컬 실행 환경에서 클라우드 자동화 환경으로 전환 (무료)

---

## 1. LLM API 교체: OpenAI → Google Gemini

### 변경 사유
- OpenAI API 비용 발생
- Google Gemini API 무료 티어 활용 (gemini-2.5-flash)

### 수정된 파일

#### `gptbitcoin.py` (Upbit 기반 메인 트레이딩 봇)
- **import 변경**
  ```python
  # Before
  from openai import OpenAI

  # After
  import google.generativeai as genai
  ```

- **API 설정 추가**
  ```python
  genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
  ```

- **모델 호출 변경**
  ```python
  # Before
  client = OpenAI()
  response = client.chat.completions.create(
      model="gpt-4o-2024-08-06",
      messages=[...],
      response_format={...}
  )

  # After
  model = genai.GenerativeModel('gemini-2.5-flash')
  response = model.generate_content(
      prompt,
      generation_config=genai.GenerationConfig(
          response_mime_type="application/json",
      )
  )
  ```

- **무한 루프 제거** (클라우드 스케줄링으로 대체)
  ```python
  # Before
  while True:
      ai_trading()
      time.sleep(3600 * 8)

  # After
  if __name__ == "__main__":
      ai_trading()
  ```

#### `chart_gpt_coin.py` (Bithumb 기반 트레이딩 봇)
- 동일한 방식으로 OpenAI → Gemini 교체
- 무한 루프 제거

#### `requirements.txt`
```
# Before
openai

# After
google-generativeai
```

---

## 2. 인프라 구성: Oracle Cloud VM

### 선택 이유
- **GitHub Actions 불가**: Upbit API가 IP 화이트리스트 필요, GitHub Actions는 동적 IP 사용
- **Oracle Cloud Free Tier**: 평생 무료 VM + 고정 IP 제공

### VM 설정 과정

#### 2.1 Oracle Cloud VM 생성
1. Oracle Cloud 계정 생성
2. Compute → Instances → Create Instance
3. Shape: VM.Standard.E2.1.Micro (Always Free)
4. OS: Ubuntu 22.04 또는 24.04

#### 2.2 고정 IP 확인 및 Upbit API 등록
1. VM의 Public IP 확인
2. Upbit → 마이페이지 → Open API 관리
3. API 키 생성 시 해당 IP 등록

#### 2.3 VM 환경 설정
```bash
# SSH 접속
ssh ubuntu@<VM_IP>

# 필수 패키지 설치
sudo apt update && sudo apt install -y python3 python3-pip git
sudo apt install python3.12-venv -y

# 코드 클론
git clone https://github.com/Changho0514/autoBTC.git
cd autoBTC

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

#### 2.4 환경변수 설정
```bash
nano .env
```

`.env` 파일 내용:
```
UPBIT_ACCESS_KEY=업비트_액세스_키
UPBIT_SECRET_KEY=업비트_시크릿_키
GEMINI_API_KEY=구글_제미나이_API_키
SERP_API_KEY=서프_API_키
```

#### 2.5 테스트 실행
```bash
source venv/bin/activate
python3 gptbitcoin.py
```

---

## 3. 자동화 설정: Cron

### 스케줄 (하루 3번)
| UTC | KST | 설명 |
|-----|-----|------|
| 00:00 | 09:00 | 아침 |
| 08:00 | 17:00 | 저녁 |
| 16:00 | 01:00 | 새벽 |

### Cron 설정
```bash
crontab -e
```

추가 내용:
```cron
0 0 * * * cd /home/ubuntu/autoBTC && /home/ubuntu/autoBTC/venv/bin/python3 gptbitcoin.py >> /home/ubuntu/autoBTC/trade.log 2>&1
0 8 * * * cd /home/ubuntu/autoBTC && /home/ubuntu/autoBTC/venv/bin/python3 gptbitcoin.py >> /home/ubuntu/autoBTC/trade.log 2>&1
0 16 * * * cd /home/ubuntu/autoBTC && /home/ubuntu/autoBTC/venv/bin/python3 gptbitcoin.py >> /home/ubuntu/autoBTC/trade.log 2>&1
```

### 로그 확인
```bash
tail -f /home/ubuntu/autoBTC/trade.log
```

---

## 4. 새로 추가된 파일

### `.env.example`
환경변수 템플릿 파일
```
UPBIT_ACCESS_KEY=your_upbit_access_key
UPBIT_SECRET_KEY=your_upbit_secret_key
GEMINI_API_KEY=your_gemini_api_key
SERP_API_KEY=your_serp_api_key
```

### `.github/workflows/auto-trade.yml`
GitHub Actions 워크플로우 (현재 미사용 - IP 제한 문제로 Oracle VM 사용)

---

## 5. 비용 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| LLM API | OpenAI (유료) | Gemini 2.5 Flash (무료) |
| 서버 | 로컬 PC 상시 가동 | Oracle Cloud VM (무료) |
| **월 비용** | **약 $20~50** | **$0** |

---

## 6. 모델 변경 히스토리

시도한 모델들:
1. `gemini-3-flash` → 404 에러 (모델명 없음)
2. `gemini-3-pro-preview` → 429 에러 (무료 티어 없음)
3. `gemini-2.5-flash` → **성공** (무료 티어 지원)

---

## 7. 유지보수 명령어

### VM 접속
```bash
ssh ubuntu@<VM_IP>
```

### 코드 업데이트
```bash
cd ~/autoBTC
git pull
```

### 수동 실행
```bash
source venv/bin/activate
python3 gptbitcoin.py
```

### 로그 확인
```bash
tail -f ~/autoBTC/trade.log
```

### Cron 확인/수정
```bash
crontab -l  # 확인
crontab -e  # 수정
```

### Streamlit 대시보드 실행
```bash
source venv/bin/activate
nohup streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

---

## 8. 트러블슈팅

### 문제: `externally-managed-environment` 에러
```bash
# 해결: 가상환경 사용
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 문제: Gemini API 모델을 찾을 수 없음
```
# 사용 가능한 무료 모델: gemini-2.5-flash
# gemini-3-pro는 무료 티어 없음
```

### 문제: Upbit API IP 제한
```
# GitHub Actions 대신 Oracle Cloud VM 사용 (고정 IP)
```

---

## 작성자
- 마이그레이션 작업: Claude Opus 4.5
- 작업일: 2026-01-14
