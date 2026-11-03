export const LANGS = [
  ["en", "English"],
  ["zh-CN", "简体中文"],
  ["zh-TW", "繁體中文"],
  ["ja", "日本語"],
  ["ko", "한국어"],
  ["de", "Deutsch"],
  ["fr", "Français"],
  ["es", "Español"],
  ["ru", "Русский"],
];

export const SYMBOL_ROWS = [
  [["sin", "sin()", -1], ["cos", "cos()", -1], ["tan", "tan()", -1], ["√", "sqrt()", -1], ["ln", "ln()", -1], ["exp", "exp()", -1], ["abs", "abs()", -1]],
  [["π", "π", 0], ["e", "e", 0], ["x²", "^2", 0], ["^", "^", 0], ["(", "(", 0], [")", ")", 0]],
  [["+", "+", 0], ["−", "-", 0], ["×", "*", 0], ["÷", "/", 0]],
];

const TEXT = {
  en: {
    title: "Locus", surface: "3D surface", curve: "2D curve", parametric: "Parametric curve", vector: "Vector field", points: "Points", physics: "Physics",
    hint: "Drag to orbit, scroll to zoom, right-click to pan", derivative: "Plot derivative", remove: "Remove",
    orientDefault: "Default view", orientXY: "XY view", zoomIn: "Zoom in", zoomOut: "Zoom out", symbols: "Insert a symbol", sketch: "Sketch fit",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), empty for a plane curve",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "Overlay y = x^2, optional",
    proj: "Projectile", osc: "Harmonic oscillator", motion: "Custom x(t), y(t)",
    phSpeed: "Speed", phAngle: "Angle in degrees", phGravity: "Gravity", phAmp: "Amplitude", phOmega: "Angular frequency", phPhase: "Phase in radians", phCycles: "Cycles",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t start", phT1: "t end",
    errFormula: "Enter at least one formula.", errSix: "At most 6 formulas at once.", errFinite: "{name} must be a finite number.", errRange: "A range needs two numbers.",
    errParam: "A parametric curve needs x(t) and y(t).", errPoint: "Each point is x y or x y z, with finite coordinates at most 1,000,000 in magnitude.",
    errCount: "Provide 1 to 400 points, one x y or x y z per line.", errSame: "Use either all x y points or all x y z points.",     errMotion: "Unknown motion type.", errMode: "Unknown calculation type.",
    errUnreadable: "The calculation did not return a readable result.",
    errSurface: "This is a surface. Switch to 3D surface.",
    errSyntax: "Use y = sin(x) or sin(π). Write multiplication as *.",
    errSurfaceSyntax: "Write the surface as z = sin(π) or x^3. Functions need parentheses, and multiplication uses *.",
    errSketch: "Draw a stroke that actually changes.",
  },
  "zh-CN": {
    title: "Locus", surface: "三维曲面", curve: "二维曲线", parametric: "参数曲线", vector: "向量场", points: "散点", physics: "物理运动",
    hint: "拖动旋转，滚轮缩放，右键平移", derivative: "显示导数曲线", remove: "删除",
    orientDefault: "默认方向", orientXY: "XY 方向", zoomIn: "放大", zoomOut: "缩小", symbols: "点击插入符号", sketch: "手绘拟合",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t)，平面曲线留空",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "叠加 y = x^2，可空",
    proj: "抛体", osc: "简谐振动", motion: "自定义 x(t), y(t)",
    phSpeed: "初速度", phAngle: "仰角（度）", phGravity: "重力加速度", phAmp: "振幅", phOmega: "角频率", phPhase: "相位（弧度）", phCycles: "周期数",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t 起点", phT1: "t 终点",
    errFormula: "请输入至少一条公式。", errSix: "一次最多 6 条公式。", errFinite: "{name} 必须是有限数字。", errRange: "范围需要两个数字。",
    errParam: "参数曲线需要 x(t) 和 y(t)。", errPoint: "每个点都是 x y 或 x y z，坐标必须有限且绝对值不超过 1000000。",
    errCount: "请提供 1 到 400 个点，每行是 x y 或 x y z。", errSame: "请统一使用 x y 或 x y z。",     errMotion: "未知的运动类型。", errMode: "未知的计算类型。",
    errUnreadable: "计算没有返回可读结果。",
    errSurface: "这是曲面公式，请切换到三维曲面。",
    errSyntax: "公式写成 y = sin(x) 或 sin(π)。乘法要用 *。",
    errSurfaceSyntax: "曲面写成 z = sin(π) 或 x^3。函数要加括号，乘法用 *。",
    errSketch: "请画出一段有起伏的曲线。",
  },
  "zh-TW": {
    title: "Locus", surface: "三維曲面", curve: "二維曲線", parametric: "參數曲線", vector: "向量場", points: "散點", physics: "物理運動",
    hint: "拖曳旋轉，滾輪縮放，右鍵平移", derivative: "顯示導數曲線", remove: "刪除",
    orientDefault: "預設方向", orientXY: "XY 方向", zoomIn: "放大", zoomOut: "縮小", symbols: "點擊插入符號",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t)，平面曲線留空",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "疊加 y = x^2，可留空",
    proj: "拋體", osc: "簡諧振動", motion: "自訂 x(t), y(t)",
    phSpeed: "初速度", phAngle: "仰角（度）", phGravity: "重力加速度", phAmp: "振幅", phOmega: "角頻率", phPhase: "相位（弧度）", phCycles: "週期數",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t 起點", phT1: "t 終點",
    errFormula: "請輸入至少一條公式。", errSix: "一次最多 6 條公式。", errFinite: "{name} 必須是有限數字。", errRange: "範圍需要兩個數字。",
    errParam: "參數曲線需要 x(t) 和 y(t)。", errPoint: "每個點都是 x y 或 x y z，座標必須有限且絕對值不超過 1000000。",
    errCount: "請提供 1 到 400 個點，每行是 x y 或 x y z。", errSame: "請統一使用 x y 或 x y z。", errMotion: "未知的運動類型。", errMode: "未知的計算類型。",
  },
  ja: {
    title: "Locus", surface: "3D 曲面", curve: "2D 曲線", parametric: "パラメトリック曲線", vector: "ベクトル場", points: "点", physics: "物理運動",
    hint: "ドラッグで回転、ホイールで拡大、右クリックで移動", derivative: "導関数を表示", remove: "削除",
    orientDefault: "標準方向", orientXY: "XY 方向", zoomIn: "拡大", zoomOut: "縮小", symbols: "記号を挿入",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t)。平面曲線なら空欄",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "重ねる y = x^2。空欄可",
    proj: "放物運動", osc: "単振動", motion: "任意の x(t), y(t)",
    phSpeed: "初速", phAngle: "仰角（度）", phGravity: "重力加速度", phAmp: "振幅", phOmega: "角周波数", phPhase: "位相（ラジアン）", phCycles: "周期数",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t の開始", phT1: "t の終了",
    errFormula: "式を1つ以上入力してください。", errSix: "式は一度に6つまでです。", errFinite: "{name} は有限の数にしてください。", errRange: "範囲には2つの数が必要です。",
    errParam: "パラメトリック曲線には x(t) と y(t) が必要です。", errPoint: "各点は x y または x y z で、有限かつ絶対値は 1000000 以下です。",
    errCount: "1 から 400 点を、1 行に x y または x y z で入力してください。", errSame: "x y と x y z は混ぜないでください。", errMotion: "不明な運動の種類です。", errMode: "不明な計算の種類です。",
  },
  ko: {
    title: "Locus", surface: "3D 곡면", curve: "2D 곡선", parametric: "매개변수 곡선", vector: "벡터장", points: "점", physics: "물리 운동",
    hint: "드래그로 회전, 휠로 확대, 오른쪽 버튼으로 이동", derivative: "도함수 표시", remove: "삭제",
    orientDefault: "기본 방향", orientXY: "XY 방향", zoomIn: "확대", zoomOut: "축소", symbols: "기호 삽입",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), 평면 곡선이면 비움",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "겹쳐 그릴 y = x^2, 선택",
    proj: "포물선 운동", osc: "단조화 진동", motion: "사용자 x(t), y(t)",
    phSpeed: "초기 속력", phAngle: "앙각(도)", phGravity: "중력 가속도", phAmp: "진폭", phOmega: "각진동수", phPhase: "위상(라디안)", phCycles: "주기 수",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t 시작", phT1: "t 끝",
    errFormula: "식을 하나 이상 입력하세요.", errSix: "식은 한 번에 6개까지입니다.", errFinite: "{name}은(는) 유한한 숫자여야 합니다.", errRange: "범위에는 숫자 두 개가 필요합니다.",
    errParam: "매개변수 곡선에는 x(t)와 y(t)가 필요합니다.", errPoint: "각 점은 x y 또는 x y z이며, 유한하고 절댓값은 1000000 이하여야 합니다.",
    errCount: "1개에서 400개의 점을 한 줄에 x y 또는 x y z로 입력하세요.", errSame: "x y와 x y z를 섞지 마세요.", errMotion: "알 수 없는 운동 종류입니다.", errMode: "알 수 없는 계산 종류입니다.",
  },
  de: {
    title: "Locus", surface: "3D-Fläche", curve: "2D-Kurve", parametric: "Parameterkurve", vector: "Vektorfeld", points: "Punkte", physics: "Physik",
    hint: "Ziehen dreht, Rad zoomt, Rechtsklick verschiebt", derivative: "Ableitung zeigen", remove: "Entfernen",
    orientDefault: "Standardansicht", orientXY: "XY-Ansicht", zoomIn: "Vergrößern", zoomOut: "Verkleinern", symbols: "Symbol einfügen",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), leer für eine ebene Kurve",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "y = x^2 darüberlegen, optional",
    proj: "Wurf", osc: "Harmonische Schwingung", motion: "Eigenes x(t), y(t)",
    phSpeed: "Geschwindigkeit", phAngle: "Winkel in Grad", phGravity: "Schwerebeschleunigung", phAmp: "Amplitude", phOmega: "Kreisfrequenz", phPhase: "Phase in Radiant", phCycles: "Perioden",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "t Anfang", phT1: "t Ende",
    errFormula: "Mindestens eine Formel eingeben.", errSix: "Höchstens 6 Formeln auf einmal.", errFinite: "{name} muss eine endliche Zahl sein.", errRange: "Ein Bereich braucht zwei Zahlen.",
    errParam: "Eine Parameterkurve braucht x(t) und y(t).", errPoint: "Jeder Punkt ist x y oder x y z, endlich und höchstens 1.000.000 im Betrag.",
    errCount: "1 bis 400 Punkte, je Zeile x y oder x y z.", errSame: "Entweder nur x y oder nur x y z verwenden.", errMotion: "Unbekannte Bewegungsart.", errMode: "Unbekannte Berechnungsart.",
  },
  fr: {
    title: "Locus", surface: "Surface 3D", curve: "Courbe 2D", parametric: "Courbe paramétrique", vector: "Champ de vecteurs", points: "Points", physics: "Physique",
    hint: "Glisser pour tourner, molette pour zoomer, clic droit pour déplacer", derivative: "Afficher la dérivée", remove: "Retirer",
    orientDefault: "Vue par défaut", orientXY: "Vue XY", zoomIn: "Zoom avant", zoomOut: "Zoom arrière", symbols: "Insérer un symbole",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), vide pour une courbe plane",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "Superposer y = x^2, facultatif",
    proj: "Projectile", osc: "Oscillateur harmonique", motion: "x(t), y(t) personnalisés",
    phSpeed: "Vitesse", phAngle: "Angle en degrés", phGravity: "Gravité", phAmp: "Amplitude", phOmega: "Pulsation", phPhase: "Phase en radians", phCycles: "Cycles",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "début de t", phT1: "fin de t",
    errFormula: "Saisissez au moins une formule.", errSix: "6 formules au plus à la fois.", errFinite: "{name} doit être un nombre fini.", errRange: "Une plage demande deux nombres.",
    errParam: "Une courbe paramétrique demande x(t) et y(t).", errPoint: "Chaque point est x y ou x y z, fini et d’amplitude au plus 1 000 000.",
    errCount: "Donnez 1 à 400 points, une ligne x y ou x y z.", errSame: "Utilisez soit tous les points x y, soit tous les points x y z.", errMotion: "Type de mouvement inconnu.", errMode: "Type de calcul inconnu.",
  },
  es: {
    title: "Locus", surface: "Superficie 3D", curve: "Curva 2D", parametric: "Curva paramétrica", vector: "Campo vectorial", points: "Puntos", physics: "Física",
    hint: "Arrastra para girar, la rueda amplía, clic derecho desplaza", derivative: "Mostrar la derivada", remove: "Quitar",
    orientDefault: "Vista predeterminada", orientXY: "Vista XY", zoomIn: "Acercar", zoomOut: "Alejar", symbols: "Insertar un símbolo",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), vacío para una curva plana",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "Superponer y = x^2, opcional",
    proj: "Proyectil", osc: "Oscilador armónico", motion: "x(t), y(t) propios",
    phSpeed: "Velocidad", phAngle: "Ángulo en grados", phGravity: "Gravedad", phAmp: "Amplitud", phOmega: "Frecuencia angular", phPhase: "Fase en radianes", phCycles: "Ciclos",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "inicio de t", phT1: "fin de t",
    errFormula: "Introduce al menos una fórmula.", errSix: "Como máximo 6 fórmulas a la vez.", errFinite: "{name} debe ser un número finito.", errRange: "Un rango necesita dos números.",
    errParam: "Una curva paramétrica necesita x(t) e y(t).", errPoint: "Cada punto es x y o x y z, finito y de magnitud como máximo 1 000 000.",
    errCount: "Da de 1 a 400 puntos, una línea x y o x y z.", errSame: "Usa todos los puntos x y o todos los puntos x y z.", errMotion: "Tipo de movimiento desconocido.", errMode: "Tipo de cálculo desconocido.",
  },
  ru: {
    title: "Locus", surface: "3D-поверхность", curve: "2D-кривая", parametric: "Параметрическая кривая", vector: "Векторное поле", points: "Точки", physics: "Физика",
    hint: "Тяните для поворота, колесо меняет масштаб, правая кнопка сдвигает", derivative: "Показать производную", remove: "Удалить",
    orientDefault: "Обычный вид", orientXY: "Вид XY", zoomIn: "Приблизить", zoomOut: "Отдалить", symbols: "Вставить символ",
    phSurface: "z = sin(x)*cos(y)", phCurve: "sin(x)", phXt: "x(t) = cos(t)", phYt: "y(t) = sin(t)", phZt: "z(t), пусто для плоской кривой",
    phFx: "fx = -y", phFy: "fy = x", phPoints: "0 0\n1 1\n2 4", phOverlay: "Наложить y = x^2, необязательно",
    proj: "Бросок", osc: "Гармонические колебания", motion: "Свои x(t), y(t)",
    phSpeed: "Скорость", phAngle: "Угол в градусах", phGravity: "Ускорение свободного падения", phAmp: "Амплитуда", phOmega: "Угловая частота", phPhase: "Фаза в радианах", phCycles: "Число периодов",
    phMx: "x(t) = t", phMy: "y(t) = 4*t - 4.9*t^2", phT0: "начало t", phT1: "конец t",
    errFormula: "Введите хотя бы одну формулу.", errSix: "Не больше 6 формул за раз.", errFinite: "{name} должно быть конечным числом.", errRange: "Для диапазона нужны два числа.",
    errParam: "Параметрической кривой нужны x(t) и y(t).", errPoint: "Каждая точка — x y или x y z, конечная и не больше 1 000 000 по модулю.",
    errCount: "Укажите от 1 до 400 точек, по одной x y или x y z в строке.", errSame: "Используйте либо все точки x y, либо все точки x y z.", errMotion: "Неизвестный тип движения.", errMode: "Неизвестный тип расчёта.",
  },
};

