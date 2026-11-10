# GaussLook 1.0 검증 기록

검증일: 2026-11-10. Python 3.12.14 / Linux / Tk 9.0 환경입니다.

## 자동 시험

`python -m pytest -q`: **24 passed**.

검증 범위: 에너지 정밀도·진동수/변위·수렴 기준, Link1별 분리와 원문 행 번호, frequency 미수행/잘린 출력/SCF 실패, Raman 레이저 의존성, broadening 면적, 거리/각도와 정의 불가 조건, fchk 좌표·에너지 단위/손상 배열, Gaussian 입력 왕복과 spin parity, 편집 후 계산 데이터 해제, 프로젝트의 임의 경로 접근 방지, cube 단위·값 수·mesh·보간·격자 불일치, 저주파 보정, Kabsch 정렬, API·원문 폴더 범위·교차 출처 거부, mock formchk의 원본 보존 및 utility 실패 처리, 조건이 다른 계산의 상대 에너지 순위 방지, 선형 이원자 분자의 isotope 질량 배율.

`node --check web/app.js`: 통과. Python compileall: 통과.

## 공개 Gaussian 출력 확인

개발 중 [cclib-data](https://github.com/cclib/cclib-data)의 공개 표본을 내려받아 분석했습니다. 표본 원문은 이 저장소에 재배포하지 않습니다.

| 표본 | 확인 결과 |
|---|---|
| Gaussian16/water.log | Opt/Freq 2개 작업 분리, 원자 3개, frequency 작업의 모드 3개, 전자 에너지 -76.340665699 Eh |
| Gaussian16/water_neutral_nbo_opt_freq.out | Opt/Freq 분리, 원자 3개, frequency 3개, 전하·MO·열화학 읽기 |
| Gaussian16/C01_CC.log | 원자 3개, CC 최종 에너지 -75.01737470585509 Eh; SCF와 구별 |
| Gaussian16/mp2_avdz_freq_tight.log | 원자 21개, 모드 57개, MP2 에너지 -551.55801572117 Eh |
| Gaussian16/dvb_cm5_hirshfeld.out | 원자 20개, 구조·SCF·기본 전하 읽기. 추가 CM5/Hirshfeld 표는 출력 형식별 지원 공백이 있어 완전 추출을 주장하지 않음 |
| FChk/Gaussian09/dvb_gopt_qchem.fchk 및 unconverged 파일 | 원자 20개, MO 60개, 두 파일 모두 checkpoint만으로 수렴 성공을 판정하지 않음 |

## X11 실제 화면 시험

동일한 시험 프로세스 안에서 Xorg dummy display를 실행하고 TCP X11로 연결했습니다. Tk GUI 생성·데모 읽기·진동 모드 선택·스펙트럼·CPU 표면을 실행하고 실제 X11 화면을 캡처해 확인했습니다. 모드 표 3개와 약 2900개 canvas 항목을 확인했습니다.

검증 환경의 Tk는 CJK font를 제공하지 않아 영문 UI fallback을 추가했습니다. 한글 font가 있는 MobaXterm 사용자 환경은 이 환경과 다르며, 실제 사용자의 서버·MobaXterm 조합으로 추가 확인이 필요합니다. 프레임 속도를 정량 benchmark하거나 모든 X11 환경의 성능을 보장한 것은 아닙니다.

## 웹 검증

실제 Python HTTP 서버와 연결한 jsdom UI/API 시험을 수행했습니다. `tests/ui_dom.cjs`는 초기 계산 표시, IR 스펙트럼 요청, cube mesh 요청과 유한한 vertex/faces 전달, 조건 비교, 140개 상태표 표시를 확인했습니다. 결과: **DOM passed, structures 1, surfaces 1, features 140, errors []**.

이 DOM 시험은 3Dmol renderer를 mock으로 대체하므로 **실제 브라우저/WebGL GPU 렌더 검증과 구별**합니다. 개발 실행 환경에서 Chromium이 필요한 Unix socket을 사용할 수 없어 실제 브라우저 렌더 시험은 완료하지 못했습니다. 3Dmol.js 2.5.5는 upstream 배포물을 포함했으며, 사용자 브라우저에서 첫 실행 시 WebGL 상태를 확인하세요.

## 검증하지 않은 외부 기능

Gaussian 실행 파일이 없어 실제 formchk/cubegen 실행은 검증하지 않았습니다. utility wrapper는 mock executable로 성공/실패·원본 보존을 확인했습니다. 새 Gaussian 계산을 수행해 결과 정확도를 검증한 것은 아닙니다. 대형 파일·상관 밀도·고각운동량 기저·특수 ONIOM/PBC/응답 출력은 실제 표본을 추가해 검증해야 합니다.

## 실행 방법

```bash
python -m pip install -r requirements.txt pytest
python -m pytest -q
python -m compileall -q gausslook GaussLook.py
node --check web/app.js
```

DOM 시험에는 별도 개발용 `jsdom`과 같은 프로세스 namespace에서 구동한 서버 URL이 필요합니다. 사용자 실행에는 Node나 jsdom이 필요하지 않습니다.
