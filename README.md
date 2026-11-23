# ⚡ 단타 검색기 (안드로이드 앱)

## 구조
- `scan.py` : 전 종목 시세 → 단타 지표 계산 → `docs/data.json` 저장
- `.github/workflows/update.yml` : 평일 장중 5분마다 scan.py 자동 실행
- `docs/` : 앱 화면 (GitHub Pages로 배포 → APK로 포장)

## 1. 깃허브에 올리기
1. github.com 가입 → New repository → 이름 `danta` → **Public** → Create
2. "uploading an existing file" → 이 폴더 안의 파일을 모두 올림
   (휴대폰에서 `.github` 폴더가 안 올라가면: Add file → Create new file →
   이름에 `.github/workflows/update.yml` 입력 → 내용 붙여넣기)

## 2. 자동 갱신 켜기
- Settings → Actions → General → Workflow permissions → **Read and write** → Save
- Actions 탭 → "단타 데이터 갱신" → Run workflow (첫 데이터 생성)

## 3. 앱 주소 만들기
- Settings → Pages → Branch: `main`, 폴더: `/docs` → Save
- 1~2분 뒤 주소 생성: `https://아이디.github.io/danta/`

## 4. APK로 포장 (휴대폰 가능)
- WebIntoApp.com 같은 웹→APK 변환 사이트에 3번 주소 입력
- 앱 이름 "단타 검색기", 아이콘은 `docs/icon-512.png` 사용
- 만들어진 APK 파일을 회원들에게 전달 (설치 시 "출처를 알 수 없는 앱" 허용 필요)

## 바꾸고 싶을 때
- 화면/전략 수정: `docs/index.html` 수정 → 앱 재설치 없이 바로 반영
- 점수 계산: `scan.py`의 build() 함수
