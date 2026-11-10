# GaussLook 1.0

Gaussian 16 결과 분석 프로그램입니다. **하나의 Python 분석 엔진을 X11 GUI와 웹 GUI가 공유**합니다.

```bash
python GaussLook.py
python GaussLook.py --web --port 8888
```

원래 작성한 [구축 기획서](docs/Gaussian16_Analysis_Studio_Planning_KO.md)와 [31쪽 PDF](docs/Gaussian16_Analysis_Studio_Planning_KO.pdf)를 포함합니다. 기획의 전체 범위와 현재 구현을 구분한 [140개 기능 상태표](docs/FEATURE_STATUS.md)를 제공합니다. **GaussView의 모든 기능을 완전히 대체한 버전은 아닙니다.** 일상적인 Gaussian 결과 분석과 공통 엔진을 구현한 첫 배포입니다.

## 설치

Python 3.10 이상을 사용하세요. 개발 검증 환경은 Python 3.12입니다.

```bash
git clone https://github.com/jinstone2001-stack/gauss-look.git
cd gauss-look
python -m pip install -r requirements.txt
python GaussLook.py --check
```

SMILES conformer와 MOL/SDF/MOL2/PDB/CIF 읽기를 사용하려면 추가 설치합니다.

```bash
python -m pip install -r requirements-optional.txt
```

X11 GUI에는 Tkinter가 필요합니다. Ubuntu/Debian은 `sudo apt install python3-tk`, RHEL 계열은 해당 Python 버전에 맞는 tkinter 패키지를 설치하세요. Conda 환경에서는 `conda install tk`를 사용할 수 있습니다. Tkinter는 pip requirements에 넣는 패키지가 아닙니다.

## X11 / MobaXterm

1. MobaXterm의 X server를 시작합니다.
2. SSH session에서 **X11 forwarding**을 활성화합니다. 서버도 SSH X11 forwarding을 허용해야 합니다.
3. 서버에서 `echo $DISPLAY`로 전달된 값을 확인합니다. 값을 임의의 상수로 덮어쓰지 마세요.
4. 다음 명령을 실행합니다.

```bash
python GaussLook.py
python GaussLook.py result.log result.fchk
python GaussLook.py --demo
```

기본 GUI는 Tkinter와 CPU canvas를 사용하므로 원격 OpenGL context가 필수가 아닙니다. 마우스 드래그로 회전, 휠로 확대, 클릭으로 원자를 선택합니다. 2/3/4개 선택 시 거리/각도/이면각을 표시합니다. 한글 font를 사용할 수 있는 Tk에서는 한글 UI를 사용하고, CJK font가 없는 Tk/X11 build에서는 읽을 수 있는 **영문 UI로 자동 전환**합니다. 한글 표시가 필요하면 Noto Sans CJK KR 또는 NanumGothic과 Xft 지원 Tk를 설치하거나 웹 모드를 사용하세요.

표면은 CPU preview로 표시하며 약 2200개 삼각형으로 제한합니다. 복잡한 오비탈 표면·많은 원자가 있는 구조는 웹 모드를 권장합니다. 이 preview 제한은 원본 cube 또는 분석 데이터의 해상도를 변경하지 않습니다.

## 웹 / 현재 PC의 브라우저

서버에서 실행합니다.

```bash
python GaussLook.py --web --port 8888
python GaussLook.py --web --port 8888 --root /path/to/results
```

MobaXterm의 **Tunneling → New SSH tunnel → Local port forwarding**에서 다음처럼 설정합니다.

| 항목 | 값 |
|---|---|
| Forwarded port | `8888` |
| SSH server | 계산 서버 주소 |
| SSH login | 서버 사용자명 |
| Remote server | `127.0.0.1` |
| Remote port | `8888` |

터널을 시작한 뒤 **현재 PC의 Chrome/Edge/Firefox**에서 `http://127.0.0.1:8888`을 엽니다. 원격 서버의 Firefox를 자동 실행하지 않습니다. SSH CLI에서는 `ssh -L 8888:127.0.0.1:8888 user@server`와 같은 터널을 사용할 수 있습니다.

분자 회전은 현재 PC의 WebGL에서 수행합니다. 분석과 파일·cube 생성은 서버에서 수행합니다. 3Dmol.js 2.5.5를 배포물에 포함하므로 실행 시 CDN 접속이 필요하지 않습니다.

`파일 열기`는 PC의 파일을 서버의 임시 작업 공간으로 업로드합니다. `서버 폴더`는 `--root` 안의 서버 파일을 엽니다. 원격 서버의 결과는 서버 폴더로 열면 대형 로그를 PC로 내려받았다 다시 올릴 필요가 없습니다. 기본 서버 주소는 loopback입니다. `--host 0.0.0.0`는 인증이 없는 서버를 네트워크에 노출하므로 개인 SSH 터널 사용 시에는 변경하지 마세요.

## 현재 사용할 수 있는 기능

