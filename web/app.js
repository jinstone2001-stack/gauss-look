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
  settings = { labels: false, style: "ball", background: "#101b2b" };
try {
  settings = {
    ...settings,
    ...JSON.parse(localStorage.getItem("gausslook.settings") || "{}"),
  };
} catch (e) {}
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
function node(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = String(text);
  if (cls) n.className = cls;
  return n;
}
function status(t, error = false) {
  $("status").textContent = t;
  $("status").classList.toggle("error", error);
}
async function api(path, body) {
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
  const b = node("button", label);
  b.title = helpText(label);
  b.onclick = async () => {
    try {
      await fn();
    } catch (e) {
      status(e.message, true);
    }
  };
  parent.append(b);
  return b;
}
function note(parent, text) {
  parent.append(node("p", text, "note"));
}
function field(parent, label, value, type = "text") {
  const l = node("label", label, "field"),
    v = node("input");
  v.type = type;
  v.value = value ?? "";
  l.append(v);
  parent.append(l);
  return v;
}
function select(parent, label, options, value) {
  const l = node("label", label, "field"),
    s = node("select");
  for (const [v, t] of options) s.append(new Option(t, v));
  if (value !== undefined) s.value = value;
  l.append(s);
  parent.append(l);
  return s;
}
function table(parent, headers, rows, onClick) {
  const t = node("table"),
    head = node("tr");
  headers.forEach((h) => head.append(node("th", h)));
  const thead = node("thead");
  thead.append(head);
  t.append(thead);
  const body = node("tbody");
  rows.forEach((row, i) => {
    const tr = node("tr");
    row.forEach((v) =>
      tr.append(node("td", typeof v === "number" ? format(v) : (v ?? "—"))),
    );
    if (onClick) {
      tr.className = "selectable";
      tr.onclick = () => onClick(i, tr);
    }
    body.append(tr);
  });
  t.append(body);
  parent.append(t);
  return t;
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
    viewer.render();
    status(`MO ${d.orbital} / ${d.spin} · ±위상 표면 (파랑 + / 분홍 −)`);
    return d;
  }
  if (d.ids?.length) await load(d.ids[0]);
  return d;
}
async function poll(id) {
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
function draw(reset = false, coords = null) {
  if (!viewer || !calc?.frames.length) return;
  const key = calc.id + ":" + frame;
  if (key !== renderedFrameKey) {
    clearShapes();
    renderedFrameKey = key;
  }
  const cam = reset ? null : viewer.getView();
  viewer.removeAllModels();
  viewer.removeAllLabels();
  model = viewer.addModel(xyz(coords || calc.frames[frame].coords), "xyz");
  applyStyle();
  model.setClickable({}, true, (a) => {
    const i = a.index;
    if (selected.includes(i)) selected = selected.filter((v) => v !== i);
    else selected.push(i);
    applyStyle();
    showSelection();
  });
  if (reset) viewer.zoomTo();
  else viewer.setView(cam);
  viewer.render();
  $("frameLabel").textContent = `${frame + 1} / ${calc.frames.length}`;
  if (!coords) updateForcePanel().catch((e) => status(e.message, true));
}
function applyStyle() {
  if (!model) return;
  let st =
    settings.style === "sphere"
      ? { sphere: { scale: 0.8 } }
      : settings.style === "line"
        ? { line: {} }
        : settings.style === "stick"
          ? { stick: { radius: 0.16 } }
          : { stick: { radius: 0.12 }, sphere: { scale: 0.25 } };
  model.setStyle({}, st);
  if (!$("hydrogens").checked) model.setStyle({ elem: "H" }, { hidden: true });
  if (selected.length)
    model.setStyle(
      { index: selected },
      {
        sphere: { scale: 0.34, color: "#57d1c9" },
        stick: { radius: 0.16, color: "#57d1c9" },
      },
    );
  viewer.removeAllLabels();
  if ($("labels").checked)
    model.selectedAtoms({}).forEach((a, i) =>
      viewer.addLabel(`${i + 1} ${a.elem}`, {
        position: a,
        fontSize: 11,
        backgroundOpacity: 0.4,
      }),
    );
  viewer.render();
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
  $("play").textContent = "▶ 경로";
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
  status(`${m.frequency_cm1} cm-1 · 시각화용 진동 변위 (실제 시간축 아님)`);
}
function renderPanel() {
  const panel = $("panel");
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
        `${calc.charge ?? "미확인"} / ${calc.multiplicity ?? "미확인"}`,
      ],
      ["원자 / 프레임", `${calc.atoms.length} / ${calc.frames.length}`],
    ])
      note(panel, `${k}: ${v}`);
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
    for (const w of calc.warnings) note(panel, "• " + w);
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
      calc.quality.checks.map((q) => [q.check, q.status, q.detail]),
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
    const smiles = field(panel, "SMILES", "c1ccccc1");
    button(panel, "3D conformer 생성", async () =>
      result(await action("smiles", { smiles: smiles.value })),
    );
    note(panel, "RDKit 필요. 힘장 구조 생성 후 Gaussian 최적화를 수행하세요.");
    const route = field(panel, "Gaussian route", "#p B3LYP/def2SVP Opt Freq"),
      q = field(panel, "Charge", calc.charge ?? 0, "number"),
      mult = field(panel, "Multiplicity", calc.multiplicity ?? 1, "number"),
      mem = field(panel, "Memory", "4GB"),
      cores = field(panel, "Cores", 4, "number"),
      add = node("textarea");
    add.placeholder = "사용자 추가 입력 (basis/ECP 등)";
    panel.append(add);
    button(panel, "Gaussian 입력 저장", async () => {
      const d = await action("input", {
        route: route.value,
        charge: +q.value,
        multiplicity: +mult.value,
        memory: mem.value,
        cores: +cores.value,
        additional: add.value,
        frame,
      });
      download(d.filename, d.text);
    });
    button(panel, "선택 원자 삭제 → 새 구조", async () => {
      if (!selected.length) throw Error("원자를 먼저 선택하세요.");
      await result(
        await action("edit", { operation: "delete", indices: selected, frame }),
      );
    });
    const vector = field(panel, "선택 원자 이동 dx,dy,dz (Å)", "0,0,1");
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
      Object.entries(state.utilities || {}).map(([k, v]) => [k, v || "미설치"]),
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
        v.feature,
        v.available ? "가능" : "데이터/연동 필요",
        v.reason,
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
    d.map((v) => [v.id, v.feature, v.status]),
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
  ctx.fillStyle = "#101b2b";
  ctx.fillRect(0, 0, w, h);
  if (!plotData?.x.length) {
    ctx.fillStyle = "#94a9c0";
    ctx.fillText("스펙트럼 또는 경로를 선택하세요.", 40, 50);
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
  ctx.strokeStyle = "#344b66";
  ctx.strokeRect(45, 16, w - 62, h - 48);
  ctx.strokeStyle = "#57d1c9";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  xs.forEach((x, i) => {
    if (i === 0) ctx.moveTo(X(x), Y(ys[i]));
    else ctx.lineTo(X(x), Y(ys[i]));
  });
  ctx.stroke();
  ctx.fillStyle = "#94a9c0";
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
$("uploadBtn").onclick = () => $("upload").click();
$("upload").onchange = async (event) => {
  for (const file of event.target.files) {
    try {
      status(file.name + " 읽는 중…");
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
$("center").onclick = () => {
  viewer?.zoomTo();
  viewer?.render();
};
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
$("hydrogens").onchange = applyStyle;
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
  $("play").textContent = "■ 정지";
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
  const d = await api("/api/browse?path=" + encodeURIComponent(path));
  const root = $("modalBody");
  root.replaceChildren(node("h2", "서버 폴더 / " + d.path));
  if (d.path && d.path !== ".")
    button(root, "상위 폴더", () =>
      browse(d.path.split("/").slice(0, -1).join("/")),
    );
  table(
    root,
    ["이름", "종류"],
    d.entries.map((v) => [v.name, v.directory ? "폴더" : v.size + " bytes"]),
    async (i) => {
      const v = d.entries[i];
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
  if (!$("modal").open) $("modal").showModal();
}
$("settingsBtn").onclick = () => {
  const p = $("modalBody");
  p.replaceChildren(node("h2", "표시 설정"));
  const font = select(p, "폰트", [
      ['Arial,"Malgun Gothic",sans-serif', "Arial / 맑은 고딕"],
      ['Calibri,"Gulim",sans-serif', "Calibri / 굴림"],
      ['"Noto Sans CJK KR",sans-serif', "Noto Sans KR"],
    ]),
    size = field(p, "글자 크기 px", 14, "number"),
    bg = field(p, "Viewer 배경", settings.background, "color");
  button(p, "적용", () => {
    document.documentElement.style.setProperty("--font", font.value);
    document.documentElement.style.fontSize = size.value + "px";
    settings.background = bg.value;
    viewer.setBackgroundColor(bg.value);
    viewer.render();
    localStorage.setItem("gausslook.settings", JSON.stringify(settings));
  });
  $("modal").showModal();
};
try {
  viewer = $3Dmol.createViewer("viewer", {
    backgroundColor: settings.background,
    antialias: true,
  });
  new ResizeObserver(() => {
    viewer.resize();
    viewer.render();
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
    applyHelpTitles();
    renderPanel();
    if (state.calculations.length) load(state.calculations[0].id);
  })
  .catch((e) => status(e.message, true));
