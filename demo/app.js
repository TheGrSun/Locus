import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { finiteBounds as bounds, viewSpan } from "./bounds.js";
import { LANGS, translate, translateError } from "./i18n.js";

const COLORS = ["#4f86c6", "#d16b66", "#5aa57a", "#8a6bb8", "#e09a4a", "#6e767d"];
const AXIS = { x: "#d6453d", y: "#2c6cb5", z: "#2e9a5a" };
const mode = document.getElementById("mode");
const rows = document.getElementById("rows");
const extra = document.getElementById("extra");
const error = document.getElementById("error");
const plane = document.getElementById("plane");
const stage = document.getElementById("stage");
const viewport = document.getElementById("viewport");
const context = plane.getContext("2d");
let expressions = [""];
let timer = 0;
let userMoved = false;
let requestSerial = 0;
let inflight = null;
let activeField = null;
let lang = "en";
let planeZoom = 1;

function text(key) { return translate(lang, key); }

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
viewport.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xffffff);
const camera = new THREE.PerspectiveCamera(42, 1, 0.05, 500);
camera.up.set(0, 0, 1);
let controls;
function attachControls() {
  const target = controls ? controls.target.clone() : new THREE.Vector3();
  controls?.dispose();
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.zoomSpeed = 0.7;
  controls.target.copy(target);
  controls.addEventListener("start", () => { userMoved = true; });
  controls.update();
}
attachControls();
const axes = new THREE.Group();
const graphs = new THREE.Group();
scene.add(axes, graphs);
scene.add(new THREE.AmbientLight(0xffffff, 0.72));
const sun = new THREE.DirectionalLight(0xffffff, 0.85);
sun.position.set(8, -6, 14);
scene.add(sun);

function resize() {
  const rect = viewport.getBoundingClientRect();
  renderer.setSize(rect.width, rect.height, false);
  camera.aspect = rect.width / Math.max(rect.height, 1);
  camera.updateProjectionMatrix();
  plane.width = Math.max(1, Math.floor(rect.width * devicePixelRatio));
  plane.height = Math.max(1, Math.floor(rect.height * devicePixelRatio));
  drawPlane(lastPlane);
}
new ResizeObserver(resize).observe(viewport);

function sprite(text, color, scale) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 128;
  const pen = canvas.getContext("2d");
  pen.fillStyle = color;
  pen.font = "italic 36px Times New Roman";
  pen.textAlign = "center";
  pen.textBaseline = "middle";
  pen.fillText(text, 128, 64);
  const material = new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(canvas), depthTest: false });
  const label = new THREE.Sprite(material);
  label.scale.set(scale * 1.15, scale * 0.58, 1);
  return label;
}

function stepFor(span) {
  const rough = Math.abs(span) / 6 || 1;
  const power = 10 ** Math.floor(Math.log10(rough));
  const fraction = rough / power;
  return (fraction < 1.5 ? 1 : fraction < 3 ? 2 : fraction < 7 ? 5 : 10) * power;
}

function line(group, a, b, color, overlay = false) {
  const geometry = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...b)]);
  const segment = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color, depthTest: !overlay }));
  if (overlay) segment.renderOrder = 8;
  group.add(segment);
}

