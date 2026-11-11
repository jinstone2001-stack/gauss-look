# GaussLook 1.3 사용자 도움말

프로그램의 도움말 또는 F1에서 같은 내용을 검색할 수 있습니다. 한국어/English는 화면에서 선택합니다.

## 1.3 작업공간·입력과 반응 속도

구조·입력 탭에서 Gaussian 설정과 미리보기를 바로 사용합니다. 빠른 스크롤은 최신 입력만 반영합니다.

구조·입력 탭에서 작업, method/basis, 전하/spin, 메모리/core, checkpoint, title, 고급 Route와 추가 입력을 설정하고 미리보기·저장합니다. 테마나 언어를 바꿔도 입력 초안과 선택한 MO·분극률 출처를 유지합니다. 폴더와 파일 형식은 별도 표시로 구분합니다. 한국어에서는 한글 글꼴을 우선 선택하며 서버에도 한글 글꼴이 필요합니다. 회전·확대의 중복 그리기를 합치고 진동 중 모델을 재사용합니다. MO cube는 원본 checkpoint의 경로·크기·수정 시각, spin/MO/격자가 같으면 재사용합니다. 같은 field·등치값의 표면도 최근 8개까지 재사용하며 원래 격자와 단위는 유지합니다. 새 chk 읽기는 원본을 다시 변환하며 Gaussian 실행 자체의 속도는 도구와 계산 크기에 따라 다릅니다.

관련 버튼: 구조·입력, Build / Input, 미리보기, Preview

## 언어·테마·화면 설정과 표 정렬

설정에서 한국어/English, Dark/Light와 분자 표시를 선택합니다. 표 머리글은 숫자 값을 기준으로 정렬합니다.

언어는 UI 설명을 바꾸며 Gaussian keyword, 원본 계산명, 수치와 단위는 유지합니다. 테마와 분자 배경색은 별도 설정입니다. 원자/결합 크기와 label은 표시만 바꾸며 좌표나 분석값은 바꾸지 않습니다. 표 머리글을 다시 누르면 오름차순/내림차순을 전환합니다. 정렬한 행을 선택해도 원래 MO/모드/원자와 연결됩니다. 서버 폴더의 경로 입력칸에 경로를 붙여넣고 Enter 또는 이동을 누르세요. '..'와 상위 폴더 버튼으로 되돌아갑니다. 웹에서는 --root 안의 폴더만 접근합니다. Gaussian 입력창에서 작업, method/basis, 전하/spin, Link 0, title과 추가 입력을 설정하고 미리보기 후 .gjf를 저장합니다. 고급 Route와 Gen/ECP 등 추가 입력은 사용자가 계산 조건을 확인해야 합니다. SMILES 입력은 계속 사용할 수 있습니다.

관련 버튼: 설정, Settings, 서버 폴더, Server folder, Gaussian 입력, Gaussian input

## 처음 사용하기 · 필요한 파일

log는 계산 과정·에너지·진동을, chk/fchk는 MO 파동함수 등을 제공합니다. 두 파일을 같은 계산에서 준비하세요.

1. 파일 열기로 .log와 같은 계산의 .chk 또는 .fchk를 엽니다.
2. chk는 서버의 formchk로 안전한 복사본을 변환합니다. 원본은 수정하지 않습니다.
3. 로그를 선택하고 로그·chk 연결에서 최종 구조가 일치하는 checkpoint를 연결하면 한 항목에서 로그 분석과 MO 표면을 사용할 수 있습니다.
4. MO, 진동, 에너지·Force, 분극률 탭을 사용하세요.
5. 정상 종료, SCF 수렴, 기하 수렴, 최소점/TS 분류는 서로 다른 상태입니다.

관련 버튼: 파일 열기, Open files, 파일 열기 또는 데모

## MO / HOMO / LUMO 분석

