"use strict";
// Only authored UI messages are translated. File names, coordinates, raw output,
// route input and data cells keep the original source text.
const EN_UI = {
  "파일 열기":"Open files", "서버 폴더":"Server folder", "데모":"Demo", "프로젝트 저장":"Save project", "새로고침":"Reload source", "작업 취소":"Cancel task", "설정":"Settings", "화면 설정":"Display settings", "도움말":"Help", "닫기":"Close", "중심":"Fit", "선택 해제":"Clear selection", "XYZ 저장":"Save XYZ", "번호":"Labels", "▶ 경로":"▶ Path", "■ 정지":"■ Stop", "계산 경로 / 스펙트럼":"Energy path / spectrum", "☀ 라이트 모드":"☀ Light mode", "☾ 다크 모드":"☾ Dark mode", "프로젝트 탐색기":"PROJECT EXPLORER",
  "원본 계산 결과와 편집 구조를 구별합니다.":"Original calculation results and edited structures are kept separate.", "파일을 열거나 데모를 선택하세요.":"Open a file or select Demo.",
  "개요":"Overview", "MO·표면":"MO · Surfaces", "진동·분광":"Vibrations · Spectra", "에너지·Force":"Energy · Force", "분극률":"Polarizability", "수렴·TS":"Convergence · TS", "물성":"Properties", "경로":"Path", "비교·열화학":"Compare · Thermochemistry", "구조·입력":"Structure · Input", "도구":"Tools", "지원 범위":"Feature status",
  "파일을 열면 구조와 분석 항목을 표시합니다.":"Open a file to display its structure and analysis.", "선택 결과":"Selected result", "계산 유형":"Calculation type", "전하 / 다중도":"Charge / multiplicity", "원자 / 프레임":"Atoms / frames", "미확인":"Unknown", "미출력":"Not reported", "미설치":"Not installed", "미상":"Unknown", "계산 조건 없음":"No calculation route reported", "에너지 레코드":"Energy records", "종류":"Type", "원문 행":"Source line", "항목":"Item", "상태":"Status", "근거/조건":"Evidence / conditions", "값":"Value", "임계값":"Threshold", "판정":"Result", "기능":"Feature", "가용성":"Availability", "조건":"Conditions", "가능":"Available", "데이터/연동 필요":"Data / utility required",
  "분석 JSON 저장":"Save analysis JSON", "HTML 보고서":"HTML report", "최적화 기준 (마지막 4개)":"Optimization criteria (last four)", "최적화 기준":"Optimization criterion", "첫 imaginary mode 재생":"Play first imaginary mode", "허수 모드를 찾지 못했습니다.":"No imaginary mode was found.",
  "imaginary mode 1개는 TS 후보입니다. 모드 움직임과 양방향 IRC 끝점 연결을 확인하세요.":"One imaginary mode identifies a TS candidate. Inspect the motion and verify both IRC endpoints.",
  "분자 분극률은 고분자의 1 GHz 복소 유전율과 다릅니다.":"Molecular polarizability differs from a polymer's complex permittivity at 1 GHz.",
  "구조 순서와 해당 frame의 에너지를 연결합니다. IRC/scan의 물리적 축이 별도로 추출되지 않은 경우 frame 번호를 사용합니다.":"Structures are linked to their frame energies. Frame numbers are used when a physical IRC / scan coordinate is unavailable.",
  "에너지 경로 그리기":"Plot energy path", "전체 계산 조건 비교":"Compare all calculation conditions", "Gaussian 원래 열화학 (Hartree)":"Original Gaussian thermochemistry (Hartree)", "저주파 cutoff (cm-1)":"Low-frequency cutoff (cm-1)", "엔트로피 보정 모델":"Entropy correction model", "표준 농도 (mol/L, 빈칸=변경 없음)":"Standard concentration (mol/L; empty = unchanged)", "별도 보정 결과":"Calculate separate correction", "구조 정렬 대상":"Structure alignment target", "RMSD 정렬 검사":"Check RMSD alignment",
  "G만 별도로 보정하며 원본을 변경하지 않습니다. 다른 온도는 새로운 frequency/thermochemistry 분석이 필요합니다.":"Only G is corrected in a separate result. Original data remain unchanged. Other temperatures require a new frequency / thermochemistry analysis.",
  "3D conformer 생성":"Generate 3D conformer", "RDKit 필요. 힘장 구조 생성 후 Gaussian 최적화를 수행하세요.":"Requires RDKit. Optimize the generated force-field structure with Gaussian.", "Gaussian 입력 생성":"Build Gaussian input", "Gaussian 입력 저장":"Save Gaussian input", "선택 원자 삭제 → 새 구조":"Delete selected atoms → new structure", "선택 원자 이동 → 새 구조":"Translate selected atoms → new structure", "선택 원자 이동 dx,dy,dz (Å)":"Translate selection dx,dy,dz (Å)", "원자를 먼저 선택하세요.":"Select atoms first.", "사용자 추가 입력 (basis/ECP 등)":"Additional input (basis / ECP blocks, etc.)",
  "편집 구조는 새 항목으로 생성하며 예전 계산 결과를 이어 붙이지 않습니다. 원본으로 돌아가면 이전 구조가 유지됩니다.":"Edits create a new structure without attaching results from the original calculation. The original structure remains available.",
  "원본 출력 첫 500행":"Show first 500 source lines", "원문 시작 행":"First source line", "원문 구간 보기":"Show source range", "동위원소 질량 amu (모든 원자, 쉼표 구분)":"Isotope masses in amu (all atoms, comma separated)", "Hessian 동위원소 재분석":"Reanalyze isotopes from Hessian", "고급 공통 분석 API":"Advanced analysis API", "분석 실행":"Run analysis", "분석 결과":"Analysis result", "JSON 저장":"Save JSON",
  "cube 매핑·단면·격자 연산·반응 에너지 등을 JSON으로 요청할 수 있습니다. 사용법은 README 및 docs/API.md 참조.":"Request cube mapping, sections, grid operations and reaction energies as JSON. See README and docs/API.md.",
  "진동 모드를 먼저 선택하세요.":"Select a vibration mode first.", "변위 데이터가 없습니다.":"No displacement data are available.", "기획서 140개 항목의 구현 상태입니다. 조건부/부분/후속 구현 항목을 완전 지원으로 표시하지 않습니다.":"Implementation status of the 140 planned features. Conditional, partial and planned features are identified explicitly.", "스펙트럼 또는 경로를 선택하세요.":"Select a spectrum or energy path.", "현재 추적 중인 분석 작업이 없습니다.":"No analysis task is currently being tracked.", "작업 진행 중…":"Working…", "DEMO · 화면 시연용 합성 자료. 실제 Gaussian 결과가 아닙니다.":"DEMO · Synthetic data for UI demonstration; not a Gaussian result.",
  "이름":"Name", "폴더":"Folder", "상위 폴더":"↑ Parent folder", "서버 디렉터리 경로":"Server directory path", "이동":"Go", "현재 폴더":"Current folder", "경로를 입력하거나 붙여넣고 Enter를 누르세요. 서버의 허용된 루트 안에서 탐색합니다.":"Type or paste a path and press Enter. Browsing stays within the server's allowed root.", "숫자 오름차순 / 내림차순 정렬 (빈 값은 마지막)":"Sort numerically ascending / descending (missing values last)",
  "표시 설정":"Display settings", "폰트":"Font", "글자 크기 px":"Font size (px)", "Viewer 배경":"Viewer background", "적용":"Apply", "적용 / 저장":"Apply / save", "기본값 복원":"Restore defaults", "테마":"Theme", "다크":"Dark", "라이트":"Light", "언어":"Language", "글꼴·화면":"Font · Appearance", "구조 뷰어":"Structure viewer", "원소별 색상":"Element colors", "원자 크기":"Atom scale", "결합 반지름 (Å)":"Bond radius (Å)", "선택 색상":"Selection color", "레이블 색상":"Label color", "레이블 크기 px":"Label size (px)", "원자 번호 표시":"Show atom labels", "수소 표시":"Show hydrogens", "드래그: 회전 · 휠: 확대 · 오른쪽 드래그: 이동 · 원자 클릭: 선택":"Drag: rotate · Wheel: zoom · Right drag: pan · Click atom: select", "표시 설정을 저장했습니다.":"Display settings saved.",
  "GaussLook 도움말 · 1.3":"GaussLook Help · 1.3", "버튼 이름 / HOMO / frequency / Force / 파일 확장자 검색":"Search buttons / HOMO / frequency / Force / file extension", "예: Reload source, imaginary, polarizability":"Example: Reload source, imaginary, polarizability", "관련 버튼":"Related controls", "검색된 도움말이 없습니다.":"No help topics match your search.",
  "Spin / 공간 오비탈":"Spin / spatial orbital", "선택 MO 번호 (1부터)":"Selected MO number (starts at 1)", "점유":"Occupation", "MO 등치값 |ψ|":"MO isovalue |ψ|", "격자 (미세할수록 오래 걸림)":"Grid (finer takes longer)", "선택 MO ±표면":"Selected MO ± surfaces", "표면 숨기기":"Hide surfaces", "같은 계산의 chk/fchk":"chk/fchk from the same calculation", "로그·chk 연결":"Link log · chk", "Cube · density · ESP 도구":"Cube · density · ESP tools", "공간장":"Scalar field", "Gaussian cubegen으로 생성":"Generate with Gaussian cubegen", "열려 있는 cube":"Open cube", "Field 채널 (0부터)":"Field channel (starts at 0)", "+ 표면":"+ surface", "− 표면":"− surface", "cube를 먼저 여세요.":"Open a cube first.", "cube 정보·적분":"Cube information · integral",
  "에너지 차이는 orbital gap입니다. 여기 에너지·고분자 band gap과 동일한 값으로 해석하지 않습니다. ±표면 색은 오비탈의 위상입니다.":"The energy difference is an orbital gap, distinct from excitation energies and polymer band gaps. Surface colors indicate orbital phase.",
  "MO 에너지가 없습니다. orbital 정보를 출력한 log 또는 chk/fchk를 여세요.":"No MO energies are available. Open a log with orbital output or a chk/fchk file.",
  "MO 표면에는 MO 계수를 저장한 chk/fchk와 Gaussian cubegen이 필요합니다. log만으로는 에너지·점유를 확인할 수 있습니다.":"MO surfaces require a chk/fchk containing MO coefficients and Gaussian cubegen. A log alone can provide energies and occupations.",
  "선택한 MO의 양·음 위상 표면을 함께 생성합니다. 격자는 재사용하고 등치값만 바꾸면 표면을 다시 만듭니다.":"Generate both phases of the selected MO. Cached grids are reused when only the isovalue changes.",
  "진동수 미계산 / 미출력":"Frequencies not calculated / reported", "Imaginary만 보기":"Show imaginary modes only", "진폭 (표시용)":"Amplitude (visualization)", "재생 속도":"Playback speed", "변위 벡터":"Displacement vectors", "재생":"Play", "정지":"Stop", "평형 구조":"Equilibrium structure", "모드":"Mode", "모드 행을 선택하세요.":"Select a mode row.", "표시할 허수 모드가 없습니다.":"No imaginary modes to display.", "Gaussian Freq 결과가 필요합니다.":"Gaussian Freq results are required.", "모드 +변위 XYZ":"Mode + displacement XYZ", "모드 -변위 XYZ":"Mode − displacement XYZ", "IR · Raman · UV · NMR 스펙트럼":"IR · Raman · UV · NMR spectra", "진동수 배율":"Frequency scale", "FWHM (진동 cm-1 / UV eV / NMR ppm)":"FWHM (vibration cm-1 / UV eV / NMR ppm)", "Raman 온도 (K)":"Raman temperature (K)", "스펙트럼 그리기":"Plot spectrum",
  "모드가 계산된 기준 구조에서 재생합니다. 진폭·속도는 시각화 설정입니다. 음의 모드가 1개이면 TS 후보이며, 움직임과 양방향 IRC로 검증하세요.":"Modes play around their reference structure. Amplitude and speed are visual settings. One negative mode is a TS candidate; verify its motion and both IRC directions.",
  "Force 단위":"Force units", "Force 벡터 (보기용 길이 정규화)":"Force vectors (normalized display length)", "에너지·Force CSV":"Energy · Force CSV", "구조 선택":"Select structure", "출력됨":"Reported", "에너지 미출력":"Energy not reported", "전자 에너지":"Electronic energy", "분극률 CSV":"Polarizability CSV",
  "원자별 Force가 출력되지 않았습니다. Force=0이라는 뜻이 아닙니다. .chk의 Cartesian Gradient 또는 force를 출력한 .log를 여세요.":"Atomic forces were not reported; this does not mean Force = 0. Open a .chk with Cartesian Gradient or a .log with force output.",
  "Force = −gradient. 위의 Cartesian 성분 max/RMS와 Gaussian 내부좌표 최적화 수렴 기준값을 구분하세요.":"Force = −gradient. Cartesian component max/RMS values differ from Gaussian's internal-coordinate optimization criteria.",
  "분극률 미계산 / 미출력. Gaussian Polar 또는 해당 response 계산 결과와 chk/fchk를 여세요. 값이 없으면 0으로 표시하지 않습니다.":"Polarizability was not calculated / reported. Open Gaussian Polar or response results and their chk/fchk. Missing values are not shown as zero.",
  "1 a.u. = 0.148184711472 Å³ (polarizability volume). tensor 성분은 좌표계에 따라 달라집니다. 분자 α는 고분자의 1 GHz 복소 유전율·유전손실과 다른 값입니다.":"1 a.u. = 0.148184711472 Å³ (polarizability volume). Tensor components depend on coordinates. Molecular α differs from a polymer's complex permittivity and dielectric loss at 1 GHz.",
  "간편 설정":"Quick settings", "커스텀 설정":"Custom settings", "입력 미리보기":"Input preview", "방법 / XC":"Method / XC", "기저함수":"Basis set", "파동함수":"Wavefunction", "분산 보정":"Dispersion correction", "계산 종류":"Job type", "총전하":"Total charge", "스핀 다중도":"Spin multiplicity", "CPU %NProcShared":"CPU %NProcShared", "메모리 %Mem":"Memory %Mem", "제목 (ASCII)":"Title (ASCII)", "체크포인트 %Chk":"Checkpoint %Chk", "용매":"Solvent", "용매 모델":"Solvation model", "SCF 보조":"SCF solver", "SCF 최대 반복":"SCF max cycles", "수치 적분격자":"Integration grid", "최적화 최대 반복":"Optimization max cycles", "추가 route 키워드":"Additional route keywords", "route 직접 입력":"Enter route directly", "외부 기저 / ECP / 추가 입력":"External basis / ECP / additional input", "입력 생성 / 갱신":"Generate / update input", ".gjf 다운로드":"Download .gjf", "입력 미리보기를 먼저 생성하세요.":"Generate an input preview first.", "방법과 기저함수를 함께 설정합니다. 현재 선택한 frame의 Cartesian 좌표를 사용합니다.":"Configure the method and basis together. Cartesian coordinates come from the selected frame.", "총전하와 다중도 및 Gen/ECP 블록을 확인하세요. Gaussian 실행이나 스케줄러 제출은 하지 않습니다.":"Check total charge, multiplicity and Gen/ECP blocks. This builds input; it does not run Gaussian or submit a scheduler job.", "Gen / GenECP 사용 시 검증한 기저 / ECP 블록을 직접 입력하세요. 자동 ECP 추정은 하지 않습니다.":"For Gen / GenECP, provide validated basis / ECP blocks below. ECP assignments are not inferred.", "입력 생성 중…":"Generating input…", "서버 폴더 열기":"Open server folder", "화면 설정을 변경합니다.":"Adjust appearance and molecular rendering.", "언어를 선택합니다. 전문용어와 원본 계산 자료는 유지합니다.":"Choose the UI language. Scientific terms and original calculation data are preserved."
};
const KO_UI = { "Ball & stick":"공·막대", "Sticks":"막대", "Wireframe":"선", "Space filling":"공간 채움", "Atom":"원자", "Frame":"프레임", "Charge":"전하", "Multiplicity":"다중도", "Memory":"메모리", "Cores":"CPU", "Spectrum":"스펙트럼", "Isotropic mean":"등방성 평균", "Polarizability volume":"분극률 부피", "Anisotropy":"비등방성", "Polar source":"분극률 출처", "HOMO–LUMO gap":"HOMO–LUMO gap" };
function translate(text) {
  if (typeof text !== "string") return text;
  if (settings.language !== "en") return KO_UI[text] || text;
  if (EN_UI[text]) return EN_UI[text];
  return text
    .replace(/^imaginary 1개 \(([-+\d.]+) cm-1\)\. 의도한 TS인지 모드와 양방향 IRC로 확인하세요\.$/, "One imaginary mode ($1 cm-1). Verify the intended TS using its motion and both IRC directions.")
    .replace(/^imaginary (\d+)개\. 작은 음수도 자동 삭제하지 않습니다\.$/, "$1 imaginary modes. Small negative frequencies are retained.")
    .replace(/\. 방법별 해석 필요\.$/, ". Interpret according to the calculation method.");
}
function t(text) { return translate(text); }
function ui(ko, en) { return settings.language === "en" ? en : ko; }
Object.assign(EN_UI, {
  "한국어 / 시스템 글꼴":"Korean / system fonts", "크기":"Size", "파일":"File",
  "제목":"Title", "용매 (SMD)":"Solvent (SMD)", "Arial / 맑은 고딕":"Arial / Malgun Gothic", "Calibri / 굴림":"Calibri / Gulim",
  "고유값 / a.u.":"Eigenvalues / a.u.", "부분·조건부":"Partial / conditional", "지원":"Supported", "후속 구현":"Planned",
  "계산 종료":"Calculation termination", "기하 최적화":"Geometry optimization", "정지점 분류":"Stationary point classification", "파동함수 안정성":"Wavefunction stability",
  "정상 종료와 기하 수렴·정지점 종류는 별개입니다.":"Normal termination, geometry convergence and stationary point classification are separate checks.",
  "해당 작업의 SCF 결과 레코드를 기준으로 표시합니다.":"Based on the SCF records for this job.", "최적화 작업에만 적용합니다.":"Applies to geometry optimization jobs only.",
  "frequency가 없습니다. imaginary 0개라는 뜻이 아닙니다.":"No frequency results are available; this does not mean zero imaginary modes.",
  "음의 normal-mode 진동수 없음. gradient·제약·계산 조건 일치 확인 필요.":"No negative normal-mode frequencies. Check gradients, constraints and calculation conditions.",
  "정상 SCF 종료만으로 Stable 계산 통과를 추정하지 않습니다.":"Normal SCF termination does not establish wavefunction stability.",
  "구조·측정":"Structure · Measurements", "에너지·수렴":"Energy · Convergence", "진동 애니메이션":"Vibration animation", "cube 생성":"Cube generation", "동위원소 재분석":"Isotope analysis", "비조화·Vibronic·ROA 정량 표시":"Anharmonic · Vibronic · ROA quantitative display",
  "좌표가 필요합니다.":"Coordinates are required.", "계산 결과 로그가 필요합니다.":"A calculation log is required.", "모드별 Cartesian 변위가 필요합니다.":"Cartesian displacements for each mode are required.",
  "IR intensity가 필요합니다.":"IR intensities are required.", "Raman activity가 필요합니다.":"Raman activities are required.", "여기 상태 에너지·oscillator strength가 필요합니다.":"Excitation energies and oscillator strengths are required.", "NMR shielding이 필요합니다.":"NMR shielding is required.", "MO 에너지·점유 데이터가 필요합니다.":"MO energies and occupations are required.",
  "fchk 및 Gaussian cubegen 실행 환경이 필요합니다.":"An fchk and a working Gaussian cubegen environment are required.", "Hessian을 저장한 checkpoint와 Gaussian freqchk가 필요합니다.":"A checkpoint containing the Hessian and Gaussian freqchk are required.", "현재 버전에서는 전용 parser가 검증되지 않았습니다. 원본 출력에서 확인하세요.":"The dedicated parser has not been validated in this release. Check the original output.",
  "사용 가능":"Available", "화면 시연용 합성 자료입니다. 실제 Gaussian 계산값이 아닙니다.":"Synthetic demonstration data; not an actual Gaussian result.",
});
// Focused analysis UI. Numerical values are produced by the shared Python engine.
let helpData = { topics: [] },
  activeSpin = "alpha",
  activeMO = null,
  activePolar = null,
  modeAmplitude = 0.5,
  modeSpeed = 1,
  modeVectors = false,
  forceVectors = false,
  vectorShapes = [],
  forceUnits = "Eh/Bohr",
  frameRequest = 0;