function buildAxes(x0, x1, y0, y1, z0, z1) {
  axes.clear();
  const box = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
  [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7]].forEach(([a, b]) => line(axes, box[a], box[b], 0xc5d0cb));
  const xStep = stepFor(x1 - x0), yStep = stepFor(y1 - y0), zStep = stepFor(z1 - z0);
  for (let x = Math.ceil(x0 / xStep) * xStep; x <= x1 + 1e-9; x += xStep) line(axes, [x, y0, 0], [x, y1, 0], 0xd7e0db);
  for (let y = Math.ceil(y0 / yStep) * yStep; y <= y1 + 1e-9; y += yStep) line(axes, [x0, y, 0], [x1, y, 0], 0xd7e0db);
  line(axes, [x0, 0, 0], [x1, 0, 0], AXIS.x, true);
  line(axes, [0, y0, 0], [0, y1, 0], AXIS.y, true);
  line(axes, [0, 0, z0], [0, 0, z1], AXIS.z, true);
  const span = Math.max(x1 - x0, y1 - y0, z1 - z0);
  const label = span * 0.034;
  const place = (textLabel, color, position) => { const item = sprite(textLabel, color, label); item.position.set(...position); axes.add(item); };
  place("x", AXIS.x, [x1 + label * 1.6, 0, 0]);
  place("y", AXIS.y, [0, y1 + label * 1.6, 0]);
  place("z", AXIS.z, [0, 0, z1 + label * 1.6]);
  for (let value = Math.ceil(x0 / xStep) * xStep; value <= x1; value += xStep) if (Math.abs(value) > 1e-9) place(String(Math.round(value * 1000) / 1000), "#243028", [value, y0 - label * 2.2, 0]);
  for (let value = Math.ceil(y0 / yStep) * yStep; value <= y1; value += yStep) if (Math.abs(value) > 1e-9) place(String(Math.round(value * 1000) / 1000), "#243028", [x0 - label * 2.2, value, 0]);
  for (let value = Math.ceil(z0 / zStep) * zStep; value <= z1; value += zStep) if (Math.abs(value) > 1e-9) place(String(Math.round(value * 1000) / 1000), "#243028", [label * 2.2, y0, value]);
  if (!userMoved) {
    const center = new THREE.Vector3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
    camera.position.set(center.x + span * 0.95, center.y - span * 0.85, center.z + span * 0.62);
    controls.target.copy(center);
    controls.update();
  }
}