HOMO·LUMO를 선택하고 에너지·점유수·gap을 확인합니다. 표면은 chk/fchk의 MO 계수와 cubegen이 필요합니다.

Spin: alpha/beta를 구분합니다. 제한 오비탈의 점유수는 0/1/2, 분리 spin 채널은 0/1입니다.
HOMO 선택 / LUMO 선택: 번호 입력과 diagram을 해당 오비탈로 이동합니다.
MO 표: 행을 누르면 번호와 에너지를 선택합니다. 번호는 1부터 시작합니다.
선택 MO ±표면: cubegen으로 해당 MO cube를 생성하고 양/음 위상을 함께 표시합니다. 두 색은 위상이며 양/음 전하가 아닙니다.
등치값은 |ψ|의 표시 수준입니다. 값이 작을수록 표면이 커지며, 서로 다른 MO를 비교할 때 같은 값을 사용하세요.
HOMO–LUMO gap은 orbital energy 차이입니다. 광학 excitation energy나 고분자 band gap으로 자동 해석하지 않습니다.
log만 있으면 출력된 MO 에너지와 점유를 확인할 수 있습니다. 파동함수 계수가 없으면 표면을 생성하지 않습니다.

관련 버튼: HOMO 선택, LUMO 선택, HOMO, Selected MO +/-, 선택 MO ±표면, LUMO, 선택 MO ±표면, Render MO +/-, MO energy diagram, cubegen, Gaussian cubegen으로 생성, MO·표면, MO / Fields

## Frequency · 허수 진동수 · 애니메이션

모드 행을 선택하면 해당 진동을 재생합니다. 음의 주파수는 허수 모드이며 의도한 TS인지 추가 확인이 필요합니다.

진동수의 단위는 cm-1입니다. 음수는 imaginary frequency를 뜻하며 빨간색으로 표시합니다. 작은 음수를 임의로 삭제하지 않습니다.
Imaginary만: 음의 진동수만 필터합니다. 미계산은 imaginary 0개와 다릅니다.
모드 행 선택 / 재생: 해당 모드가 계산된 기준 구조에서 진동을 재생합니다. 다른 최적화 frame에 모드를 임의로 붙이지 않습니다.
진폭: 화면에서의 변위 크기입니다. 실제 열진동 진폭이 아닙니다. 재생 속도도 실제 물리적 진동 주기와 다릅니다.
정지: 재생을 멈춥니다. 평형 구조: 원래 기준 좌표로 돌아갑니다.
변위 벡터: 모드의 움직임 방향을 표시합니다. ±변위 XYZ는 새 Gaussian 입력 구조를 만드는 데 쓸 수 있습니다.
완전 Hessian의 비선형 자유 분자는 통상 3N-6개 모드지만, 선형·고정·부분 Hessian은 다릅니다. 1개의 허수 모드는 TS 후보이며 양방향 IRC 연결을 확인해야 합니다.

관련 버튼: 진동·분광, Vibrations, 첫 imaginary mode 재생, Imaginary only, Imaginary만, 재생, 정지, Stop, 재생 중지, 진동, Play mode, 평형 구조, Equilibrium, 변위 벡터, Displacement vectors, 모드 +변위 XYZ, 모드 -변위 XYZ, ± XYZ, Mode XYZ

## 구조별 Total energy와 Force

선택 frame의 전자 에너지와 원자별 force를 표시합니다. force=-gradient이며 수렴 기준 force와 구분합니다.

