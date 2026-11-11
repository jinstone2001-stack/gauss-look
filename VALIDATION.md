# GaussLook 검증 기록

## 1.3 검증 — 2026-11-11

- 검증 대상은 `D:\Codex\05.gauss-look`입니다. 이전 ChatGPT 대화의 v1.3 요청(성능, Build/Input 인라인 Gaussian 설정, 스크롤 누적 해소, Light 대비, 파일 구분, 한글 표시, 설정 간격)을 기준으로 v1.2에서 이어서 구현했습니다. 원본 기획서와 LICENSE는 변경하지 않았습니다.
- Windows / Python 3.12.14: **91 passed**(엔진/API 77개 + 실제 Tk UI 14개). cube의 단위·채널·orbital ID와 잘못된 숫자/개수 거부, checkpoint 변경 시 캐시 무효화, 표면 재사용·매핑 분리·캐시 상한, 한글 프로젝트 UTF-8, 최신/오래된 휠 입력·시각 wrap, 정적 결합 재사용, 표시 원자 반경 선택, 현재 frame의 인라인 Gaussian 입력과 저장, 언어 변경 시 MO·분극률 선택 유지 등을 포함합니다.
- 실제 Tk 8.6 win32: 한국어/영어, Light와 한글 글꼴 fallback, 형식별 파일 표시, 작아진 설정창, 인라인 입력·현재 frame·고급 Route/추가 입력의 기존 왕복 시험이 통과했습니다. Linux CI에서도 새 Tk 시험을 Xvfb 대상으로 추가했습니다.
- 실제 Python HTTP 서버 + jsdom/모의 renderer: **DOM passed / errors []**, structures=3, coordinateUpdates=5, renders=13, surfaces=3, features=140. 인라인 입력 생성, 계산별 초안과 분극률 출처 보존, 진동·설정 변경 중 모델 재사용, 최신 휠 입력과 오래된 입력 거부, 폴더/확장자 구분을 확인했습니다. 이 결과는 실제 GPU 시험이 아닙니다.
- 실제 Chrome + 내장 3Dmol.js의 소프트웨어 WebGL: 한국어/Light 화면, 진동 중 GLModel 재사용, 1280×800에서 가로·문서 넘침 없이 Gaussian 생성/다운로드까지 표시, 높이 약 413px인 표시 설정창을 확인했습니다. page error는 0개였습니다.
- Python compileall, 두 웹 JavaScript 구문 검사, `git diff --check`, CLI `--version`(1.3.0)이 통과했습니다. scikit-image 내부의 NumPy 2.5 deprecation warning 70개는 남아 있습니다.

### 합성 성능 비교

같은 Windows/Python 환경에서 v1.2의 해당 함수를 불러 비교했습니다. 아래 시간은 5회 중앙값이며 실제 Gaussian 실행 시간이나 모든 데이터의 성능을 뜻하지 않습니다.

| 항목 | v1.2 / 캐시 전 | v1.3 / 캐시 후 | 확인 |
|---|---:|---:|---|
| cube 읽기: 100³×1, D 지수 1백만 값, 13,333,407 bytes | 0.1287 s | 0.1016 s | 약 21% 시간 감소; 배열 완전 일치 |
| 같은 cube의 Python 추적 peak 메모리 | 91.47 MiB | 83.73 MiB | 약 8.5% 감소; 전체 프로세스 RSS와는 다름 |
| fchk 숫자 배열: coefficient 100,000개, 1,560,089 bytes | 0.07861 s | 0.05994 s | 약 24% 시간 감소; 레코드 일치 |
| 같은 38³ field의 동일 등치면 함수 호출 | 0.001958 s | 0.0000012 s | marching-cubes 재계산 생략; JSON·전송·화면 그리기 제외 |

실제 Windows Tk CPU Canvas에서도 탄소 원자 100개, 620×440 canvas, 회전 redraw 20회와 update_idletasks를 측정했습니다. redraw당 산술 평균은 v1.2 **170.40 ms → v1.3 58.08 ms**로 약 2.93배 빨랐습니다. 위 중앙값 표와는 별도 측정이며 MobaXterm 또는 일반적인 FPS 보장이 아닙니다. 1280×800 실제 Tk 화면에서 가로 한글 글꼴, toolbar/언어 선택, 13개 Gaussian 설정·미리보기·저장이 표시되는 것을 확인했습니다.

실제 Gaussian `formchk/cubegen`, 사용자의 MobaXterm/X11, 실제 GPU와 대형 분자의 장시간 FPS는 검증하지 않았습니다. 원본 격자 해상도·분석 수치·단위는 줄이지 않았으며, 실제 유틸리티 실행 속도는 Gaussian 환경과 파일 크기에 따라 달라집니다.

## 1.2 검증 — 2026-11-11