const ERROR_KEY = {
  "请输入至少一条公式。": "errFormula",
  "一次最多 6 条公式。": "errSix",
  "范围需要两个数字。": "errRange",
  "参数曲线需要 x(t) 和 y(t)。": "errParam",
  "每个点都是 x y 或 x y z，坐标必须有限且绝对值不超过 1000000。": "errPoint",
  "请提供 1 到 400 个点，每行是 x y 或 x y z。": "errCount",
  "请统一使用 x y 或 x y z。": "errSame",
  "未知的运动类型。": "errMotion",
  "未知的计算类型。": "errMode",
  "这是曲面公式，请切换到三维曲面。": "errSurface",
  "手绘至少需要一段有变化的曲线。": "errSketch",
};

export function translate(lang, key) {
  const pack = TEXT[lang] || TEXT.en;
  return pack[key] || TEXT.en[key] || key;
}

export function translateError(lang, message) {
  const lined = /^(第 \d+ 行「[^」]*」：)([\s\S]*)$/.exec(message || "");
  if (lined) return lined[1] + translateError(lang, lined[2]);
  if (message && (message.startsWith("Use x^2") || message.startsWith("Enter a ") || message.startsWith("Parametric ") || message.startsWith("Supported syntax"))) {
    return translate(lang, "errSyntax");
  }
  if (message && (message.startsWith("Use z =") || message.startsWith("Surfaces use"))) {
    return translate(lang, "errSurfaceSyntax");
  }
  const finite = /^(\w+) 必须是有限数字。$/.exec(message || "");
  if (finite) return translate(lang, "errFinite").replace("{name}", finite[1]);
  const key = ERROR_KEY[message];
  return key ? translate(lang, key) : message;
}