Frame slider 또는 구조 표에서 frame을 선택하면 그 구조에 연결된 에너지와 force를 표시합니다.
Total energy: SCF/MP2/CC/ONIOM 등 종류와 함께 Hartree, eV로 표시합니다. 출력되지 않은 frame의 값을 앞뒤 값으로 채우지 않습니다.
원자별 Fx/Fy/Fz 및 |F|: Hartree/Bohr 또는 eV/Å를 선택합니다. 1 Eh/Bohr ≈ 51.4221 eV/Å입니다. fchk Cartesian Gradient는 부호를 반전해 force로 변환합니다.
Max component/RMS component는 Cartesian 성분으로 계산한 값입니다. Gaussian의 내부좌표 최적화 수렴 표와 같은 값이라고 가정하지 않습니다.
log의 input orientation과 standard orientation이 다르면 강체 정렬로 Force를 구조 좌표계에 맞춥니다. 출처에 좌표계를 표시합니다.
Force 벡터는 보기 좋게 정규화한 화살표이며 실제 수치는 표에서 확인하세요. Force가 기록되지 않았으면 미출력으로 표시합니다.
.chk에는 일반적으로 현재 구조만 남습니다. 최적화 모든 step의 분석에는 중간 구조와 force를 출력한 .log가 필요합니다.

관련 버튼: 에너지·Force, Energy / Force, Energy / Force CSV, Plot energy path, Force 벡터, Force vectors, 에너지 경로 그리기, 현재 plot CSV 저장, Save plot CSV, 에너지·Force CSV

## Polarizability · 분극률

3×3 분극률 tensor, 등방 평균, 비등방성, 고유값과 출처를 표시합니다. 분극률과 유전율은 다릅니다.

평균 α = (αxx+αyy+αzz)/3입니다. 원본 a.u. 및 polarizability volume Å³로 표시하며 1 a.u. ≈ 0.148184711472 Å³입니다.
비등방성은 tensor의 대각·비대각 성분으로 계산합니다. tensor 성분은 좌표계에 따라 달라지지만 평균·고유값은 강체 회전에서 불변입니다.
출처 선택: log의 Exact/고정밀 archive/응답 tensor 또는 fchk 기록을 구분합니다. 주파수 W가 제공되면 a.u.와 static 여부를 표시합니다.
계산하지 않은 분극률은 0이 아닌 미계산으로 표시합니다. 필요하면 Gaussian Polar 또는 해당 response 계산을 수행하세요.
분자 α만으로 고분자의 1 GHz 복소 유전율·유전손실을 바로 구할 수 없습니다.

관련 버튼: 분극률, Polarizability, 분극률 CSV, Polar CSV, Polar source

## 로그·chk 연결

로그의 에너지·force·진동과 checkpoint의 MO를 한 계산 항목으로 연결합니다. 다른 구조·전하·spin은 거부합니다.

로그와 chk/fchk를 모두 엽니다. 로그 계산을 선택하고 연결 대상 checkpoint를 고른 뒤 연결합니다.
원자 순서·최종 구조·전하·다중도를 검사하고 구조가 다르면 거부합니다. 좌표계가 강체 회전으로 다른 경우 새 모델을 checkpoint 좌표계로 정렬해 표면을 맞춥니다.
최종 구조 일치만으로 method/basis/전자 상태까지 자동 증명되지는 않습니다. 같은 계산에서 생성한 파일인지 원본 입력도 확인하세요.
기존 항목을 덮어쓰지 않고 새 연결 항목을 만듭니다. chk 또는 log만 열어도 각 파일에 있는 정보는 사용할 수 있습니다.

관련 버튼: 로그·chk 연결, Link log + checkpoint

## Demo · 데모

프로그램 조작 확인용 합성 물 분자·진동·공간장을 엽니다. 실제 Gaussian 결과가 아닙니다.

파일 없이 회전·진동·스펙트럼·표면 동작을 연습하는 샘플입니다. 에너지·진동·공간장 값을 연구 결과로 사용하지 마세요. 실제 .log/.chk 분석에는 필요하지 않으며 원본 파일을 변경하지 않습니다.

관련 버튼: Demo, 데모, 데모 보기

## Reload source · 원본 다시 읽기

현재 항목의 원본 파일을 다시 분석합니다. Gaussian 계산을 다시 실행하는 버튼이 아닙니다.