- Windows / Python 3.12.14: **65 passed**. 기존 분석·parser·utility adapter 시험과 새 폴더/API·Gaussian 입력·실제 Tk 화면 시험을 포함합니다. NumPy 2.5 / scikit-image 내부의 deprecation warning이 남아 있으며, 전체 통합 실행에서는 Tk Variable의 종료 시점 GC 관련 경고도 1회 관찰했습니다.
- 실제 Tk 8.6.12 win32: 한국어↔영어, 도움말 언어 변경, Dark/Light와 사용자 배경색, 설정 저장, 숫자/음수/빈 값 정렬, 정렬 후 원래 모드·frame 선택, 한글·공백 경로 붙여넣기, `..`와 뒤로, 선택 frame의 Gaussian 입력 생성·Route override·저장 일치를 확인했습니다. 이 버전의 MobaXterm/X11 조합은 다시 실행하지 않았습니다.
- 실제 Python 서버 + jsdom/모의 renderer: 기존 MO/진동/Force/분극률/표면/상태표에 더해 숫자 정렬·행 연결, 언어와 설정 저장, theme, 폴더 경로 Enter·상위 폴더, SMILES 입력 유지, 구조화 Gaussian 입력과 Link 0 미리보기를 확인했습니다. **DOM passed / errors []**. 모의 renderer 시험을 실제 GPU 렌더 시험으로 간주하지 않습니다.
- 실제 Chrome: 내장 3Dmol.js의 물 분자 WebGL 표시, 한국어/영어 전환, Dark/Light와 Gaussian 설정·입력 미리보기 화면을 직접 확인했습니다. 숫자 정렬과 PNG 저장도 확인했습니다. 다운로드 완료 이벤트를 기다리는 도구는 시간 초과했지만 실제 생성된 PNG 파일을 별도로 열어 분자 렌더를 확인했습니다. 대형 분자 FPS 또는 모든 GPU·브라우저의 호환성을 측정한 시험은 아닙니다.
- Python compileall과 두 웹 JavaScript 구문 검사를 수행했습니다. CI에는 Linux의 Xvfb/Tk 회귀시험도 추가했습니다.
- `.glproj` 형식과 분석 단위·원문·계산 데이터의 저장 방식은 변경하지 않았습니다. 아래의 1.1 공개 Gaussian 출력 검증은 이전 버전의 근거입니다.
- 실제 Gaussian `formchk/cubegen` 실행 파일이 없어 해당 도구와 새 Gaussian 계산은 검증하지 않았습니다. adapter의 성공·실패·원본 보존은 모의 실행 파일로 검증했습니다.

## 1.1 검증 기록 (이전 버전)

검증일: 2026-11-10. Python 3.12.14 / Linux / Tk 9.0 환경입니다.

## 자동 시험

`python -m pytest -q`: **42 passed**.

1.1 추가 회귀시험: `Full title`의 5개 단어/4개 A12 문자열 재현, 여러 줄 C/H·logical·0개 배열·붙은 E16.8 숫자·손상 레코드, checkpoint Total Energy 우선·force=−gradient·tensor 변환·모드 배열, ROHF 및 분리 spin 점유, frame별 Force/미출력 구별, input→standard 좌표계 Force 회전, CCD 원문 Hartree 보존과 보조 parser 단위 복원, static/response 분극률과 고정밀 archive·Link1 원문 행, 로그·chk 정렬 연결과 불일치 거부, mock cubegen의 ±표면·격자 재사용·snapshot 경로 신뢰 방지, 원본 chk 재변환·원본 보존, 공유 도움말 내용입니다.

검증 범위: 에너지 정밀도·진동수/변위·수렴 기준, Link1별 분리와 원문 행 번호, frequency 미수행/잘린 출력/SCF 실패, Raman 레이저 의존성, broadening 면적, 거리/각도와 정의 불가 조건, fchk 좌표·에너지 단위/손상 배열, Gaussian 입력 왕복과 spin parity, 편집 후 계산 데이터 해제, 프로젝트의 임의 경로 접근 방지, cube 단위·값 수·mesh·보간·격자 불일치, 저주파 보정, Kabsch 정렬, API·원문 폴더 범위·교차 출처 거부, mock formchk의 원본 보존 및 utility 실패 처리, 조건이 다른 계산의 상대 에너지 순위 방지, 선형 이원자 분자의 isotope 질량 배율.

`node --check web/app.js` 및 `web/core.js`: 통과. Python compileall: 통과.

## 공개 Gaussian 출력 확인

