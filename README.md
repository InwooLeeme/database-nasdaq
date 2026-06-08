# 나스닥 패턴 분석 차트

나스닥 종합지수의 과거 데이터(1980~2024년, 일봉)를 캔들차트로 보여주고,
특정 기간의 주가 흐름과 가장 비슷하게 움직였던 과거 구간을 찾아보는 프로젝트입니다.
"지금과 닮은 흐름이 과거에도 있었다면 그 뒤엔 어떻게 됐을까?"라는 질문을
코사인·피어슨 유사도로 따져보는 것을 목표로 합니다.

## 구성

- `front/` — React(CRA) + lightweight-charts로 만든 캔들차트
- `back/` — FastAPI + SQLite. 과거 데이터 API와 유사도 분석 스크립트
- `api/` — Vercel 서버리스 배포용 백엔드 진입점

프론트와 백엔드는 각각 별도의 Vercel 프로젝트로 배포합니다.

## 실행 방법

### 백엔드

```bash
cd back
pip install -r requirements.txt
uvicorn main:app --reload          # http://127.0.0.1:8000
```

CSV에서 데이터베이스를 다시 만들고 싶다면:

```bash
python database.py     # CSV → chart.db 의 stocks 테이블 적재
python cosine.py       # 코사인 유사도 계산 후 저장
```

### 프론트엔드

```bash
cd front
npm install
npm start              # http://localhost:3000
```

로컬에서는 `REACT_APP_API_URL`을 비워두면 자동으로 `http://127.0.0.1:8000`을 사용합니다.

## API

- `GET /nasdaq_chart` — 일봉 OHLC 데이터
- `GET /cosine_similarity` — 유사도가 높은 과거 구간 목록

배포 환경에서는 `/api` 접두사가 붙습니다 (예: `/api/nasdaq_chart`).

## 성능 최적화

응답 크기를 gzip으로 87% 줄이고, 차트 렌더링을 SVG에서 canvas로 옮기는 등
성능을 개선한 과정은 [docs/PERFORMANCE.md](docs/PERFORMANCE.md)에 따로 정리해 두었습니다.