실행 중인 Gaussian 로그에 내용이 더 기록되었거나 파일이 변경되었을 때 새 내용을 읽습니다. 새 분석 항목을 만들며 원본은 덮어쓰지 않습니다. chk 변환 항목은 원본 chk를 다시 변환합니다. 원본 경로가 없는 프로젝트 snapshot은 다시 원본을 열어야 합니다.

관련 버튼: Reload source, 원본 새로고침, 새로고침

## Save project · 분석 세션 저장

읽은 계산 수치의 snapshot을 .glproj로 저장합니다. chk·cube 원본을 모두 포함하는 백업은 아닙니다.

나중에 분석 수치·구조를 다시 열기 위한 snapshot입니다. 안전을 위해 snapshot에 적힌 서버 경로를 자동 신뢰하지 않습니다. MO 표면을 다시 만들려면 원본 chk/fchk 또는 cube를 다시 열어야 합니다. 원본 로그·체크포인트도 별도로 보관하세요.

관련 버튼: Save project, 프로젝트 저장

## XYZ · 구조 좌표 내보내기

현재 선택 frame의 원소·좌표를 XYZ 파일로 저장합니다. 에너지·오비탈·진동 데이터는 포함하지 않습니다.

다른 분자 프로그램이나 새 계산 준비에 사용할 수 있습니다. 일반 XYZ에는 결합차수·basis·charge·spin이 보존되지 않으므로 Gaussian 입력을 만들 때 전하·다중도를 확인하세요. 진동 중 ±변위 구조는 별도의 모드 변위 XYZ 기능을 사용합니다.

관련 버튼: XYZ, XYZ 저장

## Report JSON · 분석 보고서

선택 계산의 분석 수치·출처·판정을 기계가 읽을 수 있는 JSON으로 내보냅니다.

에너지·진동·MO 에너지·물성·수렴 상태 등을 Python/Excel 후처리 또는 기록에 활용할 수 있습니다. 원본 파동함수와 MO cube를 대신하는 파일은 아닙니다. HTML 보고서는 같은 내용을 브라우저에서 읽기 위한 파일입니다.

관련 버튼: Report JSON, 보고서 JSON, 분석 JSON 저장, HTML 보고서

## 스펙트럼·배율·선폭

원시 주파수·강도로 스펙트럼을 그립니다. FWHM은 peak 선폭이며 값의 단위는 스펙트럼 종류에 따라 다릅니다.

IR/Raman/VCD는 cm-1, UV-Vis/ECD는 eV, NMR은 ppm 축을 사용합니다. 주파수 배율은 표시용이며 원시 값을 수정하지 않습니다. Raman에는 레이저 파장·온도가 필요하고, NMR에는 기준 shielding을 입력합니다. CSV는 곡선의 숫자, SVG는 그래프 이미지입니다.

관련 버튼: 스펙트럼 그리기, Plot, CSV, SVG, 스펙트럼 CSV

## 구조 뷰어·Frame·재생

드래그로 회전, 휠로 확대, 원자 클릭으로 측정합니다. Frame은 구조 최적화·경로의 한 구조입니다.

중심은 화면 배향을 맞추고 원자 좌표를 변경하지 않습니다. 번호/H는 원자 라벨과 수소 표시입니다. 2/3/4개 원자를 선택하면 거리/각도/이면각을 표시합니다. 경로 재생은 저장된 구조의 순서를 보여주며 실제 시간의 MD 궤적이라고 자동 해석하지 않습니다. PNG는 현재 구조 화면을 저장합니다.

관련 버튼: 중심, Center, 번호, Labels, H, 선택 해제, Clear selection, ▶ 경로, Play path, PNG

## Cube · 등치면·위상

cube 공간장으로 ±표면을 표시합니다. MO의 부호는 위상이며 density·ESP의 단위와 다릅니다.

