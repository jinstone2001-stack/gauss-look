# GaussLook 1.1 검증 기록

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
