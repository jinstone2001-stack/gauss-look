"use strict";
const $ = (id) => document.getElementById(id);
let state = {},
  calc = null,
  selected = [],
  frame = 0,
  viewer = null,
  model = null,
  meshes = [],
  plotData = null,
  timer = null,
  modeIndex = null,
  currentTask = null,
  renderedFrameKey = null,
  settings = {
    language: "ko", theme: "dark", labels: false, hydrogens: true,
    style: "ball", background: "#101b2b", atomScale: 0.3, bondRadius: 0.14,
    selection: "#00d8e6", labelColor: "#f1f5fa", labelSize: 12,
    fontKo: "Malgun Gothic", fontEn: "Arial", fontSize: 14,
    elementColors: { H: "#e8edf4", C: "#7891ad", N: "#4d8eff", O: "#ff5b68", F: "#5bd684", P: "#f4a340", S: "#ebd14b", Cl: "#5bd684", Br: "#b56d4b", I: "#aa80db", Sn: "#8bcad5" },
  };
const defaultSettings = JSON.parse(JSON.stringify(settings));
try {
  const saved = JSON.parse(localStorage.getItem("gausslook.settings") || "{}");
  settings = {
    ...settings,
    ...saved,
  };
  if (typeof saved?.font === "string") {
    if (!saved.fontEn && saved.font.startsWith("Calibri")) settings.fontEn = "Calibri";
    if (!saved.fontKo && saved.font.includes('"Gulim"')) settings.fontKo = "Gulim";
    if (!saved.fontKo && saved.font.startsWith('"Noto Sans CJK KR"')) settings.fontKo = "Noto Sans CJK KR";
  }
} catch (e) {}
settings.elementColors = { ...defaultSettings.elementColors, ...settings.elementColors };
settings.language = settings.language === "en" ? "en" : "ko";
settings.theme = settings.theme === "light" ? "light" : "dark";
delete settings.font;
for (const key of ["fontKo", "fontEn"])
  if (typeof settings[key] !== "string" || !settings[key].trim()) settings[key] = defaultSettings[key];