양/음 등치면과 투명도·등치값을 조절합니다. 표면 숨기기는 원본 cube를 삭제하지 않습니다. Field 채널은 multi-orbital cube 안의 데이터 선택으로 0부터 시작합니다. 적분을 전자수로 해석하려면 밀도 종류·단위를 확인해야 합니다.

관련 버튼: + 표면, − 표면, + Surface, - Surface, 숨기기, Hide, 표면 숨기기, cube 정보·적분

## 도구·고급 분석·설정

외부 도구 경로·원본 출력·고급 JSON 분석과 표시 설정을 확인합니다. 없는 데이터는 생성된 것처럼 표시하지 않습니다.

분석 실행은 docs/API.md의 공통 엔진 요청을 실행합니다. 임의 shell 명령 입력 기능이 아닙니다. 원본 출력은 연결된 파일의 지정 행을 읽습니다. 동위원소 재분석에는 완전 Hessian과 모든 원자의 질량이 필요합니다. 저주파 보정·정렬·반응 에너지는 계산 조건과 가정을 확인하세요. 표시 설정의 폰트·크기·색은 결과 수치와 별개입니다. 작업 취소는 분석/utility 작업을 취소하며 Gaussian 원본 결과를 삭제하지 않습니다.

관련 버튼: 도구, Tools, 실행, Run, 분석 실행, 원본 출력, Source output, 원문 구간 보기, 원본 출력 첫 500행, 설정, 표시 설정, Display settings, 적용, Apply, Cancel task, 작업 취소, 동위원소 Hessian 재분석, Hessian 동위원소 재분석, 별도 보정 결과, 전체 계산 조건 비교, RMSD 정렬 검사, 지원 범위, Feature status

## 구조 편집·입력 작성

편집은 새 구조를 만듭니다. 예전 에너지·MO·진동을 편집 구조의 계산값으로 이어 붙이지 않습니다.

SMILES는 RDKit으로 conformer를 만들며 Gaussian 최적화 결과가 아닙니다. 선택 원자 삭제·이동 후 새 계산을 수행해야 합니다. 입력 저장에서 method/basis, charge/multiplicity, 추가 basis/ECP 조건을 확인하세요. 다른 방법의 구조에 frequency 결과를 임의로 연결하지 마세요.

관련 버튼: 3D conformer 생성, SMILES → conformer (RDKit), SMILES to conformers (RDKit), Gaussian 입력 저장, Save Gaussian input, 선택 원자 삭제 → 새 구조, Delete selected / new model, 선택 원자 이동 → 새 구조

## 도움말·검색

기능별 설명을 검색합니다. 마우스를 버튼 위에 두면 짧은 설명이 나타나며 F1으로 이 도움말을 엽니다.

버튼 이름, HOMO/LUMO, force, frequency, polarizability 또는 파일 확장자로 검색하세요. 기획서의 구현 상태표는 기능 지원 범위를 보여주며, 이 도움말은 실제 조작 방법과 해석 기준을 설명합니다.

관련 버튼: 도움말, Help, 도움말 크게 보기, Open help window, 닫기, Close

## 모든 버튼 기능 찾아보기

화면의 각 버튼이 수행하는 동작과 저장 내용을 확인합니다.

표시 설정 / Display settings / 설정 / Settings / 화면 설정
언어·테마·글꼴과 분자 배경, 원소색, 원자/결합 크기를 조절하고 저장합니다. 계산 좌표와 분석값은 바뀌지 않습니다.

Gaussian 입력 설정… / Gaussian input settings… / Gaussian 입력 생성 / Build Gaussian input
Gaussian 계산 종류·method/basis·전하/spin·Link 0·추가 입력을 구성하는 창을 엽니다. SMILES로 만든 구조도 사용할 수 있습니다.

입력 생성 / 갱신 / Generate / refresh input / Generate / update input
선택 frame과 입력한 조건을 검사해 .gjf 미리보기를 갱신합니다. Gaussian 계산은 실행하지 않습니다.

