import fs from "node:fs/promises";
import path from "node:path";
import sharp from "file:///C:/Users/lfaf-test/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/lib/index.js";

const dir = process.argv[2] || "C:\\Users\\lfaf-test\\Documents\\报告编写\\AI大赛\\.bomcheck-review\\inspect";
const files = (await fs.readdir(dir))
  .filter((name) => /^slide-\d+\.png$/i.test(name))
  .sort();
const thumbW = 480;
const thumbH = 270;
const labelH = 32;
const cols = 4;
const rows = Math.ceil(files.length / cols);
const composites = [];

for (const [index, name] of files.entries()) {
  const thumb = await sharp(path.join(dir, name))
    .resize(thumbW, thumbH, { fit: "contain", background: "#ffffff" })
    .extend({ bottom: labelH, background: "#ffffff" })
    .png()
    .toBuffer();
  composites.push({
    input: thumb,
    left: (index % cols) * thumbW,
    top: Math.floor(index / cols) * (thumbH + labelH),
  });
}

await sharp({
  create: {
    width: cols * thumbW,
    height: rows * (thumbH + labelH),
    channels: 3,
    background: "#e8ecef",
  },
})
  .composite(composites)
  .png()
  .toFile(path.join(dir, "montage.png"));
