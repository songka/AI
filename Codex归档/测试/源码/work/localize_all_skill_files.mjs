import fs from "fs";
import path from "path";

const base = path.join(
  "C:",
  "Users",
  "lfaf-test",
  "Documents",
  "测试",
  "电气工程师agent skill"
);

const packages = [
  "EE-AI-Toolkit(电气工程师AI工具包)",
  "PLC-Programming(PLC编程开发综合)",
];

const cnWord = new Map([
  ["power", "功率"],
  ["calculator", "计算器"],
  ["load", "负载"],
  ["forecasting", "预测"],
  ["linear", "线性"],
  ["regression", "回归"],
  ["transformer", "变压器"],
  ["efficiency", "效率"],
  ["fault", "故障"],
  ["classification", "分类"],
  ["simple", "基础"],
  ["ml", "机器学习"],
  ["data", "数据"],
  ["cleaner", "清洗"],
  ["signal", "信号"],
  ["plotter", "绘图"],
  ["unit", "单位"],
  ["converter", "转换"],
  ["prompt", "提示词"],
  ["validator", "校验"],
  ["ohm", "欧姆"],
  ["law", "定律"],
  ["solver", "求解"],
  ["voltage", "电压"],
  ["drop", "降落"],
  ["csv", "CSV"],
  ["engineering", "工程"],
  ["reader", "读取"],
  ["improved", "改进版"],
  ["three", "三相"],
  ["phase", "相"],
  ["current", "电流"],
  ["resistance", "电阻"],
  ["impedance", "阻抗"],
  ["reactance", "电抗"],
  ["capacitance", "电容"],
  ["inductance", "电感"],
  ["harmonic", "谐波"],
  ["filter", "滤波"],
  ["motor", "电机"],
  ["battery", "电池"],
  ["solar", "光伏"],
  ["wind", "风电"],
  ["relay", "继电器"],
  ["protection", "保护"],
  ["short", "短路"],
  ["circuit", "电路"],
  ["energy", "电能"],
  ["cost", "成本"],
  ["optimization", "优化"],
  ["visualization", "可视化"],
  ["report", "报告"],
]);

function walk(dir, out = []) {
  for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, item.name);
    if (item.isDirectory()) walk(full, out);
    else out.push(full);
  }
  return out;
}

function titleFromPythonName(file) {
  const name = path.basename(file, ".py").replace(/^script_\d+_/, "");
  const words = name.split(/[_\-\s]+/).filter(Boolean);
  const cn = words.map((w) => cnWord.get(w.toLowerCase()) || w).join("");
  const en = words.join(" ");
  return { cn: cn || "电气工程示例", en };
}

function localizePython(file) {
  let text = fs.readFileSync(file, "utf8");
  text = text.replace(
    /^# 中文导读开始[\s\S]*?# 中文导读结束\r?\n\r?\n?/,
    ""
  );
  const { cn, en } = titleFromPythonName(file);
  const header = [
    "# 中文导读开始",
    `# 中文说明：本脚本用于演示“${cn}”相关的电气工程计算、数据处理或 AI 辅助分析方法。`,
    `# 原始英文主题：${en}`,
    "# 使用建议：可先阅读函数名、输入参数和输出结果，再根据现场数据修改数值或文件路径。",
    "# 功能保持：这里只增加中文说明，不改变原有代码逻辑、文件名或导入方式。",
    "# 中文导读结束",
    "",
  ].join("\n");
  fs.writeFileSync(file, header + text, "utf8");
}

let pyCount = 0;
for (const pkg of packages) {
  const pkgDir = path.join(base, pkg, "package");
  for (const file of walk(pkgDir)) {
    if (file.toLowerCase().endsWith(".py")) {
      localizePython(file);
      pyCount += 1;
    }
  }
}

console.log(`已处理 Python 文件：${pyCount}`);