.gjf 다운로드 / Download .gjf / .gjf / .com 저장 / Save .gjf / .com
현재 설정으로 입력을 다시 생성하고 .gjf 파일로 저장합니다. Gen/ECP 블록은 직접 확인하세요.

이동 / Go
입력하거나 붙여넣은 폴더 경로로 이동합니다. 웹에서는 --root 범위 안의 경로만 사용할 수 있습니다.

상위 폴더 / ↑ Parent folder / .. ↑
현재 폴더의 바로 위 폴더로 이동합니다. 웹 루트에서는 더 올라가지 않습니다.

간편 설정 / Quick settings / 커스텀 설정 / Custom settings / 입력 미리보기 / Input preview
Gaussian 입력의 기본 조건, 고급 Route/추가 입력, 생성된 입력 미리보기 사이를 전환합니다.

파일 열기 / Open files
log/chk/fchk/cube 또는 저장한 프로젝트를 엽니다. 웹에서는 PC 파일을 업로드합니다.

서버 폴더
--root 안의 서버 파일을 열며 대형 결과를 PC로 옮길 필요가 없습니다.

상위 폴더
서버 파일 목록에서 한 단계 위 폴더로 이동합니다.

Demo / 데모
조작 연습용 합성 물 분자·모드·공간장을 엽니다. 실제 Gaussian 결과가 아닙니다.

Reload source / 원본 새로고침 / 새로고침
선택 항목의 원본을 다시 분석합니다. chk는 원본 chk에서 다시 변환하며 Gaussian 계산을 다시 실행하지 않습니다.

Save project / 프로젝트 저장
계산 수치·구조 snapshot을 .glproj로 저장합니다. 원본 chk/cube는 별도 보관해야 합니다.

XYZ / XYZ 저장
현재 frame의 원소·좌표를 XYZ로 저장합니다. MO·진동·에너지는 포함하지 않습니다.

Report JSON / 보고서 JSON / 분석 JSON 저장
선택 계산의 구조·에너지·MO 에너지·진동·물성·판정을 JSON으로 내보냅니다.

JSON 저장
현재 결과 창에 표시된 분석 값을 JSON 파일로 저장합니다.

HTML 보고서
선택 계산의 분석 snapshot을 브라우저에서 읽는 HTML 보고서로 저장합니다.

설정 / 표시 설정 / Display settings
글꼴·글자 크기 등의 화면 설정을 엽니다. 계산 수치는 바뀌지 않습니다.

적용 / Apply
설정 창의 글꼴·크기·화면 설정을 적용합니다.

도움말 / Help
검색 가능한 내장 매뉴얼과 버튼별 사용법을 엽니다. F1으로도 열 수 있습니다.

닫기 / Close
현재 보고서·설정 창을 닫습니다.

작업 취소 / Cancel task
추적 중인 분석 또는 Gaussian utility 작업을 취소합니다. 원본 파일은 보존합니다.

중심 / Center
구조를 화면에 맞춥니다. 저장된 원자 좌표는 변경하지 않습니다.

번호 / Labels
구조 뷰어에 원자 번호·원소 라벨을 표시하거나 숨깁니다.

H
구조 뷰어의 수소 원자를 표시하거나 숨깁니다.

선택 해제 / Clear selection
선택한 원자를 해제하고 거리·각도 측정 표시를 초기화합니다.

PNG
현재 분자 뷰어 화면을 PNG 이미지로 저장합니다.

▶ 경로 / Play path
저장된 구조 frame을 순서대로 재생합니다. 실제 MD 시간축을 뜻하지는 않습니다.

정지 / Stop / 재생 중지
현재 구조 경로 또는 진동 애니메이션을 멈춥니다. 평형 구조로 복원하려면 평형 구조를 누르세요.

HOMO / HOMO 선택
선택 spin 채널의 가장 높은 점유 MO를 선택합니다. 표와 diagram, MO 번호를 함께 갱신합니다.