function helpText(label) {
  const control = helpData.controls?.find((c) => c.labels.includes(label));
  if (control) return settings.language === "en" ? control.summary_en || control.summary_ko : control.summary_ko;
  const topic = helpData.topics.find((t) => t.buttons.includes(label));
  return (
    (settings.language === "en" ? topic?.summary_en : topic?.summary_ko) ||
    (settings.language === "en" ? `${t(label)}: See Help for controls, required data and input conditions.` : `${label}: 자세한 조작·입력 조건은 도움말에서 확인하세요.`)
  );
}
function applyHelpTitles() {
  document.querySelectorAll("button").forEach((b) => {
    if (!b.title) b.title = helpText(b.dataset.label || b.textContent.trim());
  });
}
function openHelp() {
  tab = "도움말";
  renderPanel();
}
function renderHelp(parent) {
  parent.append(node("h2", "GaussLook 도움말 · 1.3"));
  const search = field(
    parent,
    "버튼 이름 / HOMO / frequency / Force / 파일 확장자 검색",
    "",
  );
  search.placeholder = t("예: Reload source, imaginary, polarizability");
  const list = node("div", undefined, "help-topics");
  parent.append(list);
  const content = node("article", undefined, "help-content");
  parent.append(content);
  function show(t) {
    const language = settings.language;
    content.replaceChildren(
      node("h3", t["title_" + language] || t.title_ko),
      node("p", t["summary_" + language] || t.summary_ko),
      node("p", t["body_" + language] || t.body_ko, "manual-body"),
    );
    content.append(
      node("h4", "관련 버튼"),
      node("p", t.buttons.map(translate).join(" · "), "note"),
    );
  }
  function filter() {
    const q = search.value.toLocaleLowerCase();
    list.replaceChildren();
    content.replaceChildren();
    const topics = helpData.topics.filter((t) =>
      [t.title_ko, t.title_en, t.body_ko, t.body_en, ...t.buttons]
        .join(" ")
        .toLocaleLowerCase()
        .includes(q),
    );
    topics.forEach((topic) => button(list, topic["title_" + settings.language] || topic.title_ko, () => show(topic)));
    if (topics.length) show(topics[0]);
    else note(content, "검색된 도움말이 없습니다.");
  }
  search.oninput = filter;
  filter();
}
function metric(parent, label, value) {
  const c = node("div", undefined, "metric");
  c.append(node("small", t(label)), node("strong", value === undefined || value === null ? t("미출력") : t(value)));
  parent.append(c);
}
function renderMO(parent) {
  const channels = calc.orbital_analysis.channels;
  if (!channels[activeSpin]) activeSpin = Object.keys(channels)[0] || "alpha";
  const spin = select(
    parent,
    "Spin / 공간 오비탈",
    Object.keys(channels).map((k) => [k, k]),
    activeSpin,
  );
  spin.onchange = () => {
    activeSpin = spin.value;
    activeMO = null;
    renderPanel();
  };
  const o = channels[activeSpin] || { rows: [] };
  if (!o.rows.some((r) => r.mo === activeMO)) activeMO = o.homo?.mo || 1;
  const cards = node("div", undefined, "metrics");
  parent.append(cards);
  for (const name of ["homo", "lumo"]) {
    const r = o[name];
    metric(
      cards,
      name.toUpperCase(),
      r ? `MO ${r.mo} · ${r.energy_eV.toFixed(6)} eV` : "미확인",
    );
  }
  metric(
    cards,
    "HOMO–LUMO gap",
    o.gap_eV !== undefined && o.gap_eV !== null
      ? o.gap_eV.toFixed(6) + " eV"
      : "미확인",
  );
  note(
    parent,
    "에너지 차이는 orbital gap입니다. 여기 에너지·고분자 band gap과 동일한 값으로 해석하지 않습니다. ±표면 색은 오비탈의 위상입니다.",
  );
  const control = node("div", undefined, "row");
  parent.append(control);
  let moInput;
  function choose(n) {
    activeMO = n;
    if (moInput) moInput.value = n;
    drawDiagram();
    highlight();
  }
  for (const name of ["HOMO", "LUMO"]) {
    const b = button(control, name, () => {
      if (o[name.toLowerCase()]) choose(o[name.toLowerCase()].mo);
    });
    b.disabled = !o[name.toLowerCase()];
  }
  moInput = field(parent, "선택 MO 번호 (1부터)", activeMO, "number");
  moInput.min = 1;
  moInput.max = o.rows.length || 1;
  moInput.onchange = () => choose(+moInput.value);
  const diagram = node("div", undefined, "orbital-diagram");
  parent.append(diagram);
  let moTable;
  function highlight() {
    moTable
      ?.querySelectorAll("tbody tr")
      .forEach((tr) =>
        tr.classList.toggle("selected", o.rows[+tr.dataset.originalIndex].mo === activeMO),
      );
  }
  function drawDiagram() {
    diagram.replaceChildren();
    const h = o.homo?.mo || activeMO;
    const rows = o.rows.filter(
      (r) => (r.mo >= h - 2 && r.mo <= h + 3) || r.mo === activeMO,
    );
    if (!rows.length) {
      note(
        diagram,
        "MO 에너지가 없습니다. orbital 정보를 출력한 log 또는 chk/fchk를 여세요.",
      );
      return;
    }
    const ns = "http://www.w3.org/2000/svg",
      svg = document.createElementNS(ns, "svg");
    svg.setAttribute("viewBox", "0 0 520 190");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "MO energy diagram (eV)");
    const es = rows.map((r) => r.energy_eV),
      lo = Math.min(...es),
      span = Math.max(1, Math.max(...es) - lo);
    function item(tag, attrs, text) {
      const e = document.createElementNS(ns, tag);
      Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v));
      if (text !== undefined) e.textContent = text;
      svg.append(e);
      return e;
    }
    const light = settings.theme === "light";
    item("text", { x: 5, y: 15, fill: light ? "#3e5269" : "#a2b7ce", "font-size": 12 }, "eV");
    rows.forEach((r, i) => {
      const x = 48 + (i * 440) / Math.max(1, rows.length - 1),
        y = 146 - ((r.energy_eV - lo) / span) * 110,
        color =
          r.mo === activeMO ? (light ? "#00676c" : "#57d1c9") : r.occupation ? (light ? "#215a96" : "#65bafa") : (light ? "#9b2852" : "#f29eb0");
      const line = item("line", {
        x1: x - 20,
        x2: x + 20,
        y1: y,
        y2: y,
        stroke: color,
        "stroke-width": r.mo === activeMO ? 6 : 4,
        tabindex: 0,
        role: "button",
        "aria-label": `Select MO ${r.mo}`,
      });
      line.style.cursor = "pointer";
      line.onclick = () => choose(r.mo);
      line.onkeydown = (e) => {
        if (e.key === "Enter") choose(r.mo);
      };
      item(
        "text",
        { x, y: y - 12, fill: color, "font-size": 11, "text-anchor": "middle" },
        `${r.mo} ${r.label}`,
      );
      item(
        "text",
        {
          x,
          y: y + 18,
          fill: light ? "#203146" : "#c5d3e4",
          "font-size": 11,
          "text-anchor": "middle",
        },
        r.energy_eV.toFixed(3),
      );
    });
    diagram.append(svg);
  }
  const tableArea = node("div", undefined, "table-scroll");
  parent.append(tableArea);
  moTable = table(
    tableArea,
    ["MO", "종류", "eV", "Hartree", "점유"],
    o.rows.map((r) => [
      r.mo,
      r.label,
      r.energy_eV.toFixed(6),
      r.energy_hartree.toFixed(8),
      r.occupation,
    ]),
    (i) => choose(o.rows[i].mo),
  );
  drawDiagram();
  highlight();
  const level = field(parent, "MO 등치값 |ψ|", 0.03, "number"),
    grid = select(
      parent,
      "격자 (미세할수록 오래 걸림)",
      ["coarse", "medium", "fine"].map((v) => [v, v]),
    );
  const b = button(parent, "선택 MO ±표면", async () =>
    result(
      await action("orbital_surface", {
        spin: activeSpin,
        orbital: +moInput.value,
        grid: grid.value,
        level: +level.value,
      }),
    ),
  );
  b.disabled = !calc.orbital_surface_ready || !o.has_coefficients;
  note(
    parent,
    b.disabled
      ? "MO 표면에는 MO 계수를 저장한 chk/fchk와 Gaussian cubegen이 필요합니다. log만으로는 에너지·점유를 확인할 수 있습니다."
      : "선택한 MO의 양·음 위상 표면을 함께 생성합니다. 격자는 재사용하고 등치값만 바꾸면 표면을 다시 만듭니다.",
  );
  button(parent, "표면 숨기기", clearShapes);
  if (calc.kind !== "checkpoint" && calc.kind !== "cube") {
    const options = state.calculations.filter(
      (c) => c.kind === "checkpoint" && c.checkpoint_linked,
    );
    if (options.length) {
      const chk = select(
        parent,
        "같은 계산의 chk/fchk",
        options.map((c) => [c.id, c.name]),
      );
      button(parent, "로그·chk 연결", async () =>
        result(await action("link_checkpoint", { checkpoint_id: chk.value })),
      );
    }
  }
  const advanced = node("details");
  advanced.append(node("summary", "Cube · density · ESP 도구"));
  parent.append(advanced);
  const kind = select(advanced, "공간장", [
    ["density", "SCF density"],
    ["potential", "SCF ESP"],
    ["spin", "SCF spin density"],
  ]);
  button(advanced, "Gaussian cubegen으로 생성", async () =>
    result(
      await action("generate_cube", { kind: kind.value, grid: grid.value }),
    ),
  );
  const fs = Object.entries(state.fields || {}),
    fld = select(
      advanced,
      "열려 있는 cube",
      fs.map(([id, f]) => [id, f.name]),
      calc.properties.field_id,
    ),
    channel = field(advanced, "Field 채널 (0부터)", 0, "number");
  for (const sign of [1, -1])
    button(advanced, sign > 0 ? "+ 표면" : "− 표면", async () => {
      if (!fld.value) throw Error("cube를 먼저 여세요.");
      const mesh = await action("mesh", {
        field_id: fld.value,
        level: sign * Math.abs(+level.value),
        channel: +channel.value,
      });
      addMesh(mesh);
      requestViewerRender();
      status(
        `surface ${mesh.level}: ${mesh.faces.length} triangles · preview stride ${mesh.preview_stride}`,
      );
    });
  button(advanced, "cube 정보·적분", async () =>
    showObject(
      await action("integrate", {
        field_id: fld.value,
        channel: +channel.value,
      }),
    ),
  );
}
function addMesh(mesh) {
  const sh = viewer.addCustom({
    vertexArr: mesh.vertices.map((v) => new $3Dmol.Vector3(...v)),
    normalArr: mesh.normals.map((v) => new $3Dmol.Vector3(...v)),
    faceArr: mesh.faces.flat(),
    color: mesh.level > 0 ? "#58b9f8" : "#f27e96",
    opacity: 0.7,
  });
  meshes.push(sh);
}
function clearShapes() {
  if (viewer) {
    viewer.removeAllShapes();
    requestViewerRender();
  }
  meshes = [];
  vectorShapes = [];
}
function drawVectors(coords, vectors) {
  vectorShapes.forEach((sh) => viewer.removeShape(sh));
  vectorShapes = [];
  if (!vectors?.length || !viewer) return;
  const max = Math.max(...vectors.map((v) => Math.hypot(...v)));
  if (!max) return;
  coords.forEach((v, i) => {
    const end = v.map((x, j) => x + (0.9 * vectors[i][j]) / max);
    vectorShapes.push(
      viewer.addArrow({
        start: { x: v[0], y: v[1], z: v[2] },
        end: { x: end[0], y: end[1], z: end[2] },
        radius: 0.025,
        color: "#ffd078",
      }),
    );
  });
  requestViewerRender();
}
function renderVibrations(parent) {
  const modes = calc.modes,
    imag = modes.filter((m) => m.frequency_cm1 < 0);
  const c = node("div", undefined, imag.length ? "card imaginary" : "card");
  c.append(
    node(
      "strong",
      modes.length
        ? ui(`${modes.length}개 모드 · imaginary ${imag.length}개`, `${modes.length} modes · ${imag.length} imaginary`)
        : t("진동수 미계산 / 미출력"),
    ),
  );
  parent.append(c);
  const only = field(parent, "Imaginary만 보기", false, "checkbox");
  only.checked = false;
  const amp = field(parent, "진폭 (표시용)", modeAmplitude, "number"),
    speed = select(
      parent,
      "재생 속도",
      [
        [".5", "0.5×"],
        ["1", "1×"],
        ["2", "2×"],
        ["4", "4×"],
      ],
      String(modeSpeed),
    );
  amp.onchange = () => {
    modeAmplitude = +amp.value;
    if (timer && modeIndex !== null) animateMode(modeIndex, modeAmplitude);
  };
  speed.onchange = () => {
    modeSpeed = +speed.value;
  };
  const arrows = field(parent, "변위 벡터", modeVectors, "checkbox");
  arrows.checked = modeVectors;
  arrows.onchange = () => {
    modeVectors = arrows.checked;
    if (!modeVectors) drawVectors([], null);
  };
  const r = node("div", undefined, "row");
  parent.append(r);
  button(r, "재생", () => {
    if (modeIndex === null) throw Error("모드 행을 선택하세요.");
    animateMode(modeIndex, +amp.value);
  });
  button(r, "정지", stop);
  button(r, "평형 구조", () => {
    stop();
    if (modeIndex !== null)
      frame = modes[modeIndex].reference_frame ?? calc.frames.length - 1;
    $("frame").value = frame;
    drawVectors([], null);
    draw();
  });
  const area = node("div", undefined, "table-scroll modes");
  parent.append(area);
  function rows() {
    area.replaceChildren();
    const indices = modes
      .map((_, i) => i)
      .filter((i) => !only.checked || modes[i].frequency_cm1 < 0);
    const t = table(
      area,
      ["모드", "cm-1", "IR / km mol-1", "Raman"],
      indices.map((i) => [
        i + 1,
        modes[i].frequency_cm1,
        modes[i].ir_km_mol,
        modes[i].raman_activity,
      ]),
      (j, tr) => {
        animateMode(indices[j], +amp.value);
        t.querySelectorAll("tr").forEach((r) => r.classList.remove("selected"));
        tr.classList.add("selected");
      },
    );
    t.querySelectorAll("tbody tr").forEach((r, j) =>
      r.classList.toggle("imaginary", modes[indices[j]].frequency_cm1 < 0),
    );
    if (!indices.length)
      note(
        area,
        modes.length
          ? "표시할 허수 모드가 없습니다."
          : "Gaussian Freq 결과가 필요합니다.",
      );
  }
  only.onchange = rows;
  rows();
  button(parent, "모드 +변위 XYZ", () => displace(+amp.value));
  button(parent, "모드 -변위 XYZ", () => displace(-amp.value));
  note(
    parent,
    "모드가 계산된 기준 구조에서 재생합니다. 진폭·속도는 시각화 설정입니다. 음의 모드가 1개이면 TS 후보이며, 움직임과 양방향 IRC로 검증하세요.",
  );
  const adv = node("details");
  adv.append(node("summary", "IR · Raman · UV · NMR 스펙트럼"));
  adv.open = true;
  parent.append(adv);
  const kind = select(
      adv,
      "Spectrum",
      ["IR", "Raman", "VCD", "UV-Vis", "ECD", "NMR"].map((v) => [v, v]),
    ),
    scale = field(adv, "진동수 배율", 1, "number"),
    width = field(adv, "FWHM (진동 cm-1 / UV eV / NMR ppm)", 12, "number"),
    laser = field(adv, "Raman laser (nm)", 532, "number"),
    temp = field(adv, "Raman 온도 (K)", 298.15, "number"),
    ref = field(adv, "NMR reference shielding (ppm)", 0, "number");
  kind.onchange = () =>
    (width.value = ["UV-Vis", "ECD"].includes(kind.value)
      ? 0.25
      : kind.value === "NMR"
        ? 0.05
        : 12);
  button(adv, "스펙트럼 그리기", async () => {
    plotData = await action("spectrum", {
      kind: kind.value,
      scale: +scale.value,
      width: +width.value,
      laser_nm: +laser.value,
      temperature: +temp.value,
      reference: +ref.value,
    });
    plot();
  });
}
function renderForces(parent) {
  const unit = select(
    parent,
    "Force 단위",
    [
      ["Eh/Bohr", "Hartree/Bohr"],
      ["eV/A", "eV/Å"],
    ],
    forceUnits,
  );
  unit.onchange = () => {
    forceUnits = unit.value;
    updateForcePanel();
  };
  const arrows = field(
    parent,
    "Force 벡터 (보기용 길이 정규화)",
    forceVectors,
    "checkbox",
  );
  arrows.checked = forceVectors;
  arrows.onchange = () => {
    forceVectors = arrows.checked;
    updateForcePanel();
  };
  const content = node("div");
  content.id = "forceContent";
  parent.append(content);
  button(parent, "에너지·Force CSV", exportForceCSV);
  button(parent, "에너지 경로 그리기", pathPlot);
  parent.append(node("h3", "구조 선택"));
  table(
    parent,
    ["Frame", "Energy / Hartree", "종류", "Force"],
    calc.frames.map((f, i) => [
      i + 1,
      f.energy_hartree === null || f.energy_hartree === undefined
        ? "—"
        : f.energy_hartree.toFixed(12),
      f.energy_kind,
      t(f.force_record !== undefined && f.force_record !== null ? "출력됨" : "미출력"),
    ]),
    (i) => {
      stop();
      frame = i;
      $("frame").value = i;
      clearShapes();
      draw();
    },
  );
  updateForcePanel();
}
async function updateForcePanel() {
  if (tab !== "에너지·Force" || !calc) return;
  const cid = calc.id,
    at = frame,
    request = ++frameRequest,
    d = await action("frame_analysis", { frame });
  if (
    !calc ||
    calc.id !== cid ||
    frame !== at ||
    request !== frameRequest ||
    !$("forceContent")
  )
    return;
  const p = $("forceContent");
  p.replaceChildren();
  const cards = node("div", undefined, "metrics");
  p.append(cards);
  metric(
    cards,
    `Frame ${frame + 1} · ${d.energy?.kind || "energy"}`,
    d.energy ? d.energy.hartree.toFixed(12) + " Eh" : "에너지 미출력",
  );
  if (d.energy) metric(cards, "전자 에너지", d.energy.eV.toFixed(8) + " eV");
  const f = d.force,
    factor = forceUnits === "eV/A" ? 27.211386245988 / 0.529177210903 : 1;
  if (!f) {
    note(
      p,
      "원자별 Force가 출력되지 않았습니다. Force=0이라는 뜻이 아닙니다. .chk의 Cartesian Gradient 또는 force를 출력한 .log를 여세요.",
    );
    drawVectors([], null);
    return;
  }
  metric(
    cards,
    "Max Cartesian component",
    (f.max_component_hartree_bohr * factor).toPrecision(7) + " " + forceUnits,
  );
  metric(
    cards,
    "RMS Cartesian component",
    (f.rms_component_hartree_bohr * factor).toPrecision(7) + " " + forceUnits,
  );
  note(p, `${f.source} · ${t("원문 행")} ${f.line ?? "—"} · ${f.coordinate_system}`);
  table(
    p,
    ["Atom", "Fx", "Fy", "Fz", "|F|"],
    f.vectors_hartree_bohr.map((v, i) => [
      `${i + 1} ${elements[calc.atoms[i]]}`,
      ...v.map((x) => (x * factor).toPrecision(7)),
      (f.norms_hartree_bohr[i] * factor).toPrecision(7),
    ]),
    (i) => {
      selected = [i];
      applyStyle();
      showSelection();
    },
  );
  note(
    p,
    "Force = −gradient. 위의 Cartesian 성분 max/RMS와 Gaussian 내부좌표 최적화 수렴 기준값을 구분하세요.",
  );
  const start = calc.frames[frame].line ?? 0,
    end = calc.frames[frame + 1]?.line ?? Infinity;
  const criteria = calc.convergence
    .filter((v) => v.line >= start && v.line < end)
    .slice(-4);
  if (criteria.length)
    table(
      p,
      ["최적화 기준", "값", "임계값", "판정"],
      criteria.map((v) => [
        v.item,
        v.value,
        v.threshold,
        v.passed ? "YES" : "NO",
      ]),
    );
  if (forceVectors)
    drawVectors(calc.frames[frame].coords, f.vectors_hartree_bohr);
  else drawVectors([], null);
}
async function exportForceCSV() {
  const rows = [
    [
      "Frame",
      "Energy kind",
      "Energy / Eh",
      "Atom",
      "Element",
      "Fx / Eh/Bohr",
      "Fy / Eh/Bohr",
      "Fz / Eh/Bohr",
      "Norm / Eh/Bohr",
    ],
  ];
  const cid = calc.id;
  for (let i = 0; i < calc.frames.length; i++) {
    const d = await api("/api/action", {
        action: "frame_analysis",
        id: cid,
        frame: i,
      }),
      e = d.energy || {},
      f = d.force;
    if (f)
      f.vectors_hartree_bohr.forEach((v, j) =>
        rows.push([
          i + 1,
          e.kind,
          e.hartree,
          j + 1,
          elements[calc.atoms[j]],
          ...v,
          f.norms_hartree_bohr[j],
        ]),
      );
    else rows.push([i + 1, e.kind, e.hartree]);
  }
  download("energy_forces.csv", csv(rows), "text/csv");
}
function renderPolar(parent) {
  const data = calc.polarizability_analysis,
    records = data.records;
  if (!records.length) {
    note(
      parent,
      "분극률 미계산 / 미출력. Gaussian Polar 또는 해당 response 계산 결과와 chk/fchk를 여세요. 값이 없으면 0으로 표시하지 않습니다.",
    );
    return;
  }
  const source = select(
      parent,
      "Polar source",
      records.map((r, i) => [
        i,
        `${r.source} · W=${r.frequency_au ?? "?"} a.u.`,
      ]),
      records[activePolar] ? activePolar : data.default_index,
    ),
    content = node("div");
  parent.append(content);
  function show() {
    const r = records[+source.value];
    content.replaceChildren();
    const cards = node("div", undefined, "metrics");
    content.append(cards);
    metric(cards, "Isotropic mean", r.mean_au.toFixed(8) + " a.u.");
    metric(cards, "Polarizability volume", r.mean_A3.toFixed(8) + " Å³");
    metric(cards, "Anisotropy", r.anisotropy_au.toFixed(8) + " a.u.");
    table(
      content,
      ["α / a.u.", "X", "Y", "Z"],
      r.tensor_au.map((row, i) => ["XYZ"[i], ...row.map((v) => v.toFixed(8))]),
    );
    note(
      content,
      t("고유값 / a.u.") + ": " + r.eigenvalues_au.map((v) => v.toFixed(8)).join(", "),
    );
    note(
      content,
      `${r.source} · ${t("원문 행")} ${r.line ?? "—"} · ${r.orientation ?? "as reported"} · W=${r.frequency_au ?? t("미상")} a.u. ${r.frequency_au === 0 ? "(static)" : ""}`,
    );
    note(
      content,
      "1 a.u. = 0.148184711472 Å³ (polarizability volume). tensor 성분은 좌표계에 따라 달라집니다. 분자 α는 고분자의 1 GHz 복소 유전율·유전손실과 다른 값입니다.",
    );
    button(content, "분극률 CSV", () =>
      download(
        "polarizability.csv",
        csv([
          ["Source", r.source],
          ["Frequency / a.u.", r.frequency_au],
          ["Tensor / a.u.", "X", "Y", "Z"],
          ...r.tensor_au.map((row, i) => ["XYZ"[i], ...row]),
          ["Mean / a.u.", r.mean_au],
          ["Mean / A^3", r.mean_A3],
          ["Anisotropy / a.u.", r.anisotropy_au],
        ]),
        "text/csv",
      ),
    );
  }
  source.onchange = () => { activePolar = +source.value; show(); };
  show();
}