function surfaceMesh(surface, color, zSpan) {
  const width = surface.z[0].length, height = surface.z.length;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(width * height * 3);
  const zAt = (index) => surface.z[Math.floor(index / width)][index % width];
  const jump = Math.max(zSpan * 0.2, 1e-6);
  surface.z.forEach((row, yIndex) => row.forEach((value, xIndex) => {
    const offset = (yIndex * width + xIndex) * 3;
    positions[offset] = surface.x[xIndex];
    positions[offset + 1] = surface.y[yIndex];
    positions[offset + 2] = value == null || !Number.isFinite(value) ? NaN : value;
  }));
  const indices = [];
  for (let y = 0; y < height - 1; y++) {
    for (let x = 0; x < width - 1; x++) {
      const corners = [y * width + x, y * width + x + 1, (y + 1) * width + x, (y + 1) * width + x + 1];
      const heights = corners.map(zAt);
      if (heights.some((value) => value == null || !Number.isFinite(value))) continue;
      if (Math.max(...heights) - Math.min(...heights) > jump) continue;
      indices.push(corners[0], corners[2], corners[1], corners[1], corners[2], corners[3]);
    }
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return new THREE.Mesh(geometry, new THREE.MeshPhongMaterial({ color, side: THREE.DoubleSide, transparent: true, opacity: 0.78, shininess: 6, depthWrite: false }));
}

function setStage(three) {
  renderer.domElement.classList.toggle("hidden", !three);
  plane.classList.toggle("hidden", three);
  document.getElementById("hint").classList.toggle("hidden", !three);
}

function showGraph(data) {
  graphs.clear();
  const three = data.kind === "surface";
  setStage(three);
  if (three) {
    const samples = data.surfaces.flatMap((item) => item.z.flat());
    const xy = Math.max(Math.abs(data.x.at(-1) - data.x[0]), Math.abs(data.y.at(-1) - data.y[0]), 4);
    const typed = [Number(document.getElementById("z0").value), Number(document.getElementById("z1").value)];
    const [z0, z1] = typed[0] < typed[1] ? typed : viewSpan(samples, xy);
    buildAxes(data.x[0], data.x.at(-1), data.y[0], data.y.at(-1), z0, z1);
    data.surfaces.forEach((item, index) => {
      item.x = data.x;
      item.y = data.y;
      item.z = item.z.map((row) => row.map((value) => (value == null || value < z0 || value > z1 ? null : value)));
      graphs.add(surfaceMesh(item, COLORS[index % COLORS.length], z1 - z0));
    });
  } else {
    lastPlane = data;
    drawPlane(data);
  }
}

let lastPlane = null;
function drawPlane(data) {
  const width = plane.width, height = plane.height;
  context.clearRect(0, 0, width, height);
  context.fillStyle = "#fff";
  context.fillRect(0, 0, width, height);
  if (!data) data = { kind: "xy", x: [], series: [], xRange: [Number(document.getElementById("x0").value), Number(document.getElementById("x1").value)], yRange: [Number(document.getElementById("y0").value), Number(document.getElementById("y1").value)] };
  if (data.kind === "surface") return;
  const rawX = data.xRange || bounds(data.x || []);
  const rawY = data.yRange || bounds(data.series ? data.series.flatMap((series) => series.y) : []);
  const zoomRange = (range) => {
    const mid = (Number(range[0]) + Number(range[1])) / 2;
    const half = Math.max(Math.abs(Number(range[1]) - Number(range[0])) / 2, 1e-6) * planeZoom;
    return [mid - half, mid + half];
  };
  const xRange = zoomRange(rawX);
  const yRange = zoomRange(rawY);
  const pad = 56 * devicePixelRatio;
  const map = (x, y) => [pad + (x - xRange[0]) / (xRange[1] - xRange[0]) * (width - pad * 1.4), height - pad - (y - yRange[0]) / (yRange[1] - yRange[0]) * (height - pad * 1.5)];
  const xStep = stepFor(xRange[1] - xRange[0]), yStep = stepFor(yRange[1] - yRange[0]);
  context.font = `${14 * devicePixelRatio}px system-ui`;
  context.fillStyle = "#777";
  context.strokeStyle = "#eef2f0";
  context.lineWidth = 1;
  for (let x = Math.ceil(xRange[0] / xStep) * xStep; x <= xRange[1]; x += xStep) {
    const point = map(x, yRange[0]);
    context.beginPath(); context.moveTo(point[0], pad * 0.4); context.lineTo(point[0], height - pad); context.stroke();
    context.fillText(String(Math.round(x * 1000) / 1000), point[0] + 4, height - pad * 0.45);
  }
  for (let y = Math.ceil(yRange[0] / yStep) * yStep; y <= yRange[1]; y += yStep) {
    const point = map(xRange[0], y);
    context.beginPath(); context.moveTo(pad, point[1]); context.lineTo(width - pad * 0.4, point[1]); context.stroke();
    context.fillText(String(Math.round(y * 1000) / 1000), 8, point[1] - 4);
  }
  context.lineWidth = 1.15 * devicePixelRatio;
  [[xRange[0], 0, xRange[1], 0, AXIS.x], [0, yRange[0], 0, yRange[1], AXIS.y]].forEach(([a, b, c, d, color]) => {
    const start = map(a, b), end = map(c, d);
    context.strokeStyle = color;
    context.beginPath(); context.moveTo(start[0], start[1]); context.lineTo(end[0], end[1]); context.stroke();
  });
  context.font = `italic ${22 * devicePixelRatio}px "Times New Roman", serif`;
  context.fillStyle = AXIS.x;
  context.fillText("x", width - pad * 0.7, map(0, 0)[1] - 8);
  context.fillStyle = AXIS.y;
  context.fillText("y", map(0, 0)[0] + 8, pad * 0.55);
  const strokeSeries = (xs, ys, color, dash) => {
    context.beginPath();
    context.strokeStyle = color;
    context.lineWidth = 1.8 * devicePixelRatio;
    context.setLineDash(dash ? [8, 6] : []);
    let open = false;
    xs.forEach((x, index) => {
      const y = ys[index];
      if (x == null || y == null || !Number.isFinite(x) || !Number.isFinite(y)) { open = false; return; }
      const point = map(x, y);
      if (!open) context.moveTo(point[0], point[1]); else context.lineTo(point[0], point[1]);
      open = true;
    });
    context.stroke();
    context.setLineDash([]);
  };
  if (data.kind === "xy") data.series.forEach((series, index) => strokeSeries(data.x, series.y, COLORS[index % COLORS.length], series.dash));
}

function renderRows() {
  rows.replaceChildren(...expressions.map((value, index) => {
    const row = document.createElement("div");
    row.className = "row";
    row.innerHTML = `<span>${index + 1}</span><i class="swatch" style="background:${COLORS[index % COLORS.length]}"></i>`;
    const input = document.createElement("input");
    input.value = value;
    input.placeholder = mode.value === "surfaces" ? text("phSurface") : text("phCurve");
    input.oninput = () => { expressions[index] = input.value; schedule(); };
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "remove";
    remove.textContent = "×";
    remove.title = text("remove");
    remove.onclick = () => {
      if (expressions.length === 1) expressions[0] = "";
      else expressions.splice(index, 1);
      renderRows();
      schedule();
    };
    row.append(input, remove);
    return row;
  }));
}

function extraFields() {
  extra.innerHTML = "";
  document.getElementById("derivative-wrap").classList.toggle("hidden", mode.value !== "curves");
  document.getElementById("z-range").classList.toggle("hidden", mode.value !== "surfaces");
}

function payload() {
  const body = {
    mode: mode.value,
    formulas: expressions.filter(Boolean).join("\n"),
    derivative: document.getElementById("derivative").checked,
    xRange: [document.getElementById("x0").value, document.getElementById("x1").value],
    yRange: [document.getElementById("y0").value, document.getElementById("y1").value]
  };
  return body;
}

async function compute() {
  const serial = ++requestSerial;
  inflight?.abort();
  const controller = new AbortController();
  inflight = controller;
  const body = payload();
  if (!body.formulas) {
    if (serial !== requestSerial) return;
    error.textContent = "";
    const three = mode.value === "surfaces";
    setStage(three);
    graphs.clear();
    if (three) buildAxes(-5, 5, -5, 5, -5, 5);
    else { lastPlane = null; drawPlane(null); }
    return;
  }
  try {
    const response = await fetch("/api/compute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const data = await response.json();
    if (serial !== requestSerial) return;
    error.textContent = response.ok ? translateError(lang, data.warning || "") : (translateError(lang, data.error) || text("errUnreadable"));
    if (response.ok) showGraph(data);
  } catch (err) {
    if (err.name === "AbortError" || serial !== requestSerial) return;
    error.textContent = text("errUnreadable");
  }
}

function schedule() { clearTimeout(timer); timer = setTimeout(compute, 280); }

function closeMenus() {
  document.querySelectorAll(".menu ul").forEach((list) => { list.hidden = true; });
  document.querySelectorAll(".menu > button").forEach((button) => {
    button.setAttribute("aria-expanded", "false");
    button.classList.remove("on");
  });
}

function applyLanguage() {
  document.documentElement.lang = lang;
  document.getElementById("language-button").textContent = LANGS.find(([id]) => id === lang)?.[1] || "English";
  document.getElementById("mode-button").textContent = text(MODE_KEYS[mode.value] || "surface");
  document.title = text("title");
  document.getElementById("brand").textContent = text("title");
  document.getElementById("hint").textContent = text("hint");
  document.getElementById("derivative-label").textContent = text("derivative");
  document.getElementById("z-range").classList.toggle("hidden", mode.value !== "surfaces");
  for (const [value, key] of Object.entries(MODE_KEYS)) {
    mode.querySelector(`option[value="${value}"]`).textContent = text(key);
  }
  document.querySelectorAll("#mode-menu button").forEach((choice) => {
    choice.textContent = text(MODE_KEYS[choice.dataset.value]);
  });
  document.getElementById("orient-default").textContent = text("orientDefault");
  document.getElementById("orient-xy").textContent = text("orientXY");
  document.getElementById("zoom-in").textContent = text("zoomIn");
  document.getElementById("zoom-out").textContent = text("zoomOut");
  renderRows();
  extraFields();
}

function openMenu(button, menu, render) {
  button.onclick = (event) => {
    event.stopPropagation();
    const open = menu.hidden;
    closeMenus();
    menu.hidden = !open;
    button.setAttribute("aria-expanded", String(open));
    button.classList.toggle("on", open);
    if (open) render();
  };
}

function chooseLanguage() {
  const button = document.getElementById("language-button");
  const menu = document.getElementById("language-menu");
  let saved = "en";
  try { saved = localStorage.getItem("desmos-mcp-lang") || "en"; } catch { saved = "en"; }
  lang = LANGS.some(([id]) => id === saved) ? saved : "en";
  const labelOf = (id) => LANGS.find(([value]) => value === id)?.[1] || "English";
  const renderMenu = () => {
    button.textContent = labelOf(lang);
    menu.replaceChildren(...LANGS.map(([id, label]) => {
      const item = document.createElement("li");
      const choice = document.createElement("button");
      choice.type = "button";
      choice.textContent = label;
      choice.setAttribute("role", "option");
      choice.setAttribute("aria-selected", String(id === lang));
      choice.onclick = (event) => {
        event.stopPropagation();
        lang = id;
        try { localStorage.setItem("desmos-mcp-lang", lang); } catch { /* keep the choice for this visit */ }
        button.textContent = label;
        document.getElementById("mode-button").textContent = text(MODE_KEYS[mode.value] || "surface");
        closeMenus();
        applyLanguage();
      };
      item.append(choice);
      return item;
    }));
  };
  openMenu(button, menu, renderMenu);
  renderMenu();
}

const MODE_KEYS = { surfaces: "surface", curves: "curve" };

function chooseMode() {
  const button = document.getElementById("mode-button");
  const menu = document.getElementById("mode-menu");
  const renderMenu = () => {
    button.textContent = text(MODE_KEYS[mode.value]);
    menu.replaceChildren(...Object.entries(MODE_KEYS).map(([value, key]) => {
      const item = document.createElement("li");
      const choice = document.createElement("button");
      choice.type = "button";
      choice.textContent = text(key);
      choice.dataset.value = value;
      choice.setAttribute("aria-selected", String(value === mode.value));
      choice.onclick = (event) => {
        event.stopPropagation();
        mode.value = value;
        button.textContent = text(key);
        closeMenus();
        mode.onchange();
      };
      item.append(choice);
      return item;
    }));
  };
  openMenu(button, menu, renderMenu);
  renderMenu();
}

document.addEventListener("click", () => closeMenus());

document.getElementById("add").onclick = () => { expressions.push(""); renderRows(); };
mode.onchange = () => { planeZoom = 1; setStage(mode.value === "surfaces"); extraFields(); chooseMode(); userMoved = false; schedule(); };
document.querySelectorAll(".window input").forEach((input) => { input.oninput = () => { userMoved = false; schedule(); }; });
chooseLanguage();
chooseMode();
applyLanguage();
setStage(true);
buildAxes(-5, 5, -5, 5, -5, 5);
function viewingPlane() { return renderer.domElement.classList.contains("hidden"); }

function frame(modeName) {
  userMoved = true;
  const target = controls.target.clone();
  const distance = Math.max(camera.position.distanceTo(target), 1);
  if (modeName === "xy") {
    camera.up.set(0, 1, 0);
    camera.position.set(target.x, target.y, target.z + distance);
  } else {
    camera.up.set(0, 0, 1);
    camera.position.set(target.x + distance * 0.72, target.y - distance * 0.72, target.z + distance * 0.48);
  }
  camera.lookAt(target);
  attachControls();
  controls.target.copy(target);
  controls.update();
}
function resetPlane() {
  planeZoom = 1;
  drawPlane(lastPlane);
}
function zoom(factor) {
  userMoved = true;
  if (viewingPlane()) {
    planeZoom = Math.min(40, Math.max(0.05, planeZoom * factor));
    drawPlane(lastPlane);
    return;
  }
  const offset = camera.position.clone().sub(controls.target).multiplyScalar(factor);
  camera.position.copy(controls.target.clone().add(offset));
  controls.update();
}
function flash(button) {
  button.classList.remove("pressed");
  void button.offsetWidth;
  button.classList.add("pressed");
  window.clearTimeout(button._pressTimer);
  button._pressTimer = window.setTimeout(() => button.classList.remove("pressed"), 420);
}
document.addEventListener("pointerdown", (event) => {
  const button = event.target.closest("button");
  if (button) flash(button);
});
function bindTool(id, action) {
  document.getElementById(id).addEventListener("pointerdown", (event) => {
    event.preventDefault();
    action();
  });
}
function markView(name) {
  document.getElementById("orient-default").classList.toggle("on", name === "default");
  document.getElementById("orient-xy").classList.toggle("on", name === "xy");
}
bindTool("orient-default", () => { markView("default"); if (viewingPlane()) resetPlane(); else frame("default"); });
bindTool("orient-xy", () => { if (viewingPlane()) { markView("default"); resetPlane(); } else { markView("xy"); frame("xy"); } });
bindTool("zoom-in", () => zoom(0.8));
bindTool("zoom-out", () => zoom(1.25));
resize();
renderer.setAnimationLoop(() => { controls.update(); renderer.render(scene, camera); });