LUMO / LUMO 선택
선택 spin 채널의 첫 비점유 frontier MO를 선택합니다.

선택 MO ±표면 / Selected MO +/- / Render MO +/-
선택 MO를 cubegen으로 생성하고 양·음 위상 표면을 함께 표시합니다. MO 계수가 있는 chk/fchk가 필요합니다.

+ 표면 / + Surface
선택 cube에서 양의 등치값 표면을 추가합니다. 등치값은 입력 칸의 절댓값을 사용합니다.

− 표면 / - Surface
선택 cube에서 음의 등치값 표면을 추가합니다. MO에서는 음의 위상을 뜻합니다.

숨기기 / Hide / 표면 숨기기
현재 표시한 표면·벡터를 화면에서 제거합니다. 원본 cube는 삭제하지 않습니다.

cubegen / Gaussian cubegen으로 생성
선택한 SCF density/ESP/spin 또는 MO cube를 Gaussian cubegen으로 생성해 새 공간장 항목으로 엽니다.

cube 정보·적분
선택 cube의 격자·수치 범위와 선택 채널의 공간 적분을 확인합니다. 단위·밀도 종류를 확인해야 합니다.

로그·chk 연결 / Link log + checkpoint
원자 순서·최종 구조·전하·spin을 검사해 로그와 checkpoint를 새 항목으로 연결합니다.

Imaginary만 / Imaginary only
음의 진동수만 표시합니다. 작은 음수도 임의로 삭제하지 않습니다.

재생 / Play mode
선택 모드를 해당 기준 구조에서 재생합니다. 진폭·속도는 시각화 설정입니다.

첫 imaginary mode 재생
첫 음의 진동수 모드를 재생해 TS 반응 방향을 확인합니다.

평형 구조 / Equilibrium
애니메이션을 멈추고 선택 모드의 기준 구조를 복원합니다.

변위 벡터 / Displacement vectors
선택 모드의 원자별 변위 방향을 화살표로 표시합니다. 길이는 보기용으로 정규화합니다.

± XYZ / Mode XYZ / 모드 +변위 XYZ / 모드 -변위 XYZ
선택 모드의 기준 좌표에 지정 진폭의 변위를 더하거나 빼서 XYZ로 저장합니다.

Plot / 스펙트럼 그리기
선택 종류의 원시 sticks를 배율·FWHM으로 broaden해 그래프를 그립니다. 원시 값은 유지합니다.

CSV / 현재 plot CSV 저장 / Save plot CSV
현재 그래프의 x/y 수치를 CSV로 저장합니다.

SVG
현재 그래프의 곡선을 확대 가능한 SVG 이미지로 저장합니다.

Force 벡터 / Force vectors
선택 frame의 Cartesian force 방향을 보기용 길이로 정규화해 표시합니다.

에너지·Force CSV / Energy / Force CSV
모든 frame의 에너지와 원자별 force를 원본 단위 Eh, Eh/Bohr의 CSV로 저장합니다.

에너지 경로 그리기 / Plot energy path
frame 번호를 x축, 해당 구조의 전자 에너지를 y축으로 그립니다.

분극률 CSV / Polar CSV
선택 출처·응답 주파수의 tensor와 평균·비등방성을 CSV로 저장합니다.

전체 계산 조건 비교
열린 계산의 조성·전하·spin·route·에너지 종류를 비교합니다. 조건이 다르면 상대 에너지 순위를 만들지 않습니다.

별도 보정 결과
원래 온도에서 저주파 엔트로피·표준 농도 보정을 별도로 계산합니다. 원본 RRHO 값은 유지합니다.

RMSD 정렬 검사
동일 원자 순서의 두 구조를 강체 정렬해 RMSD를 확인합니다.

3D conformer 생성 / SMILES → conformer (RDKit) / SMILES to conformers (RDKit)
SMILES로부터 RDKit conformer를 만듭니다. Gaussian 최적화 결과와 구분하세요.

