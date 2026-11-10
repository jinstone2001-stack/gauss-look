# 공통 분석 API

1.1의 주요 UI는 아래 기능을 직접 제공합니다. 같은 수치를 API에서도 사용할 수 있습니다.

```json
{"action":"frame_analysis","frame":0}
```

선택 frame의 에너지 종류·Hartree/eV와 원자별 Force·max/RMS·출처를 반환합니다. `force=null`은 미출력이며 0이 아닙니다. checkpoint Gradient는 −부호로 Force로 변환합니다.

```json
{"action":"orbital_analysis"}
```

spin별 MO 번호(1부터), 에너지·점유·HOMO/LUMO·gap을 반환합니다. 분리 spin 채널과 공간 오비탈을 구분합니다.

```json
{"action":"orbital_surface","spin":"alpha","orbital":25,"grid":"coarse","level":0.03}
```

task 완료 시 `meshes`의 ±위상 표면을 반환합니다. 원래 계산 선택을 유지하며 cube는 소스 파일·수정 시각·MO·spin·격자가 같은 경우 재사용합니다. 실제로 연 chk/fchk의 MO 계수와 cubegen이 필요합니다. 프로젝트에 기록된 임의 경로를 실행 근거로 사용하지 않습니다.

```json
{"action":"link_checkpoint","checkpoint_id":"열린_checkpoint_ID"}
```

현재 로그와 선택 checkpoint의 원자 순서·전하·다중도·강체 정렬 최종 구조(RMSD≤0.002 Å)를 검사해 새 연결 항목을 만듭니다. MO 표면 좌표계에 맞춰 로그 구조·변위·Force를 회전합니다. method/basis/전자 상태 확인은 원본 입력과 함께 수행하세요.

```json
{"action":"reload_source"}
```

원본을 다시 읽고 새 항목을 만듭니다. chk는 원본 chk에서 재변환합니다. snapshot만 연 경우 원본을 다시 열어야 합니다.

`GET /api/calculation/ID`에는 `orbital_analysis`, `polarizability_analysis`, `final_frame_analysis`가 포함됩니다. `GET /api/help`는 내장 매뉴얼과 개별 버튼 설명을 반환합니다. `reference_frame`은 모드의 진동 기준 구조 인덱스입니다.

웹 `도구 → 고급 공통 분석 API`, 또는 X11 `도구`의 JSON 입력 창에서 실행합니다. `id`를 생략하면 현재 계산을 사용합니다. ID는 분석 JSON이나 `/api/state`에서 확인할 수 있습니다. 인덱스는 원자/frame/mode/field 채널의 경우 **0부터**, cubegen의 **MO 번호만 1부터**입니다. 이 엔진은 임의 shell 명령을 실행하는 기능을 제공하지 않습니다.

```json
{"action":"compare"}
```

```json
{"action":"spectrum","kind":"Raman","width":12,"scale":0.98,"laser_nm":532,"temperature":298.15}
```

```json
{"action":"thermo","cutoff":100,"model":"grimme","concentration":1.0}
```

열화학은 **원본 출력 온도에서의 entropy-only 보정**입니다. enthalpy를 재계산하지 않으며 원래 Gaussian 값은 바뀌지 않습니다. `truhlar`와 `grimme`를 구별합니다. 실제 hindered rotor 해석을 대체하지 않습니다.

```json
{"action":"generate_cube","kind":"mo","spin":"alpha","orbital":25,"grid":"coarse"}
```

현재 계산이 fchk여야 합니다. 반환한 task를 UI가 추적합니다. `kind`는 mo/density/potential/spin, grid는 coarse/medium/fine입니다. 새 공간장은 별도 항목으로 열립니다.

```json
{"action":"field_info","field_id":"열린_field_ID"}
```

```json
{"action":"mesh","field_id":"표면_field_ID","level":0.03,"channel":0,"mapped_field":"색칠할_field_ID"}
```

vertices/faces/normals 및 mapped_values를 반환합니다. mapped_values는 두 번째 장을 표면 점에서 보간한 값입니다. 기본 GUI 표면 버튼의 색은 ±단색이며, 반환한 mapping 배열을 자동으로 색칠하는 전용 조작 화면은 후속 구현입니다. 좌표·격자 범위 밖 값은 null로 표시합니다.

```json
{"action":"contour","field_id":"열린_field_ID","origin":[0,0,0],"normal":[0,0,1],"size":8,"resolution":120}
```

원점·길이 단위는 Å입니다. 단면의 2D 값 배열과 축/방향을 JSON으로 반환합니다. 전용 2D contour plot UI는 후속 구현입니다.

```json
{"action":"field_operation","field_id":"A_ID","other_id":"B_ID","operation":"subtract"}
```

원자·좌표·격자·field 수가 같아야 하며 자동 보간하지 않습니다. scale/square는 other_id가 필요 없고 scale에는 factor를 지정합니다.

```json
{"action":"integrate","field_id":"A_ID","channel":0}
```

cube는 scalar의 물리적 종류·단위를 스스로 증명하지 않습니다. 결과의 조건부 전자수는 실제 값이 e/bohr³ 밀도일 때만 해석하세요. ECP/frozen core 정의와 격자 수렴을 확인하세요.

```json
{"action":"align","other_id":"다른_계산_ID"}
```

동일 원소·원자 순서를 요구합니다. Kabsch 정렬 RMSD·회전·대응 좌표를 반환하며 자동으로 원자 순서를 바꾸지 않습니다.

```json
{"action":"isotope","masses":[15.99491462,2.01410178,2.01410178]}
```

fchk의 완전 Cartesian Hessian이 필요합니다. 회전·병진 공간을 제거한 질량가중 고유문제를 풀어 새 계산 snapshot을 만듭니다. frozen/partial Hessian 전용 처리를 일반 분자로 가정하지 마세요. 새 질량에 대한 IR/Raman intensity는 생성하지 않습니다.

```json
{"action":"reaction","terms":[{"id":"reactant_ID","coefficient":-1,"energy":"gibbs"},{"id":"product_ID","coefficient":1,"energy":"gibbs"}]}
```

energy=gibbs는 Gaussian 원래 G, 그 외 값은 마지막 electronic energy record를 사용합니다. 계산 조건·화학양론·표준상태는 출력 표에서 검토하세요. 복합 수준 SP 보정은 자동으로 추가하지 않습니다.

```json
{"action":"edit","operation":"translate","indices":[0,1],"vector":[0,0,1],"frame":0}
```

새 구조를 만들고 기존 계산 결과 연결을 해제합니다. operation=coordinate는 indices의 첫 원자에 coords=[x,y,z]를 지정합니다. delete는 선택 원자를 삭제합니다.

```json
{"action":"source","start_line":1000,"count":300}
```

원문 조회는 계산에 실제로 연결한 파일만 대상으로 합니다. 결과 레코드의 line은 전체 원문 파일의 1-based 행입니다. 원본이 없는 프로젝트 snapshot은 원문 조회가 불가능합니다.