개발 중 [cclib-data](https://github.com/cclib/cclib-data)의 공개 표본을 내려받아 분석했습니다. 표본 원문은 이 저장소에 재배포하지 않습니다.

| 표본 | 확인 결과 |
|---|---|
| Gaussian16/water.log | Opt/Freq 2개 작업 분리, 원자 3개, frequency 작업의 모드 3개, 전자 에너지 -76.340665699 Eh |
| Gaussian16/water_neutral_nbo_opt_freq.out | Opt/Freq 분리, 원자 3개, frequency 3개, 전하·MO·열화학 읽기 |
| Gaussian16/C01_CC.log | 원자 3개, **CCD 원문 에너지 -75.017378003 Eh**. 1.0 검증 기록의 -75.01737470585509 Eh는 보조 parser의 eV 변환 상수를 다른 상수로 되돌린 값이었으며 1.1에서 수정 |
| Gaussian16/mp2_avdz_freq_tight.log | 원자 21개, 모드 57개, MP2 에너지 -551.55801572117 Eh |
| Gaussian16/dvb_cm5_hirshfeld.out | 원자 20개, 구조·SCF·기본 전하 읽기. 추가 CM5/Hirshfeld 표는 출력 형식별 지원 공백이 있어 완전 추출을 주장하지 않음 |
| FChk/Gaussian09/dvb_gopt_qchem.fchk 및 unconverged 파일 | 원자 20개, MO 60개, 두 파일 모두 checkpoint만으로 수렴 성공을 판정하지 않음 |

1.1 주요 수치: water.log의 Freq 작업에서 Cartesian max component=0.000376422 Eh/Bohr, 고정밀 평균 분극률=5.409541693333334 a.u.=0.8016113750223544 Å³를 읽었습니다. MP2 표본의 Force를 input→standard 좌표계로 회전한 후 max component=0.00035483577446647317 Eh/Bohr, 평균 분극률=125.8739756 a.u.=18.652598756119566 Å³입니다. 출력 정밀도 내의 parser 확인이며 새 Gaussian 계산으로 물성을 독립 검증한 것은 아닙니다.

최적화 로그의 마지막 반복 출력 구조에 별도 에너지·Force 레코드가 없으면 미출력으로 표시합니다. 앞 frame의 값을 복사하지 않습니다. source가 검증된 동일 구조의 checkpoint를 연결하면 현재 frame의 누락 에너지/Force를 checkpoint 기록으로 보완합니다.

## X11 실제 화면 시험

동일한 시험 프로세스 안에서 Xorg dummy display를 실행하고 TCP X11로 연결했습니다. 1.1의 HOMO/LUMO 선택·클릭 diagram·양/음 CPU 표면, 공개 water.log 로드, 원자별 Force 3행·벡터, 분극률 tensor 3행, 진동 재생·평형 구조 복원, 도움말 검색·실제 tooltip 창 표시를 실행하고 X11 화면을 캡처해 확인했습니다. 41개 작업 버튼에 hover 설명이 연결되었습니다.

검증 환경의 Tk는 CJK font를 제공하지 않아 영문 UI fallback을 추가했습니다. 한글 font가 있는 MobaXterm 사용자 환경은 이 환경과 다르며, 실제 사용자의 서버·MobaXterm 조합으로 추가 확인이 필요합니다. 프레임 속도를 정량 benchmark하거나 모든 X11 환경의 성능을 보장한 것은 아닙니다.

## 웹 검증

실제 Python HTTP 서버와 연결한 jsdom UI/API 시험을 수행했습니다. `tests/run_ui_dom.py`와 `tests/ui_dom.cjs`는 합성 fixture에서 초기 계산 표시·hover 설명, LUMO 번호/diagram 선택, ±MO 표면 후 원래 계산 선택 유지, frame 변경에 따른 미출력/에너지·Force 표시, 분극률, 도움말 검색, imaginary 필터·재생·기준 구조 복원, IR·cube mesh·조건 비교·140개 상태표를 확인합니다. 결과: **DOM passed, structures 6, surfaces 3, features 140, errors []**. CI에도 이 시험을 추가했습니다.

이 DOM 시험은 3Dmol renderer를 mock으로 대체하므로 **실제 브라우저/WebGL GPU 렌더 검증과 구별**합니다. 개발 실행 환경에서 Chromium이 필요한 Unix socket을 사용할 수 없어 실제 브라우저 렌더 시험은 완료하지 못했습니다. 3Dmol.js 2.5.5는 upstream 배포물을 포함했으며, 사용자 브라우저에서 첫 실행 시 WebGL 상태를 확인하세요.

## 검증하지 않은 외부 기능

Gaussian 실행 파일이 없어 실제 formchk/cubegen 실행은 검증하지 않았습니다. utility wrapper는 mock executable로 성공/실패·원본 보존을 확인했습니다. 새 Gaussian 계산을 수행해 결과 정확도를 검증한 것은 아닙니다. 대형 파일·상관 밀도·고각운동량 기저·특수 ONIOM/PBC/응답 출력은 실제 표본을 추가해 검증해야 합니다.

## 실행 방법

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
python -m compileall -q gausslook GaussLook.py
node --check web/app.js
node --check web/core.js
npm install --prefix /tmp/gausslook-ui jsdom@26.1.0
NODE_PATH=/tmp/gausslook-ui/node_modules python tests/run_ui_dom.py
```

DOM 시험에는 별도 개발용 `jsdom`이 필요하며 launcher가 같은 namespace에서 서버를 함께 실행합니다. 사용자 프로그램 실행에는 Node나 jsdom이 필요하지 않습니다.