Gaussian 입력 저장 / Save Gaussian input
현재 구조와 route·전하·다중도·추가 입력을 .gjf로 저장합니다.

선택 원자 삭제 → 새 구조 / Delete selected / new model
선택 원자를 삭제한 새 구조를 만듭니다. 이전 에너지·MO·진동은 승계하지 않습니다.

선택 원자 이동 → 새 구조
선택 원자를 입력 벡터만큼 이동한 새 구조를 만듭니다.

원본 출력 / Source output / 원본 출력 첫 500행
선택 계산의 원본 파일 첫 500행을 읽습니다. snapshot만 있으면 원본을 다시 여세요.

원문 구간 보기
시작 행·행 수로 지정한 원본 출력 구간을 확인합니다.

Hessian 동위원소 재분석
완전 fchk Hessian과 지정한 모든 원자 질량으로 진동수·변위를 다시 계산합니다. 기존 IR/Raman 강도를 재사용하지 않습니다.

실행 / Run / 분석 실행
입력한 JSON 공통 분석 요청을 실행합니다. 요청 형식은 docs/API.md를 확인하세요.

지원 범위 / Feature status
기획서의 140개 기능에 대한 구현 상태·입력 요건을 표시합니다.

관련 버튼: 표시 설정, Display settings, 설정, Settings, 화면 설정, Gaussian 입력 설정…, Gaussian input settings…, Gaussian 입력 생성, Build Gaussian input, 입력 생성 / 갱신, Generate / refresh input, Generate / update input, .gjf 다운로드, Download .gjf, .gjf / .com 저장, Save .gjf / .com, 이동, Go, 상위 폴더, ↑ Parent folder, .. ↑, 간편 설정, Quick settings, 커스텀 설정, Custom settings, 입력 미리보기, Input preview, 파일 열기, Open files, 서버 폴더, 상위 폴더, Demo, 데모, Reload source, 원본 새로고침, 새로고침, Save project, 프로젝트 저장, XYZ, XYZ 저장, Report JSON, 보고서 JSON, 분석 JSON 저장, JSON 저장, HTML 보고서, 설정, 표시 설정, Display settings, 적용, Apply, 도움말, Help, 닫기, Close, 작업 취소, Cancel task, 중심, Center, 번호, Labels, H, 선택 해제, Clear selection, PNG, ▶ 경로, Play path, 정지, Stop, 재생 중지, HOMO, HOMO 선택, LUMO, LUMO 선택, 선택 MO ±표면, Selected MO +/-, Render MO +/-, + 표면, + Surface, − 표면, - Surface, 숨기기, Hide, 표면 숨기기, cubegen, Gaussian cubegen으로 생성, cube 정보·적분, 로그·chk 연결, Link log + checkpoint, Imaginary만, Imaginary only, 재생, Play mode, 첫 imaginary mode 재생, 평형 구조, Equilibrium, 변위 벡터, Displacement vectors, ± XYZ, Mode XYZ, 모드 +변위 XYZ, 모드 -변위 XYZ, Plot, 스펙트럼 그리기, CSV, 현재 plot CSV 저장, Save plot CSV, SVG, Force 벡터, Force vectors, 에너지·Force CSV, Energy / Force CSV, 에너지 경로 그리기, Plot energy path, 분극률 CSV, Polar CSV, 전체 계산 조건 비교, 별도 보정 결과, RMSD 정렬 검사, 3D conformer 생성, SMILES → conformer (RDKit), SMILES to conformers (RDKit), Gaussian 입력 저장, Save Gaussian input, 선택 원자 삭제 → 새 구조, Delete selected / new model, 선택 원자 이동 → 새 구조, 원본 출력, Source output, 원본 출력 첫 500행, 원문 구간 보기, Hessian 동위원소 재분석, 실행, Run, 분석 실행, 지원 범위, Feature status
