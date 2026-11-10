"use strict";
// Focused analysis UI. Numerical values are produced by the shared Python engine.
let helpData = { topics: [] },
  activeSpin = "alpha",
  activeMO = null,
  modeAmplitude = 0.5,
  modeSpeed = 1,
  modeVectors = false,
  forceVectors = false,
  vectorShapes = [],
  forceUnits = "Eh/Bohr",
  frameRequest = 0;
function helpText(label) {
  const control = helpData.controls?.find((c) => c.labels.includes(label));
  if (control) return control.summary_ko;
  const topic = helpData.topics.find((t) => t.buttons.includes(label));
  return (
    topic?.summary_ko ||
    `${label}: 자세한 조작·입력 조건은 도움말에서 확인하세요.`
  );
}
function applyHelpTitles() {
  document.querySelectorAll("button").forEach((b) => {
    if (!b.title) b.title = helpText(b.textContent.trim());
  });
}
function openHelp() {
  tab = "도움말";
  renderPanel();
}
function renderHelp(parent) {
  parent.append(node("h2", "GaussLook 도움말 · 1.1"));
  const search = field(
    parent,
    "버튼 이름 / HOMO / frequency / Force / 파일 확장자 검색",
    "",
  );
  search.placeholder = "예: Reload source, imaginary, polarizability";
  const list = node("div", undefined, "help-topics");
  parent.append(list);
  const content = node("article", undefined, "help-content");
  parent.append(content);
  function show(t) {
    content.replaceChildren(
      node("h3", t.title_ko),
      node("p", t.summary_ko),
      node("p", t.body_ko, "manual-body"),
    );
    content.append(
      node("h4", "관련 버튼"),
      node("p", t.buttons.join(" · "), "note"),
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
    topics.forEach((t) => button(list, t.title_ko, () => show(t)));
    if (topics.length) show(topics[0]);
    else note(content, "검색된 도움말이 없습니다.");
  }
  search.oninput = filter;
  filter();
}
function metric(parent, label, value) {
  const c = node("div", undefined, "metric");
  c.append(node("small", label), node("strong", value ?? "미출력"));
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
      .forEach((tr, i) =>
        tr.classList.toggle("selected", o.rows[i].mo === activeMO),
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
    item("text", { x: 5, y: 15, fill: "#a2b7ce", "font-size": 12 }, "eV");
    rows.forEach((r, i) => {
      const x = 48 + (i * 440) / Math.max(1, rows.length - 1),
        y = 146 - ((r.energy_eV - lo) / span) * 110,
        color =
          r.mo === activeMO ? "#57d1c9" : r.occupation ? "#65bafa" : "#f29eb0";
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
          fill: "#c5d3e4",
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
      viewer.render();
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
    viewer.render();
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
  viewer.render();
}
function renderVibrations(parent) {
  const modes = calc.modes,
    imag = modes.filter((m) => m.frequency_cm1 < 0);
  const c = node("div", undefined, imag.length ? "card imaginary" : "card");
  c.append(
    node(
      "strong",
      modes.length
        ? `${modes.length}개 모드 · imaginary ${imag.length}개`
        : "진동수 미계산 / 미출력",
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
      f.force_record !== undefined ? "출력됨" : "미출력",
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
  note(p, `${f.source} · 원문 행 ${f.line ?? "—"} · ${f.coordinate_system}`);
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
      data.default_index,
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
      "고유값 / a.u.: " + r.eigenvalues_au.map((v) => v.toFixed(8)).join(", "),
    );
    note(
      content,
      `${r.source} · 원문 행 ${r.line ?? "—"} · ${r.orientation ?? "as reported"} · W=${r.frequency_au ?? "미상"} a.u. ${r.frequency_au === 0 ? "(static)" : ""}`,
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
  source.onchange = show;
  show();
}