settings.fontSize = Math.round(Math.max(10, Math.min(24, Number(settings.fontSize) || 14)));
const tabs = [
  "개요",
  "MO·표면",
  "진동·분광",
  "에너지·Force",
  "분극률",
  "수렴·TS",
  "물성",
  "경로",
  "비교·열화학",
  "구조·입력",
  "도구",
  "지원 범위",
  "도움말",
];
let tab = tabs[0];
let statusMessage = "파일을 열거나 데모를 선택하세요.", statusError = false;
function node(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = ["h2", "h3", "h4", "summary"].includes(tag) ? t(String(text)) : String(text);
  if (cls) n.className = cls;
  return n;
}
function status(t, error = false) {
  statusMessage = t;
  statusError = error;
  $("status").textContent = translate(t);
  $("status").classList.toggle("error", error);
}
async function api(path, body) {
  if (body !== undefined && !["frame_analysis", "measure"].includes(body.action)) interruptAnimation();
  const r = await fetch(
    path,
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
  );
  const d = await r.json();
  if (!r.ok || d.error) throw Error(d.error || r.statusText);
  return d;
}
function button(parent, label, fn) {
  const b = node("button", t(label));
  b.dataset.label = label;
  b.title = helpText(label);
  b.onclick = async () => {
    try {
      interruptAnimation();
      await fn();
    } catch (e) {
      status(e.message, true);
    }
  };
  parent.append(b);
  return b;
}
function note(parent, text) {
  parent.append(node("p", t(text), "note"));
}
function field(parent, label, value, type = "text") {
  const l = node("label", t(label), "field"),
    v = node("input");
  v.type = type;
  v.value = value ?? "";
  l.append(v);
  parent.append(l);
  return v;
}
function select(parent, label, options, value) {
  const l = node("label", t(label), "field"),
    s = node("select");
  for (const [v, text] of options) s.append(new Option(t(text), v));
  if (value !== undefined) s.value = value;
  l.append(s);
  parent.append(l);
  return s;
}
function table(parent, headers, rows, onClick) {
  const tableElement = node("table"),
    head = node("tr");
  const thead = node("thead");
  thead.append(head);
  tableElement.append(thead);
  const body = node("tbody");
  const records = [];
  rows.forEach((row, i) => {
    const tr = node("tr");
    tr.dataset.originalIndex = String(i);
    row.forEach((v) =>
      tr.append(node("td", typeof v === "number" ? format(v) : (v ?? "—"))),
    );
    if (onClick) {
      tr.className = "selectable";
      tr.onclick = () => onClick(i, tr);
    }
    body.append(tr);
    records.push({ row, index: i, element: tr });
  });
  let sortColumn = -1, ascending = true;
  const numeric = (v) => {
    if (v === null || v === undefined || v === "" || v === "—") return null;
    if (typeof v === "number") return Number.isFinite(v) ? v : NaN;
    if (typeof v === "string" && /^\d+\s+[A-Z][a-z]?$/.test(v.trim())) return parseInt(v, 10);
    if (typeof v !== "string" || !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eEdD][+-]?\d+)?$/.test(v.trim())) return NaN;
    return Number(v.trim().replace(/[dD]/, "e"));
  };
  headers.forEach((h, column) => {
    const th = node("th", t(h));
    const values = rows.map((r) => numeric(r[column]));
    if (values.some((v) => v !== null && Number.isFinite(v)) && values.every((v) => v === null || Number.isFinite(v))) {
      th.replaceChildren();
      th.className = "numeric-sort";
      th.setAttribute("aria-sort", "none");
      const b = button(th, h, () => {
        ascending = sortColumn === column ? !ascending : true;
        sortColumn = column;
        head.querySelectorAll("th").forEach((cell, j) => {
          cell.setAttribute("aria-sort", j === column ? (ascending ? "ascending" : "descending") : "none");
          const control = cell.querySelector("button");
          if (control) control.textContent = t(headers[j]) + (j === column ? (ascending ? " ▲" : " ▼") : " ↕");
        });
        const sorted = [...records].sort((a, b) => {
          const av = numeric(a.row[column]), bv = numeric(b.row[column]);
          if (av === null || bv === null) return av === bv ? a.index - b.index : av === null ? 1 : -1;
          return (ascending ? av - bv : bv - av) || a.index - b.index;
        });
        body.replaceChildren(...sorted.map((r) => r.element));
      });
      b.textContent = t(h) + " ↕";
      b.title = t("숫자 오름차순 / 내림차순 정렬 (빈 값은 마지막)");
    }
    head.append(th);
  });
  tableElement.append(body);
  parent.append(tableElement);
  return tableElement;
}
function format(x) {
  return Number.isFinite(x)
    ? Math.abs(x) < 1e-5 && x !== 0
      ? x.toExponential(5)
      : x.toFixed(6).replace(/\.?0+$/, "")
    : String(x);
}
function download(name, text, type = "text/plain") {
  const a = node("a");
  a.href = URL.createObjectURL(new Blob([text], { type }));
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function csv(rows) {
  return rows
    .map((r) =>
      r.map((v) => '"' + String(v ?? "").replaceAll('"', '""') + '"').join(","),
    )
    .join("\n");
}
const inputDrafts = new Map(), buildDrafts = new Map();
let saveInputDraft = null;
function renderGaussianInput(parent) {
  if (!calc?.frames.length) return;
  const calculation = calc;
  const p = node("section", undefined, "gaussian-form");
  parent.append(p);
  p.id = "gaussianForm";
  p.append(node("h2", "Gaussian 16 · " + t("Gaussian 입력 생성")));
  const pages = [node("div"), node("div"), node("div")];
  pages.forEach((page, i) => {
    p.append(page);
    page.className = ["input-quick", "input-custom", "input-preview"][i];
    page.append(node("h3", ["간편 설정", "커스텀 설정", "입력 미리보기"][i]));
  });
  const values = { method:"B3LYP", basis:"def2SVP", job:"Opt Freq", memory:"4GB", cores:4, checkpoint:"gausslook.chk", scf:"XQC", grid:"UltraFine", dispersion:"None", solvent:"None", extra:"", route:"#p B3LYP/def2SVP Opt Freq", additional:"", override:false, charge:calculation.charge ?? 0, multiplicity:calculation.multiplicity ?? 1, title:calculation.name, ...inputDrafts.get(calculation.id) };
  const controls = {}, grid = node("div", undefined, "form-grid");
  pages[0].append(grid);
  const choices = {
    method:["HF", "B3LYP", "PBE1PBE", "M062X", "wB97XD", "MP2", "CCSD(T)"],
    basis:["def2SVP", "def2TZVP", "6-31G(d)", "6-311++G(d,p)", "cc-pVDZ", "Gen", "GenECP"],
    job:["SP", "Opt", "Freq", "Opt Freq", "Opt=(TS,CalcFC) Freq", "IRC=(CalcFC)", "TD(NStates=10)"],
    scf:["None", "XQC", "QC", "Tight", "VeryTight"],
    grid:["None", "UltraFine", "SuperFineGrid", "FineGrid"],
    dispersion:["None", "GD3", "GD3BJ"],
    solvent:["None", "Water", "Acetonitrile", "Toluene", "DMSO", "THF", "Chloroform", "Dichloromethane"],
  };
  for (const [key, label] of [["job","계산 종류"],["method","방법 / XC"],["basis","기저함수"],["charge","총전하"],["multiplicity","스핀 다중도"],["cores","CPU %NProcShared"],["memory","메모리 %Mem"],["checkpoint","체크포인트 %Chk"],["title","제목"],["scf","SCF 보조"],["grid","수치 적분격자"],["dispersion","분산 보정"],["solvent","용매 (SMD)"]]) {
    controls[key] = choices[key] ? select(grid, label, choices[key].map((v)=>[v,v]), values[key]) : field(grid, label, values[key], ["charge","multiplicity","cores"].includes(key) ? "number" : "text");
    controls[key].id = "input_" + key;
  }
  controls.cores.min = 1; controls.cores.max = 4096;
  controls.multiplicity.min = 1;
  [controls.charge, controls.multiplicity, controls.cores].forEach((control) => { control.step = 1; });
  note(pages[0], ui("타임라인에서 선택한 frame으로 생성합니다.", "Input uses the frame selected in the timeline."));
  controls.extra = field(pages[1], "추가 route 키워드", values.extra);
  controls.override = field(pages[1], "route 직접 입력", "", "checkbox");
  controls.override.checked = values.override;
  controls.route = field(pages[1], "Route", values.route);
  controls.route.disabled = !controls.override.checked;
  controls.override.onchange = () => { controls.route.disabled = !controls.override.checked; };
  const additionalLabel = node("label", t("외부 기저 / ECP / 추가 입력"), "field");
  controls.additional = node("textarea");
  controls.additional.value = values.additional;
  additionalLabel.append(controls.additional);
  pages[1].append(additionalLabel);
  note(pages[1], "Gen / GenECP 사용 시 검증한 기저 / ECP 블록을 직접 입력하세요. 자동 ECP 추정은 하지 않습니다.");
  const preview = node("textarea", undefined, "gaussian-preview");
  preview.id = "inputPreview";
  preview.readOnly = true;
  preview.value = values.preview || "";
  preview.setAttribute("aria-label", t("입력 미리보기"));
  pages[2].append(preview);
  note(pages[2], "총전하와 다중도 및 Gen/ECP 블록을 확인하세요. Gaussian 실행이나 스케줄러 제출은 하지 않습니다.");
  const error = node("p", "", "note error");
  error.id = "inputError"; error.setAttribute("role", "alert"); p.append(error);
  function remember() {
    const v = Object.fromEntries(Object.entries(controls).map(([key, control]) => [key, control.type === "checkbox" ? control.checked : control.value]));
    inputDrafts.set(calculation.id, {...v, preview: preview.value});
    return v;
  }
  saveInputDraft = remember;
  Object.values(controls).forEach(control => control.addEventListener("input", remember));
  Object.values(controls).forEach(control => control.addEventListener("change", remember));
  function gather() {
    const v = remember();
    Object.keys(v).forEach(key => { if (typeof v[key] === "string") v[key] = v[key].trim(); });
    for (const key of ["charge","multiplicity","cores"]) {
      if (v[key] === "" || !Number.isInteger(Number(v[key]))) throw Error(ui("전하·다중도·CPU는 정수로 입력하세요.", "Charge, multiplicity and CPU cores must be integers."));
      v[key] = Number(v[key]);
    }
    const parts = ["#p", v.method + "/" + v.basis, v.job === "SP" ? "" : v.job];
    for (const [key, pattern] of [["scf","SCF="],["grid","Integral="],["dispersion","EmpiricalDispersion="]]) {
      if (v[key] !== "None" && (key !== "grid" || !["HF","MP2","CCSD(T)"].includes(v.method))) parts.push(pattern + v[key]);
    }
    if (v.solvent !== "None") parts.push(`SCRF=(SMD,Solvent=${v.solvent})`);
    parts.push(v.extra);
    const route = v.override ? v.route : parts.filter(Boolean).join(" ");
    return { route, charge:v.charge, multiplicity:v.multiplicity, cores:v.cores, memory:v.memory, checkpoint:v.checkpoint, title:v.title, additional:v.additional, frame };
  }
  async function generate() {
    error.textContent = "";
    try {
      const result = await api("/api/action", {action:"input", id:calculation.id, ...gather()});
      preview.value = result.text;
      remember();
      return result.text;
    } catch (e) { error.textContent = t(e.message); throw e; }
  }
  const actions = node("div", undefined, "dialog-actions"); p.append(actions);
  button(actions, "입력 생성 / 갱신", generate).id = "generateInput";
  button(actions, ".gjf 다운로드", async () => download("gausslook.gjf", await generate())).id = "downloadInput";
}
async function refresh() {
  state = await api("/api/state");
  const list = $("jobs");
  list.replaceChildren();
  for (const c of state.calculations) {
    const item = node(
      "div",
      undefined,
      "job" + (calc && c.id === calc.id ? " active" : ""),
    );
    item.append(
      node("b", c.name),
      node("small", `${c.kind} · ${c.atoms} atoms · ${c.frames} frames`),
    );
    item.onclick = () => load(c.id).catch((e) => status(e.message, true));
    list.append(item);
  }
}
async function load(id) {
  stop();
  calc = await api("/api/calculation/" + id);
  frame = Math.max(0, calc.frames.length - 1);
  modeIndex = null;
  activeMO = null;
  activePolar = null;
  clearShapes();
  selected = [];
  meshes = [];
  $("frame").max = Math.max(0, calc.frames.length - 1);
  $("frame").value = frame;
  await refresh();
  draw(true);
  renderPanel();
  pathPlot();
  status(
    calc.properties.demo
      ? "DEMO · 화면 시연용 합성 자료. 실제 Gaussian 결과가 아닙니다."
      : calc.name + " · " + calc.status.termination,
  );
}
async function result(d) {
  if (d.task) return poll(d.task);
  await refresh();
  if (d.orbital_surface) {
    if (calc?.id !== d.calculation_id) return d;
    stop();
    frame = calc.frames.length - 1;
    $("frame").value = frame;
    clearShapes();
    draw(false, d.reference_coords);
    d.meshes.forEach(addMesh);
    requestViewerRender();
    status(`MO ${d.orbital} / ${d.spin} · ` + ui("±위상 표면 (파랑 + / 분홍 −)", "± phase surfaces (blue + / pink −)"));
    return d;
  }
  if (d.ids?.length) await load(d.ids[0]);
  return d;
}
async function poll(id) {
  interruptAnimation();
  currentTask = id;
  status("작업 진행 중…");
  try {
    for (;;) {
      const t = await api("/api/task/" + id);
      status(`${t.title} · ${t.status} · ${t.progress}%`);
      if (t.status === "done") {
        await result(t.result);
        if (t.output) console.info(t.output);
        return t.result;
      }
      if (["error", "cancelled"].includes(t.status))
        throw Error(t.error || "작업 취소");
      await new Promise((r) => setTimeout(r, 600));
    }
  } finally {
    if (currentTask === id) currentTask = null;
  }
}
async function action(name, p = {}) {
  return api("/api/action", { action: name, id: calc?.id, ...p });
}
function xyz(coords) {
  return (
    `${calc.atoms.length}\nGaussLook\n` +
    calc.atoms
      .map((z, i) => `${elements[z] || "X"} ${coords[i].join(" ")}`)
      .join("\n")
  );
}
const elements =
  "X H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og".split(
    " ",
  );
let renderRequest = null;
function requestViewerRender() {
  if (!viewer || renderRequest !== null) return;
  renderRequest = requestAnimationFrame(() => { renderRequest = null; viewer.render(); });
}
function draw(reset = false, coords = null) {
  if (!viewer || !calc?.frames.length) return;
  const key = calc.id + ":" + frame;
  if (key !== renderedFrameKey) {
    clearShapes();
    renderedFrameKey = key;
  }
  const cam = reset ? null : viewer.getView();
  if (model && !reset && key === model.frameKey && coords && model.setCoordinates) {
    // Mode displacements keep topology; reuse bonds instead of reparsing XYZ.
    model.setCoordinates(coords, "array");
    model.setFrame(0);
    if (settings.labels) applyStyle();
  } else if (!model || reset || key !== model.frameKey || coords) {
    viewer.removeAllModels();
    model = viewer.addModel(xyz(coords || calc.frames[frame].coords), "xyz");
    model.frameKey = key;
    model.setClickable({}, true, (a) => {
      const i = a.index;
      if (selected.includes(i)) selected = selected.filter((v) => v !== i);
      else selected.push(i);
      applyStyle();
      showSelection();
    });
    applyStyle();
  } else {
    model.setCoordinates?.(calc.frames[frame].coords, "array");
    model.setFrame?.(0);
    if (settings.labels) applyStyle();
  }
  if (reset) fitView();
  else viewer.setView(cam);
  requestViewerRender();
  $("frameLabel").textContent = `${frame + 1} / ${calc.frames.length}`;
  if (!coords) updateForcePanel().catch((e) => status(e.message, true));
}
function fitView() {
  if (!viewer) return;
  viewer.zoomTo();
  const coords = calc?.frames[frame]?.coords || [];
  const span = coords.length ? Math.max(...[0,1,2].map(axis => Math.max(...coords.map(p=>p[axis])) - Math.min(...coords.map(p=>p[axis])))) : 0;
  if (coords.length && span < 5) viewer.zoom?.(1.8);
  requestViewerRender();
}
function applyStyle() {
  if (!model) return;
  const atomScale = Math.min(0.8, Math.max(0.1, Number(settings.atomScale) || 0.3));
  const bondRadius = Math.min(0.4, Math.max(0.04, Number(settings.bondRadius) || 0.14));
  const colorfunc = (a) => settings.elementColors?.[a.elem] || $3Dmol.elementColors?.defaultColors?.[a.elem] || "#8eb8cf";
  let st =
    settings.style === "sphere"
      ? { sphere: { scale: Math.min(1.5, atomScale * 2.8), colorfunc } }
      : settings.style === "line"
        ? { line: { linewidth: 2, colorfunc } }
        : settings.style === "stick"
          ? { stick: { radius: bondRadius, colorfunc } }
          : { stick: { radius: bondRadius, colorfunc }, sphere: { scale: atomScale, colorfunc } };
  model.setStyle({}, st);
  if (selected.length)
    model.setStyle(
      { index: selected },
      {
        sphere: { scale: atomScale * 1.18, color: settings.selection },
        stick: { radius: bondRadius * 1.18, color: settings.selection },
      },
    );
  if (!$("hydrogens").checked) model.setStyle({ elem: "H" }, { sphere: { hidden: true }, stick: { hidden: true }, line: { hidden: true } });
  viewer.removeAllLabels();
  if ($("labels").checked)
    model.selectedAtoms({}).forEach((a, i) =>
      $("hydrogens").checked || a.elem !== "H" ? viewer.addLabel(`${a.index + 1} ${a.elem}`, {
        position: a,
        fontSize: settings.labelSize,
        fontColor: settings.labelColor,
        backgroundColor: settings.background,
        backgroundOpacity: 0.65,
        borderThickness: 0,
      }) : null,
    );
  requestViewerRender();
}
async function showSelection() {
  $("selection").textContent = selected.map((i) => i + 1).join(", ");
  if (selected.length >= 2 && selected.length <= 4) {
    try {
      const d = await action("measure", { indices: selected, frame });
      $("selection").textContent += ` · ${d.value.toFixed(4)} ${d.unit}`;
    } catch (e) {
      status(e.message, true);
    }
  }
}
function stop() {
  if (timer) clearInterval(timer);
  timer = null;
  $("play").textContent = t("▶ 경로");
}
function interruptAnimation() {
  if (timer) {
    stop();
    clearShapes();
    if (calc?.frames.length) draw(false, calc.frames[frame].coords);
  }
}
function animateMode(index, amp = modeAmplitude) {
  stop();
  const m = calc.modes[index];
  if (m.displacements?.length !== calc.atoms.length)
    throw Error("변위 데이터가 없습니다.");
  modeIndex = index;
  modeAmplitude = amp;
  frame = m.reference_frame ?? calc.frames.length - 1;
  $("frame").value = frame;
  clearShapes();
  const base = calc.frames[frame].coords;
  let tick = 0;
  timer = setInterval(() => {
    const s = amp * Math.sin(tick++ * 0.2 * modeSpeed),
      coords = base.map((v, i) =>
        v.map((x, j) => x + s * m.displacements[i][j]),
      );
    draw(false, coords);
    if (modeVectors) drawVectors(coords, m.displacements);
  }, 70);
  status(`${m.frequency_cm1} cm-1 · ` + ui("시각화용 진동 변위 (실제 시간축 아님)", "visualized mode displacement (not physical time)"));
}
function renderPanel() {
  const panel = $("panel");
  saveInputDraft?.();
  saveInputDraft = null;
  document.querySelector("main").classList.toggle("input-workspace", tab === "구조·입력");
  panel.replaceChildren();
  $("tabs").replaceChildren();
  tabs.forEach((t) => {
    const b = button($("tabs"), t, () => {
      tab = t;
      renderPanel();
    });
    if (t === tab) b.className = "active";
  });
  if (tab === "도움말") {
    renderHelp(panel);
    return;
  }
  if (!calc) {
    note(panel, "파일을 열면 구조와 분석 항목을 표시합니다.");
    if (tab === "지원 범위") showCatalog(panel);
    return;
  }
  panel.append(node("h2", tab));
  const p = calc.properties;
  if (tab === "개요") {
    for (const [k, v] of [
      ["선택 결과", calc.name],
      ["계산 유형", calc.kind],
      [
        "전하 / 다중도",
        `${calc.charge ?? t("미확인")} / ${calc.multiplicity ?? t("미확인")}`,
      ],
      ["원자 / 프레임", `${calc.atoms.length} / ${calc.frames.length}`],
    ])
      note(panel, `${t(k)}: ${v}`);
    const e = calc.energies.at(-1);
    if (e) {
      const card = node("div", undefined, "card");
      card.append(
        node("small", e.kind + " · Hartree"),
        node("br"),
        node("strong", e.hartree.toFixed(12)),
      );
      panel.append(card);
    }
    note(panel, calc.route || "계산 조건 없음");
    for (const w of calc.warnings) note(panel, "• " + t(w));
    panel.append(node("h3", "에너지 레코드"));
    table(
      panel,
      ["종류", "Hartree", "원문 행"],
      calc.energies
        .slice(-150)
        .map((e) => [e.kind, e.hartree.toFixed(12), e.line]),
    );
    button(panel, "분석 JSON 저장", () =>
      download(
        "analysis.json",
        JSON.stringify(calc, null, 2),
        "application/json",
      ),
    );
    button(panel, "HTML 보고서", report);
  }
  if (tab === "수렴·TS") {
    table(
      panel,
      ["항목", "상태", "근거/조건"],
      calc.quality.checks.map((q) => [t(q.check), q.status, t(q.detail)]),
    );
    panel.append(node("h3", "최적화 기준 (마지막 4개)"));
    table(
      panel,
      ["항목", "값", "임계값", "판정"],
      calc.convergence
        .slice(-4)
        .map((v) => [v.item, v.value, v.threshold, v.passed ? "YES" : "NO"]),
    );
    note(
      panel,
      "imaginary mode 1개는 TS 후보입니다. 모드 움직임과 양방향 IRC 끝점 연결을 확인하세요.",
    );
    button(panel, "첫 imaginary mode 재생", () => {
      const i = calc.modes.findIndex((m) => m.frequency_cm1 < 0);
      if (i < 0) throw Error("허수 모드를 찾지 못했습니다.");
      animateMode(i);
    });
  }
  if (tab === "진동·분광") renderVibrations(panel);
  if (tab === "MO·표면") renderMO(panel);
  if (tab === "에너지·Force") renderForces(panel);
  if (tab === "분극률") renderPolar(panel);
  if (tab === "물성") {
    for (const [k, v] of Object.entries(p)) {
      if (["field_id", "input_original"].includes(k)) continue;
      panel.append(node("h3", k));
      if (k === "charges") {
        for (const [type, vals] of Object.entries(v)) {
          note(panel, type);
          table(
            panel,
            ["Atom", "Charge"],
            vals.map((x, i) => [`${i + 1} ${elements[calc.atoms[i]]}`, x]),
            (i) => {
              selected = [i];
              applyStyle();
              showSelection();
            },
          );
        }
      } else panel.append(node("pre", JSON.stringify(v, null, 2)));
    }
    note(panel, "분자 분극률은 고분자의 1 GHz 복소 유전율과 다릅니다.");
  }
  if (tab === "경로") {
    note(
      panel,
      "구조 순서와 해당 frame의 에너지를 연결합니다. IRC/scan의 물리적 축이 별도로 추출되지 않은 경우 frame 번호를 사용합니다.",
    );
    button(panel, "에너지 경로 그리기", pathPlot);
    table(
      panel,
      ["Frame", "Hartree", "원문 행"],
      calc.frames.map((f, i) => [i + 1, f.energy_hartree, f.line]),
      (i) => {
        stop();
        frame = i;
        $("frame").value = i;
        draw();
      },
    );
  }
  if (tab === "비교·열화학") {
    button(panel, "전체 계산 조건 비교", async () => {
      const d = await action("compare");
      showObject(d);
    });
    panel.append(node("h3", "Gaussian 원래 열화학 (Hartree)"));
    table(panel, ["항목", "값"], Object.entries(calc.thermo));
    const cutoff = field(panel, "저주파 cutoff (cm-1)", 100, "number"),
      tm = select(panel, "엔트로피 보정 모델", [
        ["truhlar", "Truhlar floor"],
        ["grimme", "Grimme free rotor interpolation"],
      ]),
      conc = field(panel, "표준 농도 (mol/L, 빈칸=변경 없음)", "");
    button(panel, "별도 보정 결과", async () =>
      showObject(
        await action("thermo", {
          cutoff: +cutoff.value,
          model: tm.value,
          concentration: conc.value ? +conc.value : null,
        }),
      ),
    );
    note(
      panel,
      "G만 별도로 보정하며 원본을 변경하지 않습니다. 다른 온도는 새로운 frequency/thermochemistry 분석이 필요합니다.",
    );
    const other = select(
      panel,
      "구조 정렬 대상",
      state.calculations
        .filter((v) => v.id !== calc.id)
        .map((v) => [v.id, v.name]),
    );
    button(panel, "RMSD 정렬 검사", async () =>
      showObject(await action("align", { other_id: other.value })),
    );
  }
  if (tab === "구조·입력") {
    renderGaussianInput(panel);
    const draft = buildDrafts.get(calc.id) || {smiles:"c1ccccc1", vector:"0,0,1"};
    buildDrafts.set(calc.id, draft);
    const smiles = field(panel, "SMILES", draft.smiles);
    smiles.id = "buildSmiles";
    smiles.oninput = () => { draft.smiles = smiles.value; };
    button(panel, "3D conformer 생성", async () =>
      result(await action("smiles", { smiles: smiles.value })),
    );
    note(panel, "RDKit 필요. 힘장 구조 생성 후 Gaussian 최적화를 수행하세요.");
    button(panel, "선택 원자 삭제 → 새 구조", async () => {
      if (!selected.length) throw Error("원자를 먼저 선택하세요.");
      await result(
        await action("edit", { operation: "delete", indices: selected, frame }),
      );
    });
    const vector = field(panel, "선택 원자 이동 dx,dy,dz (Å)", draft.vector);
    vector.id = "buildVector";
    vector.oninput = () => { draft.vector = vector.value; };
    button(panel, "선택 원자 이동 → 새 구조", async () =>
      result(
        await action("edit", {
          operation: "translate",
          indices: selected,
          vector: vector.value.split(",").map(Number),
          frame,
        }),
      ),
    );
    note(
      panel,
      "편집 구조는 새 항목으로 생성하며 예전 계산 결과를 이어 붙이지 않습니다. 원본으로 돌아가면 이전 구조가 유지됩니다.",
    );
  }
  if (tab === "도구") {
    panel.append(node("h3", "Gaussian utilities"));
    table(
      panel,
      ["도구", "경로"],
      Object.entries(state.utilities || {}).map(([k, v]) => [k, v || t("미설치")]),
    );
    button(panel, "원본 출력 첫 500행", async () =>
      showObject(await action("source")),
    );
    const line = field(panel, "원문 시작 행", 1, "number");
    button(panel, "원문 구간 보기", async () => {
      const d = await action("source", { start_line: +line.value });
      showObject(d);
    });
    const masses = field(panel, "동위원소 질량 amu (모든 원자, 쉼표 구분)", "");
    button(panel, "Hessian 동위원소 재분석", async () =>
      result(
        await action("isotope", {
          masses: masses.value.split(",").map(Number),
        }),
      ),
    );
    panel.append(node("h3", "고급 공통 분석 API"));
    note(
      panel,
      "cube 매핑·단면·격자 연산·반응 에너지 등을 JSON으로 요청할 수 있습니다. 사용법은 README 및 docs/API.md 참조.",
    );
    const req = node("textarea");
    req.value = JSON.stringify(
      {
        action: "field_info",
        field_id: p.field_id || Object.keys(state.fields || {})[0] || "",
      },
      null,
      2,
    );
    panel.append(req);
    button(panel, "분석 실행", async () => {
      const args = JSON.parse(req.value),
        name = args.action;
      delete args.action;
      const d = await action(name, args);
      if (d.task) await result(d);
      else showObject(d);
    });
    table(
      panel,
      ["기능", "가용성", "조건"],
      calc.capabilities.map((v) => [
        t(v.feature),
        t(v.available ? "가능" : "데이터/연동 필요"),
        t(v.reason),
      ]),
    );
  }
  if (tab === "지원 범위") showCatalog(panel);
}
function displace(a) {
  if (modeIndex === null) throw Error("진동 모드를 먼저 선택하세요.");
  const m = calc.modes[modeIndex],
    coords = calc.frames[
      m.reference_frame ?? calc.frames.length - 1
    ].coords.map((v, i) => v.map((x, j) => x + a * m.displacements[i][j]));
  download("mode-displacement.xyz", xyz(coords));
}
function showObject(o) {
  $("modalBody").replaceChildren(
    node("h2", "분석 결과"),
    node("pre", typeof o === "string" ? o : JSON.stringify(o, null, 2)),
  );
  button($("modalBody"), "JSON 저장", () =>
    download("result.json", JSON.stringify(o, null, 2)),
  );
  $("modal").showModal();
}
async function showCatalog(panel) {
  const d = await api("/api/catalog");
  note(
    panel,
    "기획서 140개 항목의 구현 상태입니다. 조건부/부분/후속 구현 항목을 완전 지원으로 표시하지 않습니다.",
  );
  table(
    panel,
    ["ID", "기능", "상태"],
    d.map((v) => [v.id, settings.language === "en" ? v.feature_en || v.feature : v.feature, t(v.status)]),
  );
}
function pathPlot() {
  if (!calc) return;
  const rows = calc.frames
    .map((v, i) => ({ x: i + 1, y: v.energy_hartree, index: i }))
    .filter((v) => v.y !== null && v.y !== undefined);
  plotData = {
    kind: "Energy path",
    x: rows.map((v) => v.x),
    y: rows.map((v) => v.y),
    sticks: rows,
    x_unit: "frame",
    y_unit: "Hartree",
  };
  plot();
}
function plot() {
  const cv = $("plot"),
    r = cv.getBoundingClientRect(),
    dpr = window.devicePixelRatio || 1;
  cv.width = r.width * dpr;
  cv.height = r.height * dpr;
  const ctx = cv.getContext("2d");
  ctx.scale(dpr, dpr);
  const w = r.width,
    h = r.height;
  ctx.fillStyle = settings.background;
  ctx.fillRect(0, 0, w, h);
  if (!plotData?.x.length) {
    $("plotTitle").textContent = t("계산 경로 / 스펙트럼");
    ctx.fillStyle = settings.theme === "light" ? "#52677e" : "#94a9c0";
    ctx.fillText(t("스펙트럼 또는 경로를 선택하세요."), 40, 50);
    return;
  }
  const xs = plotData.x,
    ys = plotData.y;
  let xmin = Math.min(...xs),
    xmax = Math.max(...xs),
    ymin = Math.min(...ys),
    ymax = Math.max(...ys);
  if (xmin === xmax) {
    xmin -= 1;
    xmax += 1;
  }
  if (ymin === ymax) {
    ymin -= 1;
    ymax += 1;
  }
  const X = (x) => 45 + ((x - xmin) / (xmax - xmin)) * (w - 62),
    Y = (y) => h - 32 - ((y - ymin) / (ymax - ymin)) * (h - 49);
  ctx.strokeStyle = settings.theme === "light" ? "#c8d4e1" : "#344b66";
  ctx.strokeRect(45, 16, w - 62, h - 48);
  ctx.strokeStyle = settings.theme === "light" ? "#087d82" : "#57d1c9";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  xs.forEach((x, i) => {
    if (i === 0) ctx.moveTo(X(x), Y(ys[i]));
    else ctx.lineTo(X(x), Y(ys[i]));
  });
  ctx.stroke();
  ctx.fillStyle = settings.theme === "light" ? "#52677e" : "#94a9c0";
  ctx.font = "11px Arial";
  ctx.fillText(format(ymax), 2, 20);
  ctx.fillText(format(ymin), 2, h - 33);
  ctx.fillText(format(xmin), 45, h - 13);
  ctx.fillText(format(xmax), w - 60, h - 13);
  $("plotTitle").textContent =
    `${plotData.kind} · ${plotData.x_unit} / ${plotData.y_unit}`;
  cv.onclick = (event) => {
    const x = xmin + ((event.offsetX - 45) / (w - 62)) * (xmax - xmin);
    let nearest = null;
    for (const s of plotData.sticks || [])
      if (!nearest || Math.abs(s.x - x) < Math.abs(nearest.x - x)) nearest = s;
    if (nearest) {
      if (plotData.kind === "Energy path") {
        stop();
        frame = nearest.index;
        $("frame").value = frame;
        draw();
      } else if (["IR", "RAMAN", "VCD"].includes(plotData.kind))
        animateMode(nearest.index);
      status(`${plotData.kind}: ${nearest.x} ${plotData.x_unit}, ${nearest.y}`);
    }
  };
}
function report() {
  const data = JSON.stringify(calc, null, 2);
  download(
    "GaussLook-report.html",
    '<!doctype html><meta charset="utf-8"><title>GaussLook analysis</title><style>body{font:14px Arial;max-width:1000px;margin:40px auto;white-space:pre-wrap}</style><h1>GaussLook analysis snapshot</h1><pre>' +
      data.replaceAll("&", "&amp;").replaceAll("<", "&lt;") +
      "</pre>",
    "text/html",
  );
}
$("uploadBtn").onclick = () => { interruptAnimation(); $("upload").click(); };
$("upload").onchange = async (event) => {
  for (const file of event.target.files) {
    try {
      status(file.name + ui(" 읽는 중…", " · Reading…"));
      const data = new Uint8Array(await file.arrayBuffer());
      let binary = "";
      for (let i = 0; i < data.length; i += 32768)
        binary += String.fromCharCode(...data.subarray(i, i + 32768));
      await result(
        await api("/api/upload", { name: file.name, base64: btoa(binary) }),
      );
    } catch (e) {
      status(e.message, true);
    }
  }
  event.target.value = "";
};
$("demoBtn").onclick = () =>
  api("/api/demo", {})
    .then(result)
    .catch((e) => status(e.message, true));
$("refreshBtn").onclick = async () => {
  try {
    if (calc) await result(await action("reload_source"));
    else await refresh();
  } catch (e) {
    status(e.message, true);
  }
};
$("projectBtn").onclick = async () =>
  download(
    "GaussLook.glproj",
    JSON.stringify(await api("/api/project"), null, 2),
    "application/json",
  );
$("closeModal").onclick = () => $("modal").close();
$("center").onclick = fitView;
$("labels").checked = settings.labels;
$("style").value = settings.style;
$("cancelBtn").onclick = () => {
  if (currentTask)
    api("/api/cancel", { task: currentTask }).catch((e) =>
      status(e.message, true),
    );
  else status("현재 추적 중인 분석 작업이 없습니다.");
};
$("style").onchange = () => {
  settings.style = $("style").value;
  applyStyle();
  localStorage.setItem("gausslook.settings", JSON.stringify(settings));
};
$("labels").onchange = () => {
  settings.labels = $("labels").checked;
  applyStyle();
  localStorage.setItem("gausslook.settings", JSON.stringify(settings));
};
$("hydrogens").checked = settings.hydrogens;
$("hydrogens").onchange = () => { settings.hydrogens = $("hydrogens").checked; applyStyle(); saveSettings(); };
$("clearSelection").onclick = () => {
  selected = [];
  applyStyle();
  showSelection();
};
$("frame").oninput = () => {
  stop();
  frame = +$("frame").value;
  clearShapes();
  draw();
};
$("play").onclick = () => {
  if (timer) {
    stop();
    return;
  }
  if (!calc) return;
  timer = setInterval(() => {
    frame = (frame + 1) % calc.frames.length;
    $("frame").value = frame;
    draw();
  }, 160);
  $("play").textContent = t("■ 정지");
};
$("xyzBtn").onclick = async () => {
  try {
    const d = await action("xyz", { frame });
    download(d.filename, d.text);
  } catch (e) {
    status(e.message, true);
  }
};
$("snapshot").onclick = () => {
  if (!viewer) return;
  const a = node("a");
  a.href = viewer.pngURI();
  a.download = "GaussLook.png";
  a.click();
};
$("plotCsv").onclick = () => {
  if (plotData)
    download(
      "spectrum.csv",
      csv([
        ["x (" + plotData.x_unit + ")", "y (" + plotData.y_unit + ")"],
        ...plotData.x.map((x, i) => [x, plotData.y[i]]),
      ]),
      "text/csv",
    );
};
$("plotSvg").onclick = () => {
  if (!plotData?.x.length) return;
  const x = plotData.x,
    y = plotData.y,
    xmin = Math.min(...x),
    xmax = Math.max(...x),
    ymin = Math.min(...y),
    ymax = Math.max(...y);
  const pts = x
    .map(
      (v, i) =>
        `${40 + ((v - xmin) / (xmax - xmin || 1)) * 820},${350 - ((y[i] - ymin) / (ymax - ymin || 1)) * 310}`,
    )
    .join(" ");
  download(
    "plot.svg",
    `<svg xmlns="http://www.w3.org/2000/svg" width="900" height="400"><rect width="100%" height="100%" fill="white"/><polyline fill="none" stroke="#126a8d" stroke-width="1.5" points="${pts}"/></svg>`,
    "image/svg+xml",
  );
};
$("browseBtn").onclick = () => browse("").catch((e) => status(e.message, true));
async function browse(path) {
  interruptAnimation();
  const d = await api("/api/browse?path=" + encodeURIComponent(path));
  const root = $("modalBody");
  root.className = "";
  root.replaceChildren(node("h2", "서버 폴더"));
  const row = node("div", undefined, "path-row");
  root.append(row);
  const pathInput = field(row, "서버 디렉터리 경로", d.absolute_path || d.path || ".");
  pathInput.id = "browsePath";
  pathInput.autocomplete = "off";
  pathInput.spellcheck = false;
  const go = () => browse(pathInput.value.trim()).catch((e) => status(e.message, true));
  button(row, "이동", go).id = "browseGo";
  pathInput.onkeydown = (event) => { if (event.key === "Enter") { event.preventDefault(); go(); } };
  note(root, "경로를 입력하거나 붙여넣고 Enter를 누르세요. 서버의 허용된 루트 안에서 탐색합니다.");
  const parent = Object.prototype.hasOwnProperty.call(d, "parent") ? d.parent : d.path && d.path !== "." ? d.path.replace(/\\/g, "/").split("/").slice(0,-1).join("/") : null;
  if (parent !== null) button(root, "상위 폴더", () => browse(parent));
  const entries = parent !== null ? [{ name: "..", directory: true, path: parent }, ...d.entries] : d.entries;
  const listing = table(
    root,
    ["이름", "종류", "크기"],
    entries.map((v) => [v.name, v.directory ? "▸ " + t("폴더") : (v.name.match(/\.([^.]+)$/)?.[1] || t("파일")).toUpperCase(), v.directory ? "—" : v.size + " bytes"]),
    async (i) => {
      const v = entries[i];
      try {
        if (v.directory) await browse(v.path);
        else {
          $("modal").close();
          await result(await api("/api/open", { path: v.path }));
        }
      } catch (e) {
        status(e.message, true);
      }
    },
  );
  listing.classList.add("file-browser");
  [...listing.querySelectorAll("tbody tr")].forEach((row, i) => {
    row.classList.add(entries[i].directory ? "file-folder" : "file-" + (entries[i].name.match(/\.([^.]+)$/)?.[1] || "other").toLowerCase().replace(/[^a-z0-9_-]/g, "_"));
    row.tabIndex = 0;
    row.onkeydown = event => { if (event.key === "Enter") row.click(); };
  });
  if (!$("modal").open) $("modal").showModal();
}
function saveSettings() {
  try { localStorage.setItem("gausslook.settings", JSON.stringify(settings)); } catch (e) { /* Private browsing may disable persistence. */ }
}
function applyAppearance() {
  const root = document.documentElement;
  root.dataset.theme = settings.theme;
  root.lang = settings.language;
  const primary = settings.language === "ko" ? settings.fontKo : settings.fontEn;
  root.style.setProperty("--font", `${JSON.stringify(primary)},"Malgun Gothic","Gulim","Noto Sans CJK KR",Arial,sans-serif`);
  root.style.fontSize = Math.max(10, Math.min(24, Number(settings.fontSize) || 14)) + "px";
  root.style.setProperty("--viewer", settings.background);
  viewer?.setBackgroundColor(settings.background);
  requestViewerRender();
  $("language").value = settings.language;
  $("themeBtn").textContent = t(settings.theme === "dark" ? "☀ 라이트 모드" : "☾ 다크 모드");
  $("themeBtn").title = ui("다크 / 라이트 화면을 전환하고 저장합니다.", "Switch and save the dark / light theme.");
  $("labels").checked = settings.labels;
  $("hydrogens").checked = settings.hydrogens;
  $("style").value = settings.style;
  applyStyle();
  plot();
}
function applyLanguage() {
  const labels = { uploadBtn:"파일 열기", browseBtn:"서버 폴더", demoBtn:"데모", projectBtn:"프로젝트 저장", refreshBtn:"새로고침", cancelBtn:"작업 취소", settingsBtn:"설정", displayBtn:"화면 설정", helpBtn:"도움말", center:"중심", clearSelection:"선택 해제", xyzBtn:"XYZ 저장", closeModal:"닫기", snapshot:"PNG", plotCsv:"CSV", plotSvg:"SVG" };
  for (const [id, label] of Object.entries(labels)) {
    $(id).textContent = t(label);
    $(id).dataset.label = label;
    $(id).title = helpText(label);
  }
  $("language").title = t("언어를 선택합니다. 전문용어와 원본 계산 자료는 유지합니다.");
  $("displayBtn").title = t("화면 설정을 변경합니다.");
  document.querySelector(".section-title").textContent = t("프로젝트 탐색기");
  const aside = document.querySelector(".aside-note");
  aside.replaceChildren(node("span", ".log · .out · .chk · .fchk"), node("br"), node("span", ".cube · .gjf · .xyz · .sdf"), node("br"), node("br"), node("span", t("원본 계산 결과와 편집 구조를 구별합니다.")));
  $("labels").parentElement.replaceChildren($("labels"), document.createTextNode(t("번호")));
  $("labels").title = t("원자 번호 표시");
  $("hydrogens").title = t("수소 표시");
  const styleLabels = {ball:"Ball & stick",stick:"Sticks",line:"Wireframe",sphere:"Space filling"};
  [...$("style").options].forEach((option) => { option.textContent = t(styleLabels[option.value]); });
  $("viewer").title = t("드래그: 회전 · 휠: 확대 · 오른쪽 드래그: 이동 · 원자 클릭: 선택");
  $("play").textContent = t(timer ? "■ 정지" : "▶ 경로");
  $("play").title = helpText("▶ 경로");
  status(calc ? statusMessage : "파일을 열거나 데모를 선택하세요.", statusError);
  if (!plotData) $("plotTitle").textContent = t("계산 경로 / 스펙트럼");
}
function settingsDialog() {
  interruptAnimation();
  const p = $("modalBody");
  p.replaceChildren(node("h2", "표시 설정"));
  p.className = "display-settings";
  const appearance = node("div", undefined, "form-grid");
  p.append(appearance);
  const language = select(appearance, "언어", [["ko", "한국어"], ["en", "English"]], settings.language),
    theme = select(appearance, "테마", [["dark", "다크"], ["light", "라이트"]], settings.theme),
    fontKo = select(appearance, "한글 글꼴", [["Malgun Gothic", "맑은 고딕"], ["Gulim", "굴림"], ["Noto Sans CJK KR", "Noto Sans KR"]], settings.fontKo),
    fontEn = select(appearance, "영문 글꼴", [["Arial", "Arial"], ["Calibri", "Calibri"]], settings.fontEn),
    size = field(appearance, "글자 크기 px", settings.fontSize, "number");
  size.min = 10; size.max = 24; size.step = 1;
  p.append(node("h3", "구조 뷰어"));
  const view = node("div", undefined, "form-grid");
  p.append(view);
  const bg = field(view, "Viewer 배경", settings.background, "color"),
    selection = field(view, "선택 색상", settings.selection, "color"),
    atoms = field(view, "원자 크기", settings.atomScale, "number"),
    bonds = field(view, "결합 반지름 (Å)", settings.bondRadius, "number"),
    labelColor = field(view, "레이블 색상", settings.labelColor, "color"),
    labelSize = field(view, "레이블 크기 px", settings.labelSize, "number"),
    labels = field(view, "원자 번호 표시", "", "checkbox"),
    hydrogens = field(view, "수소 표시", "", "checkbox");
  labels.checked = settings.labels; hydrogens.checked = settings.hydrogens;
  atoms.min = 0.1; atoms.max = 0.8; atoms.step = 0.05;
  bonds.min = 0.04; bonds.max = 0.4; bonds.step = 0.01;
  labelSize.min = 8; labelSize.max = 24;
  theme.onchange = () => {
    bg.value = theme.value === "light" ? "#eef3f7" : "#101b2b";
    labelColor.value = theme.value === "light" ? "#203146" : "#f1f5fa";
  };
  p.append(node("h3", "원소별 색상"));
  const colors = node("div", undefined, "element-colors");
  p.append(colors);
  const elementFields = {};
  const symbols = new Set([...Object.keys(settings.elementColors), ...(calc?.atoms || []).map((z) => elements[z])]);
  for (const symbol of symbols) elementFields[symbol] = field(colors, symbol, settings.elementColors[symbol] || "#8eb8cf", "color");
  const actions = node("div", undefined, "dialog-actions");
  p.append(actions);
  button(actions, "적용 / 저장", () => {
    const ranges = [[size,10,24],[atoms,0.1,0.8],[bonds,0.04,0.4],[labelSize,8,24]];
    if (ranges.some(([control,min,max]) => !Number.isFinite(+control.value) || +control.value < min || +control.value > max)) throw Error(ui("표시 설정의 숫자 범위를 확인하세요.", "Check the numeric ranges in display settings."));
    if (!Number.isInteger(+size.value)) throw Error(ui("글자 크기는 정수로 입력하세요.", "Enter a whole-number font size."));
    Object.assign(settings, { language: language.value, theme: theme.value, fontKo: fontKo.value, fontEn: fontEn.value, fontSize:+size.value, background:bg.value, selection:selection.value, atomScale:+atoms.value, bondRadius:+bonds.value, labelColor:labelColor.value, labelSize:+labelSize.value, labels:labels.checked, hydrogens:hydrogens.checked, elementColors:Object.fromEntries(Object.entries(elementFields).map(([symbol,input])=>[symbol,input.value])) });
    saveSettings(); applyAppearance(); applyLanguage(); renderPanel();
    status("표시 설정을 저장했습니다.");
    $("modal").close();
  });
  button(actions, "기본값 복원", () => {
    const oldLanguage = settings.language;
    settings = JSON.parse(JSON.stringify(defaultSettings));
    settings.language = oldLanguage;
    saveSettings(); applyAppearance(); applyLanguage(); renderPanel(); settingsDialog();
  });
  if (!$("modal").open) $("modal").showModal();
}
$("settingsBtn").onclick = settingsDialog;
$("displayBtn").onclick = settingsDialog;
$("language").onchange = () => {
  interruptAnimation();
  settings.language = $("language").value; saveSettings(); applyLanguage(); applyAppearance(); renderPanel();
};
$("themeBtn").onclick = () => {
  settings.theme = settings.theme === "dark" ? "light" : "dark";
  settings.background = settings.theme === "light" ? "#eef3f7" : "#101b2b";
  settings.labelColor = settings.theme === "light" ? "#203146" : "#f1f5fa";
  saveSettings(); applyAppearance(); renderPanel();
};
let wheelRequest = null, latestWheel = null;
function wheelAge(event) {
  const stamp = event.timeStamp > 1e12 ? event.timeStamp - performance.timeOrigin : event.timeStamp;
  return performance.now() - stamp;
}
document.addEventListener("wheel", event => {
  if (wheelAge(event) > 120) { event.preventDefault(); event.stopImmediatePropagation(); }
}, {capture:true, passive:false});
$("viewer").addEventListener("wheel", event => {
  event.preventDefault();
  event.stopImmediatePropagation();
  latestWheel = {delta:event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? 300 : 1), time:performance.now()};
  if (wheelRequest !== null) return;
  wheelRequest = requestAnimationFrame(() => {
    wheelRequest = null;
    const wheel = latestWheel;
    latestWheel = null;
    if (!viewer || performance.now() - wheel.time > 120) return;
    viewer.zoom(Math.exp(-Math.max(-120, Math.min(120, wheel.delta)) / 600), 0);
    requestViewerRender();
  });
}, {capture:true, passive:false});
try {
  viewer = $3Dmol.createViewer("viewer", {
    backgroundColor: settings.background,
    antialias: true,
  });
  new ResizeObserver(() => {
    viewer.resize();
    requestViewerRender();
    plot();
  }).observe($("viewer"));
} catch (e) {
  status("WebGL 초기화 실패: " + e.message, true);
}
$("helpBtn").onclick = openHelp;
window.addEventListener("keydown", (e) => {
  if (e.key === "F1") {
    e.preventDefault();
    openHelp();
  }
});
Promise.all([
  refresh(),
  api("/api/help").then((d) => {
    helpData = d;
  }),
])
  .then(() => {
    applyLanguage();
    applyAppearance();
    applyHelpTitles();
    renderPanel();
    if (state.calculations.length) load(state.calculations[0].id);
  })
  .catch((e) => status(e.message, true));
