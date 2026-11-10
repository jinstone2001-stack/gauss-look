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
w.fetch = (url, opts) => fetch(new URL(url, base), opts);
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
let structures = 0,
  surfaces = 0;
const graphics = {
  getView: () => [],
  setView() {},
  render() {},
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
    return { setStyle() {}, setClickable() {}, selectedAtoms: () => atoms };
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
w.eval(
  fs.readFileSync(path.join(root, "web/core.js"), "utf8") +
    "\n" +
    fs.readFileSync(path.join(root, "web/app.js"), "utf8"),
);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const click = (text) => {
  const button = [...w.document.querySelectorAll("button")].find(
    (v) => v.textContent === text,
  );
  assert(button, `button missing: ${text}`);
  button.click();
};
async function until(fn) {
  for (let i = 0; i < 150; i++) {
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
  w.document.querySelector(".modes tbody tr").click();
  await wait(160);
  click("정지");
  click("평형 구조");
  assert.equal(w.document.getElementById("frame").value, "0");
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
  assert.deepEqual(errors, []);
  console.log(
    JSON.stringify({
      dom: "passed",
      structures,
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
