/* DOM / API integration without pretending to test a real GPU renderer.
   NODE_PATH=/path/to/node_modules node tests/ui_dom.cjs URL
   The Python test launcher must keep the server in the same network namespace. */
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { JSDOM, VirtualConsole } = require("jsdom");
const base = process.argv[2];
const root = path.resolve(__dirname, "..");
const errors = [];
const consoleBridge = new VirtualConsole();
consoleBridge.on("jsdomError", (e) => errors.push(e.message));
const dom = new JSDOM(
  fs.readFileSync(path.join(root, "web/index.html"), "utf8"),
  {
    url: base,
    runScripts: "outside-only",
    pretendToBeVisual: true,
    virtualConsole: consoleBridge,
  },
);
const w = dom.window;
let lastInputFrame = null;
w.fetch = (url, opts) => {
  if (opts?.body) { const body = JSON.parse(opts.body); if (body.action === "input") lastInputFrame = body.frame; }
  return fetch(new URL(url, base), opts);
};
w.ResizeObserver = class {
  observe() {}
  disconnect() {}
};
w.HTMLCanvasElement.prototype.getContext = () =>
  new Proxy({}, { get: () => () => {}, set: () => true });
w.Element.prototype.getBoundingClientRect = () => ({
  width: 850,
  height: 250,
  x: 0,
  y: 0,
});
w.HTMLDialogElement.prototype.showModal = function () {
  this.open = true;
};
w.HTMLDialogElement.prototype.close = function () {
  this.open = false;
};
w.URL.createObjectURL = () => "blob:mock";
w.URL.revokeObjectURL = () => {};
let structures = 0, coordinateUpdates = 0, renders = 0, zooms = [],
  surfaces = 0;
