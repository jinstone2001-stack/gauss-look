/* DOM / API integration without pretending to test a real GPU renderer.
   NODE_PATH=/path/to/node_modules node tests/ui_dom.cjs URL
   The Python test launcher must keep the server in the same network namespace. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { JSDOM, VirtualConsole } = require('jsdom');
const base = process.argv[2];
const root = path.resolve(__dirname, '..');
const errors = [];
const consoleBridge = new VirtualConsole();
consoleBridge.on('jsdomError', (e) => errors.push(e.message));
const dom = new JSDOM(fs.readFileSync(path.join(root, 'web/index.html'), 'utf8'), {
  url: base, runScripts: 'outside-only', pretendToBeVisual: true, virtualConsole: consoleBridge,
});
const w = dom.window;
w.fetch = (url, opts) => fetch(new URL(url, base), opts);
w.ResizeObserver = class { observe() {} disconnect() {} };
w.HTMLCanvasElement.prototype.getContext = () => new Proxy({}, { get: () => () => {}, set: () => true });
w.Element.prototype.getBoundingClientRect = () => ({ width: 850, height: 250, x: 0, y: 0 });
w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
w.HTMLDialogElement.prototype.close = function () { this.open = false; };
w.URL.createObjectURL = () => 'blob:mock'; w.URL.revokeObjectURL = () => {};
let structures = 0, surfaces = 0;
const graphics = {
  getView: () => [], setView() {}, render() {}, resize() {}, zoomTo() {},
  removeAllModels() {}, removeAllLabels() {}, removeAllShapes() {}, addLabel() {}, setBackgroundColor() {},
  addModel(xyz) {
    structures++;
    const atoms = xyz.split('\n').slice(2).filter(Boolean).map((line, i) => {
      const [elem, x, y, z] = line.split(/\s+/); return { elem, x: +x, y: +y, z: +z, index: i };
    });
    return { setStyle() {}, setClickable() {}, selectedAtoms: () => atoms };
  },
  addCustom(mesh) {
    assert(mesh.vertexArr.length > 0); assert(mesh.faceArr.length > 0);
    assert(mesh.vertexArr.every(v => Number.isFinite(v.x + v.y + v.z)));
    surfaces++; return mesh;
  },
};
w.$3Dmol = { createViewer: () => graphics, Vector3: class { constructor(x, y, z) { this.x=x; this.y=y; this.z=z; } } };
w.addEventListener('error', e => errors.push(e.message));
w.eval(fs.readFileSync(path.join(root, 'web/app.js'), 'utf8'));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
const click = text => {
  const button = [...w.document.querySelectorAll('button')].find(v => v.textContent === text);
  assert(button, `button missing: ${text}`); button.click();
};
async function until(fn) { for(let i=0;i<150;i++) { if(fn()) return; await wait(30); } throw Error('DOM timeout'); }
(async () => {
  await until(() => w.document.querySelectorAll('.job').length === 1 && structures > 0);
  click('진동·분광'); await wait(30); click('스펙트럼 그리기');
  await until(() => w.document.getElementById('plotTitle').textContent.startsWith('IR'));
  click('MO·표면'); await wait(30); click('+ 표면'); await until(() => surfaces === 1);
  click('비교·열화학'); await wait(30); click('전체 계산 조건 비교');
  await until(() => w.document.getElementById('modalBody').textContent.includes('compatible'));
  click('닫기'); click('지원 범위');
  await until(() => w.document.querySelectorAll('#panel tbody tr').length === 140);
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({dom:'passed',structures,surfaces,features:140,errors}));
  dom.window.close();
})().catch(e => { console.error(e); dom.window.close(); process.exitCode=1; });
