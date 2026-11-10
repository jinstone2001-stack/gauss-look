# 추가 제안의 구현 상태

| 기획 ID | 제안 | 1.0 상태 |
|---|---|---|
| N01 | 계산 품질 대시보드 | 종료·SCF·최적화·imaginary·spin 점검 구현. 미계산 안정성은 미확인으로 표시 |
| N02 | 필요 데이터 안내·파일 불일치 | capability 안내 구현. log/fchk 자동 대응·통합 매칭은 후속 |
| N03 | TS 작업공간 | TS 후보·모드·±변위·경로 선택 제공. 양방향 IRC endpoint 자동 연결은 후속 |
| N04 | 반응 자유에너지·저주파 보정 | 화학양론 에너지, entropy-only Truhlar/Grimme·농도 보정 API. 복합 SP 자동 매칭은 후속 |
| N05 | 배치 조건 일치 | 조성·전하·다중도·route·에너지 종류 일치 시만 상대 에너지 표시 |
| N06 | 오비탈 연속 추적 | 후속 구현 |
| N07 | NTO·CT 정량 패널 | 기존 저장 MO/cube 보기만 제공. transition-density SVD·CT 지표는 후속 |
| N08 | density difference 검증 | 동일 구조·격자 검사·뺄셈·조건부 적분 제공. fragment 계산 조건 마법사는 후속 |
| N09 | 모드 성격/PED | 후속 구현 |
| N10 | 실험 스펙트럼 fitting | 후속 구현 |
| N11 | J-coupling multiplet | coupling tensor 읽기 일부 보완. multiplet simulation은 후속 |
| N12 | 재현 가능한 세션 | 원본 해시·원문 행·snapshot 구현. 표시 설정 전체 복원·완전 archive는 후속 |
| N13 | 실행 중·병목·오류 도우미 | 원본 재읽기·utility 비동기/실패/취소 제공. 지속 tail·병목 자동 진단은 후속 |
| N14 | 금속·ECP·ONIOM | 일반 구조·전하/spin 보기에서 Sn 등 지원. ECP/층 전용 해석은 후속 |
| N15 | 재료 설계 export | 분극률 tensor/평균/Å³ 변환·JSON 제공. 별도 ML 데이터베이스 export는 후속 |
| N16 | 보관 패키지 | 계산 snapshot 및 export 구현. 원본·공간장 전체를 담는 archive는 후속 |

기획 문서는 목표 범위를, 이 문서는 실제 배포 범위를 나타냅니다. 필요한 데이터나 외부 프로그램이 없으면 결과를 만들어내지 않습니다.
