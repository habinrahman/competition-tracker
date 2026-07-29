/**
 * Records docs/demo/demo.gif from the weekly newsletter HTML preview.
 *
 * Usage (from repo root):
 *   python runners/build_demo_assets.py
 *   cd scripts && npm install && npx playwright install chromium && npm run record:demo
 */
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import pkg from "gifenc";
const { GIFEncoder, quantize, applyPalette } = pkg;
import pngjs from "pngjs";

const { PNG } = pngjs;

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const DEMO_DIR = path.join(ROOT, "docs", "demo");
const NEWSLETTER_HTML = path.join(DEMO_DIR, "newsletter.html");
const OUT_GIF = path.join(DEMO_DIR, "demo.gif");
const PORT = 8765;
const BASE_URL = `http://127.0.0.1:${PORT}/newsletter.html`;

function runPythonBuild() {
  return new Promise((resolve, reject) => {
    const child = spawn("python", ["runners/build_demo_assets.py"], {
      cwd: ROOT,
      stdio: "inherit",
      shell: true,
    });
    child.on("error", reject);
    child.on("close", (code) => (code === 0 ? resolve() : reject(new Error(`build exited ${code}`))));
  });
}

function startStaticServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const rel = (req.url || "/").split("?")[0].replace(/^\//, "") || "newsletter.html";
      const filePath = path.join(DEMO_DIR, rel);
      if (!filePath.startsWith(DEMO_DIR) || !fs.existsSync(filePath)) {
        res.writeHead(404);
        res.end("Not found");
        return;
      }
      const ext = path.extname(filePath);
      const type = ext === ".html" ? "text/html; charset=utf-8" : "application/octet-stream";
      res.writeHead(200, { "Content-Type": type });
      res.end(fs.readFileSync(filePath));
    });
    server.listen(PORT, "127.0.0.1", () => resolve(server));
  });
}

async function capturePng(page) {
  return page.screenshot({ type: "png", fullPage: false });
}

function pngBufferToRgba(buffer) {
  const png = PNG.sync.read(buffer);
  return { width: png.width, height: png.height, data: png.data };
}

function writeGif(frames, width, height) {
  const gif = GIFEncoder();
  for (const frame of frames) {
    const palette = quantize(frame.data, 256);
    const index = applyPalette(frame.data, palette);
    gif.writeFrame(index, width, height, { palette, delay: 950, repeat: 0 });
  }
  gif.finish();
  fs.mkdirSync(path.dirname(OUT_GIF), { recursive: true });
  fs.writeFileSync(OUT_GIF, Buffer.from(gif.bytes()));
}

async function main() {
  await runPythonBuild();

  if (!fs.existsSync(NEWSLETTER_HTML)) {
    throw new Error(`Missing ${NEWSLETTER_HTML} — run python runners/build_demo_assets.py`);
  }

  const server = await startStaticServer();

  try {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1280, height: 820 } });
    const frames = [];

    await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 60_000 });
    await page.waitForSelector("text=Your weekly update", { timeout: 15_000 });
    await page.waitForTimeout(900);
    frames.push(await capturePng(page));

    await page.evaluate(() => window.scrollBy(0, 520));
    await page.waitForTimeout(800);
    frames.push(await capturePng(page));

    await page.evaluate(() => window.scrollBy(0, 620));
    await page.waitForTimeout(800);
    frames.push(await capturePng(page));

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(900);
    frames.push(await capturePng(page));

    await browser.close();

    const rgbaFrames = frames.map(pngBufferToRgba);
    writeGif(rgbaFrames, rgbaFrames[0].width, rgbaFrames[0].height);
    console.log(`Wrote ${OUT_GIF} (${frames.length} frames)`);
  } finally {
    server.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