const graphics = {
  getView: () => [],
  setView() {},
  render() { renders++; },
  zoom(factor) { zooms.push(factor); },
  resize() {},
  zoomTo() {},
  removeAllModels() {},
  removeAllLabels() {},
  removeAllShapes() {},
  removeShape() {},
  addArrow() {
    return {};
  },
  addLabel() {},
  setBackgroundColor() {},
  addModel(xyz) {
    structures++;
    const atoms = xyz
      .split("\n")
      .slice(2)
      .filter(Boolean)
      .map((line, i) => {
        const [elem, x, y, z] = line.split(/\s+/);
        return { elem, x: +x, y: +y, z: +z, index: i };
      });
    return {
      setStyle() {}, setClickable() {}, selectedAtoms: () => atoms,
      setCoordinates(coords) {
        coordinateUpdates++;
        coords.forEach((p, i) => { atoms[i].x=p[0]; atoms[i].y=p[1]; atoms[i].z=p[2]; });
      },
      setFrame() {},
    };
  },
  addCustom(mesh) {
    assert(mesh.vertexArr.length > 0);
    assert(mesh.faceArr.length > 0);
    assert(mesh.vertexArr.every((v) => Number.isFinite(v.x + v.y + v.z)));
    surfaces++;
    return mesh;
  },
};
w.$3Dmol = {
  createViewer: () => graphics,
  Vector3: class {
    constructor(x, y, z) {
      this.x = x;
      this.y = y;
      this.z = z;
    }
  },
};
w.addEventListener("error", (e) => errors.push(e.message));
w.localStorage.setItem("gausslook.settings", JSON.stringify({font:'Calibri,"Gulim",sans-serif', fontSize:"14.0"}));
w.eval(
  fs.readFileSync(path.join(root, "web/core.js"), "utf8") +
    "\n" +
    fs.readFileSync(path.join(root, "web/app.js"), "utf8") +
    "\nglobalThis.testTable = table; globalThis.testAction = action; globalThis.testAnimateMode = animateMode; globalThis.testTimer = () => timer;",
);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const click = (text) => {
  const button = [...w.document.querySelectorAll("button")].find(
    (v) => v.textContent === text,
  );
  assert(button, `button missing: ${text}`);
  button.click();
};
async function until(fn, attempts = 150) {
  for (let i = 0; i < attempts; i++) {
    if (fn()) return;
    await wait(30);
  }
  throw Error("DOM timeout");
}
(async () => {
  await until(
    () => w.document.querySelectorAll(".job").length === 1 && structures > 0,
  );
  assert(w.document.getElementById("demoBtn").title.includes("합성"));
  assert(w.document.getElementById("refreshBtn").title.includes("다시 분석"));
  click("MO·표면");
  await wait(30);
  assert(w.document.querySelector(".orbital-diagram svg"));
  click("LUMO");
  const moInput = [...w.document.querySelectorAll("label.field")]
    .find((l) => l.textContent.includes("선택 MO 번호"))
    .querySelector("input");
  assert.equal(moInput.value, "6");
  assert(w.document.querySelector(".metric").textContent.includes("HOMO"));
  assert(w.document.querySelector("tr.selected").textContent.includes("LUMO"));
  click("선택 MO ±표면");
  await until(() => surfaces === 2);
  assert.equal(
    w.document.querySelector("#jobs .active b").textContent,
    "DEMO · water (synthetic UI fixture)",
  );
  click("에너지·Force");
  await until(() =>
    w.document.getElementById("forceContent").textContent.includes("Cartesian"),
  );
  assert(
    w.document.getElementById("forceContent").textContent.includes("미출력"),
  );
  const slider = w.document.getElementById("frame");
  slider.value = "0";
  slider.dispatchEvent(new w.Event("input"));
  await until(() =>
    w.document
      .getElementById("forceContent")
      .textContent.includes("-76.123456789012"),
  );
  assert(w.document.getElementById("forceContent").textContent.includes("Fx"));
  click("분극률");
  await wait(30);
  assert(w.document.getElementById("panel").textContent.includes("4.00000000"));
  const polar = w.document.querySelector("#panel select");
  polar.value = "1";
  polar.dispatchEvent(new w.Event("change"));
  w.document.getElementById("themeBtn").click();
  assert.equal(w.document.querySelector("#panel select").value, "1");
  assert(w.document.getElementById("panel").textContent.includes("8.00000000"));
  w.document.getElementById("themeBtn").click();
  click("도움말");
  await wait(30);
  const search = w.document.querySelector("#panel input");
  search.value = "Reload source";
  search.dispatchEvent(new w.Event("input"));
  assert(
    w.document
      .querySelector(".help-content")
      .textContent.includes("다시 실행하는 버튼이 아닙니다"),
  );
  click("진동·분광");
  await wait(30);
  click("모드 +변위 XYZ");
  await until(() =>
    w.document.getElementById("status").textContent.includes("먼저 선택"),
  );
  const filter = [...w.document.querySelectorAll("label.field")]
    .find((l) => l.textContent.includes("Imaginary만"))
    .querySelector("input");
  filter.checked = true;
  filter.dispatchEvent(new w.Event("change"));
  assert.equal(w.document.querySelectorAll(".modes tbody tr").length, 1);
  assert(
    w.document.querySelector(".modes tbody tr").classList.contains("imaginary"),
  );
  const beforeAnimation = structures, beforeCoordinates = coordinateUpdates;
  w.document.querySelector(".modes tbody tr").click();
  await wait(230);
  assert(coordinateUpdates > beforeCoordinates, "animation should update existing coordinates");
  assert(structures <= beforeAnimation + 1, "animation should not rebuild the model each tick");
  click("정지");
  click("평형 구조");
  assert.equal(w.document.getElementById("frame").value, "0");
  w.document.querySelector(".modes tbody tr").click();
  await wait(160);
  assert(w.testTimer());
  // The task is still pending when its request begins; animation must stop now.
  const measurePending = w.testAction("input");
  assert.equal(w.testTimer(), null);
  await measurePending;
  const stoppedCoordinates = coordinateUpdates;
  await wait(160);
  assert.equal(coordinateUpdates, stoppedCoordinates);
  w.document.querySelector(".modes tbody tr").click();
  await wait(160);
  click("MO·표면");
  assert.equal(w.testTimer(), null, "changing panels must stop mode animation");
  click("진동·분광");
  click("스펙트럼 그리기");
  await until(() =>
    w.document.getElementById("plotTitle").textContent.startsWith("IR"),
  );
  click("MO·표면");
  await wait(30);
  click("+ 표면");
  await until(() => surfaces === 3);
  click("비교·열화학");
  await wait(30);
  click("전체 계산 조건 비교");
  await until(() =>
    w.document.getElementById("modalBody").textContent.includes("compatible"),
  );
  click("닫기");
  click("지원 범위");
  await until(
    () => w.document.querySelectorAll("#panel tbody tr").length === 140,
  );
  // A numeric sort must compare numbers and keep callbacks tied to source rows.
  const sortResult = w.eval(`(() => {
    const host = document.createElement("div");
    let clicked = null;
    const grid = testTable(host, ["value"], [[10], [-2], [null], [2]], i => { clicked = i; });
    const heading = grid.querySelector("th button");
    heading.click();
    const ascending = [...grid.querySelectorAll("tbody tr")].map(r => r.dataset.originalIndex);
    heading.click();
    const descending = [...grid.querySelectorAll("tbody tr")].map(r => r.dataset.originalIndex);
    grid.querySelector("tbody tr").click();
    return JSON.stringify({ascending, descending, clicked});
  })()`);
  assert.deepEqual(JSON.parse(sortResult), {ascending:["1","3","0","2"], descending:["0","3","1","2"], clicked:0});
  const language = w.document.getElementById("language");
  language.value = "en";
  language.dispatchEvent(new w.Event("change"));
  await until(() => w.document.getElementById("demoBtn").textContent === "Demo");
  assert.equal(w.document.documentElement.lang, "en");
  assert(w.document.documentElement.style.getPropertyValue("--font").startsWith('"Calibri"'), "legacy English font must migrate");
  assert.equal(JSON.parse(w.localStorage.getItem("gausslook.settings")).fontKo, "Gulim");
  assert.equal(JSON.parse(w.localStorage.getItem("gausslook.settings")).language, "en");
  click("Overview");
  assert(w.document.getElementById("panel").textContent.includes("Selected result:"));
  assert.equal(w.document.querySelector("#jobs .active b").textContent, "DEMO · water (synthetic UI fixture)");
  click("Vibrations · Spectra");
  assert(w.document.getElementById("panel").textContent.includes("3 modes · 1 imaginary"));
  w.document.getElementById("themeBtn").click();
  assert.equal(w.document.documentElement.dataset.theme, "light");
  click("Display settings");
  assert(w.document.getElementById("modalBody").textContent.includes("Atom scale"));
  const settingControl = label => [...w.document.querySelectorAll("#modalBody label.field")]
    .find(l => l.firstChild.textContent === label).querySelector("input,select");
  assert.equal(settingControl("Font size (px)").value, "14");
  assert.equal(settingControl("Font size (px)").step, "1");
  settingControl("Korean font").value = "Gulim";
  settingControl("English font").value = "Calibri";
  settingControl("Font size (px)").value = "14.5";
  click("Apply / save");
  await until(() => w.document.getElementById("status").textContent.includes("whole-number"));
  assert.equal(w.document.getElementById("modal").open, true);
  settingControl("Font size (px)").value = "14";
  click("Apply / save");
  const savedFonts = JSON.parse(w.localStorage.getItem("gausslook.settings"));
  assert.equal(savedFonts.fontKo, "Gulim"); assert.equal(savedFonts.fontEn, "Calibri");
  for (let i=0; i<3; i++) {
    language.value = "ko"; language.dispatchEvent(new w.Event("change"));
    assert(w.document.documentElement.style.getPropertyValue("--font").startsWith('"Gulim"'));
    language.value = "en"; language.dispatchEvent(new w.Event("change"));
    assert(w.document.documentElement.style.getPropertyValue("--font").startsWith('"Calibri"'));
    assert.equal(w.document.getElementById("demoBtn").textContent, "Demo");
  }
  click("Display settings");
  click("Close");
  click("Server folder");
  await until(() => w.document.getElementById("browsePath"));
  const folderPath = w.document.getElementById("browsePath");
  folderPath.value = "docs";
  folderPath.dispatchEvent(new w.KeyboardEvent("keydown", {key:"Enter", bubbles:true}));
  await until(() => w.document.getElementById("browsePath") !== folderPath && w.document.getElementById("browsePath").value.endsWith("docs"));
  assert([...w.document.querySelectorAll("#modalBody tbody tr")].some(r => r.firstElementChild.textContent === ".."));
  assert(w.document.querySelector(".file-browser .file-folder"));
  assert(w.document.querySelector(".file-browser .file-md td:nth-child(2)").textContent === "MD");
  click("↑ Parent folder");
  await until(() => !w.document.getElementById("browsePath").value.endsWith("docs"));
  click("Close");
  click("Structure · Input");
  assert(w.document.getElementById("panel").textContent.includes("SMILES"));
  assert(w.document.querySelector("#panel #gaussianForm"), "Gaussian form must be inline");
  assert.equal(w.document.getElementById("modal").open, false);
  assert(!w.document.getElementById("inputPreview").closest("[hidden]"));
  const smiles = w.document.getElementById("buildSmiles");
  smiles.value = "CCO"; smiles.dispatchEvent(new w.Event("input"));
  w.document.getElementById("input_method").value = "PBE1PBE";
  w.document.getElementById("input_title").value = "preserved draft";
  w.document.getElementById("themeBtn").click();
  assert.equal(w.document.getElementById("buildSmiles").value, "CCO");
  assert.equal(w.document.getElementById("input_title").value, "preserved draft");
  assert.equal(w.document.getElementById("input_method").value, "PBE1PBE");
  language.value = "ko"; language.dispatchEvent(new w.Event("change"));
  assert.equal(w.document.getElementById("buildSmiles").value, "CCO");
  assert.equal(w.document.getElementById("input_title").value, "preserved draft");
  language.value = "en"; language.dispatchEvent(new w.Event("change"));
  w.document.getElementById("input_method").value = "B3LYP";
  w.document.getElementById("input_title").value = "UI selected frame";
  w.document.getElementById("input_memory").value = "8GB";
  w.document.getElementById("input_cores").value = "8";
  slider.value = "1"; slider.dispatchEvent(new w.Event("input"));
  w.document.getElementById("generateInput").click();
  await until(() => w.document.getElementById("inputPreview").value.includes("UI selected frame"));
  assert.equal(lastInputFrame, 1, "inline generation must use the current timeline frame");
  const inputText = w.document.getElementById("inputPreview").value;
  assert(inputText.startsWith("%mem=8GB\n%nprocshared=8\n%chk=gausslook.chk\n#p B3LYP/def2SVP Opt Freq"));
  const structuresBeforeStyle = structures;
  w.document.getElementById("themeBtn").click();
  assert.equal(structures, structuresBeforeStyle, "appearance should reuse the existing model");
  // One frame uses the latest wheel event, rather than replaying its full queue.
  zooms = [];
  const viewerElement = w.document.getElementById("viewer");
  for (let i=0; i<30; i++) viewerElement.dispatchEvent(new w.WheelEvent("wheel", {deltaY:120, bubbles:true, cancelable:true}));
  viewerElement.dispatchEvent(new w.WheelEvent("wheel", {deltaY:-120, bubbles:true, cancelable:true}));
  await wait(40);
  assert.equal(zooms.length, 1);
  assert(zooms[0] > 1, "only the latest wheel direction should be used");
  const staleWheel = new w.WheelEvent("wheel", {deltaY:120, bubbles:true, cancelable:true});
  Object.defineProperty(staleWheel, "timeStamp", {value: w.performance.now() - 500});
  viewerElement.dispatchEvent(staleWheel);
  await wait(40);
  assert.equal(zooms.length, 1, "stale wheel input must be discarded");
  click("Help");
  const appearanceHelp = w.document.querySelector("#panel input");
  appearanceHelp.value = "Language, theme";
  appearanceHelp.dispatchEvent(new w.Event("input"));
  assert(w.document.querySelector(".help-content").textContent.includes("Language, theme"));
  language.value = "ko";
  language.dispatchEvent(new w.Event("change"));
  await until(() => w.document.getElementById("demoBtn").textContent === "데모");
  assert.equal(w.document.documentElement.lang, "ko");
  click("구조·입력");
  w.document.getElementById("buildSmiles").value = "CCO";
  click("3D conformer 생성");
  await until(() => w.document.querySelector("#jobs .active b").textContent === "SMILES / CCO", 1500);
  assert(structures > structuresBeforeStyle, "the RDKit builder result must reach the viewer");
  assert.deepEqual(errors, []);
  console.log(
    JSON.stringify({
      dom: "passed",
      structures,
      coordinateUpdates,
      renders,
      surfaces,
      features: 140,
      errors,
    }),
  );
  dom.window.close();
})().catch((e) => {
  console.error(e);
  dom.window.close();
  process.exitCode = 1;
});
