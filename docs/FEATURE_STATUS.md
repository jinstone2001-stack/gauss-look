# 기능 구현 상태 · GaussLook 1.0

기획서의 140개 구현 단위입니다. 같은 항목에 여러 조작이나 출력 형식이 포함된 경우 일부만 구현되어 있으면 부분·조건부로 표시합니다. 각 기능의 입력·외부 도구 요건은 README와 docs/API.md를 확인하세요. 모든 GaussView 기능의 완전한 대체 버전이라는 의미가 아닙니다.

| ID | 기능 | 상태 |
|---|---|---|
| I01 | Gaussian 입력 읽기 | 부분·조건부 |
| I02 | 로그·출력 읽기 | 지원 |
| I03 | 바이너리 checkpoint 열기 | 지원 |
| I04 | formatted checkpoint 열기 | 지원 |
| I05 | cube 열기 | 지원 |
| I06 | Gaussian frequency 파일 열기 | 후속 구현 |
| I07 | PDB·AMBER PDB 읽기 | 부분·조건부 |
| I08 | MOL·SDF·RXN 읽기 | 부분·조건부 |
| I09 | MOL2/ML2 읽기 | 부분·조건부 |
| I10 | CIF 읽기 | 부분·조건부 |
| I11 | GMMX·AMPAC 계열 파일 | 후속 구현 |
| I12 | 여러 작업 중 선택해 열기 | 지원 |
| I13 | 중간 구조·결합 읽기 옵션 | 부분·조건부 |
| I14 | 분자 그룹·연관 파일·새로고침 | 부분·조건부 |
| I15 | 저장·일괄 형식 변환 | 부분·조건부 |
| V01 | 회전·이동·확대, 정밀 배향 | 지원 |
| V02 | wire/tube/ball-and-stick/CPK | 부분·조건부 |
| V03 | 원소·번호·값 라벨 | 부분·조건부 |
| V04 | 수소·dummy·결합 표시 제어 | 부분·조건부 |
| V05 | 거리·각·이면각 조회 | 지원 |
| V06 | 여러 독립 view | 부분·조건부 |
| V07 | molecule group multiview·동기화 | 부분·조건부 |
| V08 | 클릭·박스·brush 선택 | 부분·조건부 |
| V09 | 조건·거리·연결성 기반 선택 | 부분·조건부 |
| V10 | PDB 잔기·chain·secondary structure 선택 | 후속 구현 |
| V11 | 이름 있는 원자 그룹·선택 유지 | 부분·조건부 |
| V12 | 입체화학 R/S 표시 | 후속 구현 |
| V13 | fog·배경·축·원근·클리핑·품질 | 부분·조건부 |
| V14 | 강조·숨기기·중심맞춤·표시 색상 | 부분·조건부 |
| B01 | 원자·원소 템플릿 배치 | 후속 구현 |
| B02 | ring·functional-group 라이브러리 | 후속 구현 |
| B03 | 아미노산·nucleoside 템플릿 | 후속 구현 |
| B04 | 사용자 fragment 라이브러리 | 후속 구현 |
| B05 | fragment 결합·배치 방식 | 후속 구현 |
| B06 | fragment를 선택 원자 centroid에 배치 | 후속 구현 |
| B07 | 수소·valence 추가·삭제 | 부분·조건부 |
| B08 | 결합차수·길이 편집·SmartSlide | 후속 구현 |
| B09 | 결합각 편집·SmartSlide | 후속 구현 |
| B10 | 이면각·Newman projection 편집 | 후속 구현 |
| B11 | 분자 전체 mirror invert | 후속 구현 |
| B12 | 선택 원자 중심 반전 | 후속 구현 |
| B13 | Clean 구조 정리 | 후속 구현 |
| B14 | Rebond·weak bond 제거·사용자 길이 | 부분·조건부 |
| B15 | 점군 판정·대칭 증가/감소·제약 | 후속 구현 |
| B16 | 원자표·Cartesian/Z-matrix 편집 | 부분·조건부 |
| B17 | Z-matrix 표준화·구조 재배향 | 후속 구현 |
| B18 | 동위원소·여러 isotopologue 정의 | 부분·조건부 |
| B19 | MM atom type·전하·ONIOM layer 편집 | 후속 구현 |
| B20 | PDB 잔기·chain·구조 메타데이터 편집 | 후속 구현 |
| B21 | Redundant Coordinate Editor | 후속 구현 |
| B22 | Connection Editor·QST 원자 대응 | 후속 구현 |
| B23 | PBC Crystal Editor | 부분·조건부 |
| J01 | 작업 유형 선택 | 부분·조건부 |
| J02 | method·basis·R/U/RO·전하·다중도 | 부분·조건부 |
| J03 | 바닥/여기 상태·분산 설정 | 부분·조건부 |
| J04 | Title·Link 0 설정 | 부분·조건부 |
| J05 | 일반 계산 옵션 | 부분·조건부 |
| J06 | checkpoint 데이터 재사용 | 부분·조건부 |
| J07 | 초기 guess·mix·localize·fragment | 후속 구현 |
| J08 | population·전하·density 옵션 | 부분·조건부 |
| J09 | NBO/NPA·NLMO/NTO 저장 옵션 | 후속 구현 |
| J10 | SCRF 용매·모델·추가 입력 | 부분·조건부 |
| J11 | PBC 계산 옵션 | 후속 구현 |
| J12 | 자유 키워드·추가 절·preview | 부분·조건부 |
| J13 | QST2/QST3 TS 설정 | 후속 구현 |
| J14 | ONIOM 다층 설정 | 후속 구현 |
| J15 | CASSCF active space·MO 순열 | 후속 구현 |
| J16 | freeze·부분 모드·rigid/relaxed scan | 부분·조건부 |
| J17 | NMR spin-spin coupling 설정 | 부분·조건부 |
| J18 | fragment guess·counterpoise 설정 | 부분·조건부 |
| J19 | 이름 있는 calculation scheme | 부분·조건부 |
| J20 | 분자 그룹 일괄 입력·실행 | 부분·조건부 |
| J21 | 로컬 제출·Quick Launch | 후속 구현 |
| J22 | Current Jobs·utility 작업 제어 | 부분·조건부 |
| J23 | SC Job Manager 형태의 로컬 큐 | 후속 구현 |
| J24 | 원격 script 실행·로그 stream | 후속 구현 |
| R01 | 계산 개요·조건·구조 정보 | 지원 |
| R02 | total energy 표시 | 지원 |
| R03 | 쌍극자 크기·벡터 | 지원 |
| R04 | 분극률 등 분자 물성 요약 | 지원 |
| R05 | 최적화 수렴 요약 | 지원 |
| R06 | Thermo 요약 | 지원 |
| R07 | imaginary frequency 수 표시 | 지원 |
| R08 | Molecule Group Table | 지원 |
| R09 | 원자 물성·전하의 숫자/색 표시 | 지원 |
| R10 | 결합 길이·bond order의 숫자/색 표시 | 부분·조건부 |
| T01 | Optimization 에너지·gradient plot | 지원 |
| T02 | IRC plot·구조 보기 | 부분·조건부 |
| T03 | 1변수 PES scan | 부분·조건부 |
| T04 | 2변수 scan 3D surface | 부분·조건부 |
| T05 | BOMD·ADMP·trajectory plot | 부분·조건부 |
| T06 | conformer energy plot | 부분·조건부 |
| T07 | 구조 연속 재생·속성 추가 plot | 지원 |
| O01 | MO 에너지·점유 diagram | 부분·조건부 |
| O02 | 특정 MO·여러 MO 등치면 | 지원 |
| O03 | alpha/beta 오비탈 구별 | 지원 |
| O04 | MO 점유·charge/spin·순열 편집 | 후속 구현 |
| O05 | 기존 MO 불러오기·guess-only 생성 | 후속 구현 |
| O06 | 저장된 NBO·NLMO·NTO 등 보기 | 부분·조건부 |
| O07 | total/alpha/beta electron density | 지원 |
| O08 | electrostatic potential | 지원 |
| O09 | spin density | 지원 |
| O10 | NMR shielding·자기 관련 공간장 | 부분·조건부 |
| O11 | cube 생성·load/save/remove·격자 | 지원 |
| O12 | cube scale/square/add/subtract | 지원 |
| O13 | solid/transparent/mesh·±surface | 지원 |
| O14 | 다른 물성으로 surface 색칠 | 부분·조건부 |
| O15 | 2D contour·평면 정의·이동 | 부분·조건부 |
| O16 | PCM solvation cavity | 후속 구현 |
| S01 | 진동수·모드 선택·애니메이션 | 지원 |
| S02 | 변위·dipole derivative 벡터 | 부분·조건부 |
| S03 | 모드 방향 수동 변위·구조 저장 | 지원 |
| S04 | 주파수 scale factor | 지원 |
| S05 | IR 스펙트럼 | 지원 |
| S06 | Raman 스펙트럼 | 지원 |
| S07 | VCD 스펙트럼 | 부분·조건부 |
| S08 | ROA 스펙트럼 | 후속 구현 |
| S09 | 주파수 의존 결과 선택 | 부분·조건부 |
| S10 | isotope 치환 후 모드·스펙트럼 비교 | 부분·조건부 |
| S11 | FreqChk·모드 선택/저장 | 부분·조건부 |
| S12 | 비조화·overtone·combination 표시 | 후속 구현 |
| S13 | NMR shielding·기준물질 chemical shift | 부분·조건부 |
| S14 | UV-Vis 스펙트럼·전이 | 지원 |
| S15 | ECD 스펙트럼 | 지원 |
| S16 | ORD plot | 후속 구현 |
| S17 | Vibronic OPA·Duschinsky·전이표 | 후속 구현 |
| S18 | Mixture Editor·conformer 평균 | 부분·조건부 |
| S19 | plot 겹치기·축·선·피크·라벨 편집 | 부분·조건부 |
| P01 | plot·스펙트럼 수치 데이터 내보내기 | 지원 |
| P02 | 구조·plot 이미지 저장 | 부분·조건부 |
| P03 | 임의 크기·해상도·그룹 이미지 | 부분·조건부 |
| P04 | 진동·구조 movie와 frame 저장 | 부분·조건부 |
| P05 | 인쇄·clipboard image capture | 부분·조건부 |
| P06 | 폰트·색·크기·창·디렉터리 설정 | 부분·조건부 |
| P07 | toolbar 구성·빠른 실행 배치 | 후속 구현 |
| P08 | 그림·movie·진동·결합·clean 기본값 | 부분·조건부 |
| P09 | 창·view·그룹 관리 | 부분·조건부 |
| P10 | 도움말·문맥 도움·tips·버전 정보 | 지원 |
| A01 | GMMX conformer search 연동 | 후속 구현 |
| A02 | AMPAC interface 연동 | 후속 구현 |
