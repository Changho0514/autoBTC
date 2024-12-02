### 📱 봇코인(GPT 기반 비트코인 자동매매 시스템)

*2024.07 - 2024.08(4주) | 개인 프로젝트*

OpenAI와 기술적 분석을 결합한 자동화된 암호화폐 트레이딩 시스템 개발

**Technical Achievement**

- OpenAI GPT-4 Vision API를 활용한 차트 이미지 분석 및 매매 판단 로직 구현
- WebSocket을 활용한 실시간 시세 모니터링 시스템 구축
- SQLite를 활용한 거래 내역 데이터베이스 설계 및 구현
- Selenium을 활용한 차트 데이터 자동 수집 시스템 구현

**Key Features**

- 기술적 지표(RSI, MACD, 볼린저 밴드 등) 기반 실시간 매매 신호 생성
- YouTube 트레이딩 전문가의 투자 전략을 학습하여 매매 로직에 반영
- Fear & Greed Index, 실시간 뉴스 데이터를 활용한 시장 심리 분석
- Streamlit을 활용한 실시간 대시보드로 투자 현황 모니터링
- 자체 회고 시스템을 통한 매매 전략 자동 개선

**Challenge & Solution**

1. 대규모 데이터 처리
    - Challenge: 실시간 시세, 차트, 뉴스 데이터의 효율적 처리 필요
    - Solution: Redis 캐싱 및 배치 처리 도입으로 처리 속도 최적화
2. 실시간 이미지 분석 최적화
    - Challenge: Selenium을 통한 차트 이미지 크롤링이 EC2 환경에서 불안정하게 동작
    - Solution: 헤드리스 브라우저 설정 및 이미지 캡처 로직 최적화로 안정성 확보
3. 서버 안정성
    - Challenge: 실시간으로 가져오는 YouTube 스크립트 데이터가 GPT 토큰 제한에 빈번히 도달하고, API 비용 증가 문제 발생
    - Solution: YouTube-transcript-api를 활용해 주요 투자자들의 핵심 전략을 JSON 형태로 구조화하여 로컬 스토리지에 저장하고, 정기적으로 업데이트하는 캐싱 메커니즘 구현으로 토큰 사용량 90% 절감

**Tech Stack**

- Language & Framework: `Python` `Streamlit` `Selenium`
- AI/ML: `OpenAI GPT-4` `Technical Analysis Library`
- Database: `SQLite` `Redis`
- Infrastructure: `AWS EC2` `Jenkins` `Docker`
- API: `Upbit API` `Google News API` `YouTube API`
