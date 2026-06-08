# 성능 최적화 기록

배포하고 나니 차트 페이지가 눈에 띄게 느려서, 원인을 하나씩 측정해가며 고친 내용을 정리했습니다.
아래 크기·시간 값은 모두 실제로 잰 수치이고, 어떻게 쟀는지도 같이 적어뒀습니다.

처음엔 백엔드가 느린 줄 알았는데 측정해 보니 병목은 두 군데였습니다.
응답을 압축 없이 통째로 내려보내던 API와, 1만 개가 넘는 캔들을 한 번에 그리던 차트입니다.

## 한눈에 보기

| 영역 | 한 일 | 결과 |
|------|------|------|
| API 응답 크기 | gzip 압축 | 1.99 MB → 263 KB |
| API 응답 시간 | 압축 + CDN 캐싱 | 약 2초 → 0.15~0.49초 |
| 차트 렌더 | ApexCharts → lightweight-charts | 11,125개 캔들도 부드럽게 |
| JS 번들 | apexcharts 제거 | gzip 183 KB → 99 KB |

## 백엔드 API

문제의 엔드포인트는 나스닥 일봉 11,125행을 통째로 내려주는 `GET /api/nasdaq_chart`였습니다.

### 압축이 꺼져 있었다

응답이 1.99 MB였는데, JSON은 컬럼명이 행마다 반복되는 구조라 압축만 켜도 크게 줄어들 데이터였습니다.
FastAPI에 `GZipMiddleware`를 더하니 263 KB로, 약 7.5배 작아졌습니다.

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

압축 전후 크기는 이렇게 확인했습니다.

```bash
curl -s -o /dev/null -w "%{size_download}\n" \
  https://database-nasdaq.vercel.app/api/nasdaq_chart                    # 1989350
curl -s -H "Accept-Encoding: gzip" -o /dev/null -w "%{size_download}\n" \
  https://database-nasdaq.vercel.app/api/nasdaq_chart                    # 263033
```

### 캐싱이 안 되고 있었다

응답 헤더가 `max-age=0, must-revalidate`라 요청이 올 때마다 서버리스 함수가 새로 뜨고
SQLite를 다시 읽었습니다(`x-vercel-cache: MISS`). 이 데이터는 한 번 만들어지면 바뀌지 않으니,
`Cache-Control`에 긴 `s-maxage`를 주면 엣지가 대신 응답할 수 있습니다.
배포할 때마다 Vercel이 캐시를 비워주기 때문에 TTL을 길게 잡아도 안전합니다.

```python
CACHE_CONTROL = "public, max-age=300, s-maxage=31536000, stale-while-revalidate=86400"
# 각 엔드포인트에서: response.headers["Cache-Control"] = CACHE_CONTROL
```

압축과 캐싱을 함께 적용한 뒤 응답 시간은 약 2초에서 0.15~0.49초로 줄었습니다.

## 프론트엔드 차트

차트는 일봉 11,125개를 캔들스틱으로 그립니다. ApexCharts는 캔들 하나하나를 SVG 요소로 만드는데,
보통 1~2천 개를 넘으면 버거워합니다. 1만 개가 넘으니 첫 렌더에 몇 초씩 걸리고 줌·팬도 뚝뚝 끊겼습니다.

결국 차트 라이브러리 자체를 바꿨습니다. TradingView의 `lightweight-charts`(v5)는
canvas에 한 번에 그리는 방식이라 캔들이 1만 개를 넘어도 부드럽게 그리고 움직입니다.
데이터는 그대로 쓰되, 옮기면서 몇 가지를 맞춰줬습니다.

- API는 날짜 내림차순으로 주는데 lightweight-charts는 오름차순을 요구해서 정렬
- 날짜 문자열에 공백이 섞여 있어(`"2024- 05- 01"`) 제거
- 중복 날짜·결측값 거르기 (11,125행 모두 유효한 건 미리 확인)

라이브러리를 바꾸면서 `apexcharts`를 걷어내니 빌드 번들(JS, gzip)도 183 KB에서 99 KB로 줄어,
페이지가 처음 뜨는 속도까지 함께 빨라졌습니다.

## 측정 환경

- 백엔드: Vercel 서버리스(FastAPI) — `database-nasdaq.vercel.app`
- 프론트: Vercel 정적 호스팅(CRA) — `database-nasdaq-dyb7.vercel.app`
- 크기·시간은 `curl`로, 번들 크기는 CRA 빌드 출력으로 측정
- 차트 렌더 속도는 따로 수치를 재진 않았고, 체감과 라이브러리 특성에 근거한 설명입니다