- `.log/.out`의 작업 분리, 부분 로그 읽기, 구조·최적화 프레임, 에너지 종류·수렴 기준, 정상 종료/SCF/기하 수렴의 분리 표시.
- cclib 보완 parser를 통한 MPn/CC 결과·전하·원자 spin·MO·일부 NMR/전자전이 속성 읽기. 원문 행 번호는 전체 파일 기준으로 보존합니다.
- `.fchk/.fch`의 구조·MO 에너지/점유·전하·dipole·분극률·저장된 모드. checkpoint만으로 정상 종료를 판정하지 않습니다.
- 진동수·imaginary 모드 표, 모드 재생, ±변위 XYZ 저장, IR/Raman/VCD, UV-Vis/ECD, 기준 shielding을 지정한 NMR sticks와 broadening.
- Raman activity→상대강도 변환의 레이저 파장·온도, 주파수 배율·Gaussian/Lorentzian 선폭. 원시 값은 유지합니다.
- Gaussian cube의 여러 field·비직교 축·단위 읽기, ±등치면, field 정보/적분, 같은 격자의 scale/square/add/subtract.
- 공통 API의 mapped field sampling·임의 평면 단면, 구조 정렬 RMSD, 조건 일치 batch 비교, 화학양론 반응 에너지.
- Gaussian RRHO 원본을 유지한 별도 저주파 엔트로피 보정(Truhlar floor 또는 Grimme free rotor interpolation)과 농도 표준상태 보정.
- 완전 fchk Hessian의 동위원소 질량 재분석. 진동수와 변위만 재계산하며 기존 IR/Raman 강도를 재사용하지 않습니다.
- RDKit SMILES→ETKDG conformer→MMFF/UFF, 구조 선택 원자 삭제·좌표 이동, Cartesian Gaussian 입력 생성·추가 입력.
- 프로젝트 snapshot, XYZ/입력/분석 JSON/plot CSV 저장. 웹에서 PNG·plot SVG·HTML 보고서를 저장할 수 있습니다.
- 원본·단위·계산 단계·지원 조건이 연결된 quality dashboard와 기능 가용성 안내. 편집 구조는 기존 계산값과 연결을 해제합니다.

UI에서 일반 분석을 수행하고 `도구` 탭의 **공통 엔진 JSON 분석**으로 고급 기능에 접근합니다. [공통 API 예제](docs/API.md)를 참고하세요. Desktop에도 같은 JSON 분석 창이 있습니다.

## Gaussian utilities

Gaussian을 사용한 서버에서는 평소 사용하는 `g16.profile` 또는 module 환경을 설정한 뒤 실행하세요. `--check`로 발견한 실행 파일 경로를 확인할 수 있습니다.

```bash
python GaussLook.py --check
python GaussLook.py --gaussian-dir /path/to/g16
```

- `.chk` 열기: 원본을 복사한 뒤 `formchk`로 변환합니다. 원본 chk는 변경하지 않습니다.
- `MO·표면`: fchk를 선택하고 MO 번호·spin 또는 density/ESP/spin을 지정해 `cubegen` 작업을 실행합니다.
- `formchk/cubegen`의 반환 코드·오류·결과 파일을 검사합니다. 생성이 실패하면 정상 결과처럼 표시하지 않습니다.
- Gaussian 실행 파일·라이선스는 포함하지 않습니다. 이 개발 환경에는 실제 utility가 없어 **실제 Gaussian 실행 검증은 수행하지 못했습니다**. adapter의 성공/실패 처리는 별도 시험으로 검증합니다.
- 장시간 SCF/Opt 계산 제출, SLURM/PBS job manager, 자동 재시작은 이번 버전에 포함하지 않았습니다. 생성한 `.gjf`를 기존 계산 절차로 실행하세요.

## 해석상 주의와 지원 경계

- `Normal termination`은 전역 최소점·TS 검증 통과를 의미하지 않습니다. Freq 미수행은 허수 모드 0개가 아닙니다.
- MO 표면은 fchk+호환 cubegen 또는 cube가 필요합니다. 로그의 MO 에너지 목록만으로 파동함수를 만들지 않습니다.
- 일부 method·불완전 출력·특수 Gaussian revision은 parser 지원이 부족할 수 있습니다. 에너지 종류와 원본을 확인하세요. 입력의 Z-matrix·복합 ONIOM 원자 지정은 현재 Cartesian 구조 생성 범위 밖입니다.
- IRC/scan은 구조 순서와 추출된 에너지를 표시합니다. 물리적 반응좌표·scan 축, 2D scan 복원, 상세 trajectory 전용 parser는 후속 구현입니다.
- 비조화/ROA/ORD/vibronic 전용 표시, PCM 공동 parser, NBO 상호작용·NTO 정량 CT, orbital tracking, J-coupling multiplet simulation, 완전한 분자 builder·PBC 편집·GMMX/AMPAC은 구현 상태표를 확인하세요.
- X11와 웹의 **공통 분석 수치**를 공유합니다. 렌더 품질·영상 export·일부 설정 화면은 동일하지 않습니다. 웹의 PNG/SVG/HTML export를 native에서 동일하게 지원한다고 주장하지 않습니다.
- 프로젝트는 계산 snapshot을 저장합니다. 대형 cube/파동함수·원본 로그를 모두 내장하는 archive는 아니며, 다시 열 때 원본·cube를 재연결해야 합니다. 임의 host 경로를 신뢰해 자동으로 읽지 않습니다.
- 기본 parser 파일 한도는 512 MiB, 웹 업로드 한도는 256 MiB입니다. 매우 큰 출력은 필요한 작업별로 분리해 사용하세요.
- demo는 실제 Gaussian 결과가 아닌 화면·기능 확인용 합성 데이터입니다. 연구 수치로 사용하지 마세요.

## 명령행 분석과 검증

```bash
python GaussLook.py result.log --json > analysis.json
python GaussLook.py --demo --web --port 8888
python -m pip install pytest
python -m pytest -q
```

자체 시험과 공개 Gaussian 출력 검증의 범위는 [VALIDATION.md](VALIDATION.md)에 기록합니다.

## 라이선스

이 저장소의 `LICENSE`는 소유자의 `Ligand-` 저장소 `main/LICENSE`와 **동일한 내용**입니다. 교육 목적의 비상업적 사용만 허용하고 코드 수정·재배포·상업적 사용을 제한하는 사용자 지정 라이선스입니다. 제3자 구성요소는 각자의 라이선스를 따릅니다. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)를 참고하세요.
