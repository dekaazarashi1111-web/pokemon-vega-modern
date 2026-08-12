import crypto from "node:crypto";
import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";
import { cdpBaseUrl, sessionNamePrefix, stateDir, waitForCdp } from "./config.mjs";

const assistantSelector = "[data-message-author-role='assistant']";
const userSelector = "[data-message-author-role='user']";
const rateLimitRetryAfterMinutes = 30;
const rateLimitPatterns = [
  { code: "too_many_requests_ja", pattern: /リクエストが多すぎます/i },
  { code: "please_try_again_later_ja", pattern: /しばらくしてから/i },
  { code: "too_many_requests_en", pattern: /too many requests/i },
  { code: "try_again_later_en", pattern: /try again later/i },
  { code: "rate_limit_en", pattern: /rate limit(?:ed)?/i },
  { code: "image_generation_limit_ja", pattern: /画像生成(?:の)?(?:上限|制限)/i },
  { code: "temporary_limit_ja", pattern: /一時的(?:な)?制限/i }
];

class RateLimitedError extends Error {
  constructor(details) {
    super(`ChatGPT Webの画像生成が一時制限されています: ${details.match.code}`);
    this.name = "RateLimitedError";
    this.details = details;
  }
}

function parsePositiveInteger(value, name) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${name} は正の整数で指定してください: ${value}`);
  }
  return parsed;
}

function parseNonNegativeInteger(value, name) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`${name} は0以上の整数で指定してください: ${value}`);
  }
  return parsed;
}

function parseArgs(argv) {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const options = {
    timeoutMs: 600000,
    stableRounds: 3,
    stableIntervalMs: 2000,
    outputDir: path.join("userfile", "chatgpt_generated_images", stamp),
    promptFile: null,
    expectedImages: 1,
    minDimension: 128,
    filenamePrefix: "chatgpt_image",
    sessionIndex: Number.parseInt(process.env.CHATGPT_SESSION_INDEX || "0", 10),
    sessionCount: Number.parseInt(process.env.CHATGPT_SESSION_COUNT || "5", 10),
    sessionLockTimeoutMs: 300000,
    newChat: true,
    json: false,
    raw: false
  };
  const promptParts = [];

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--timeout-ms") {
      options.timeoutMs = parsePositiveInteger(argv[++i], "--timeout-ms");
    } else if (arg === "--stable-rounds") {
      options.stableRounds = parsePositiveInteger(argv[++i], "--stable-rounds");
    } else if (arg === "--stable-interval-ms") {
      options.stableIntervalMs = parsePositiveInteger(argv[++i], "--stable-interval-ms");
    } else if (arg === "--output-dir") {
      options.outputDir = argv[++i];
      if (!options.outputDir) {
        throw new Error("--output-dir の保存先ディレクトリを指定してください。");
      }
    } else if (arg === "--prompt-file") {
      options.promptFile = argv[++i];
      if (!options.promptFile) {
        throw new Error("--prompt-file のパスを指定してください。");
      }
    } else if (arg === "--expected-images") {
      options.expectedImages = parsePositiveInteger(argv[++i], "--expected-images");
    } else if (arg === "--min-dimension") {
      options.minDimension = parsePositiveInteger(argv[++i], "--min-dimension");
    } else if (arg === "--filename-prefix") {
      options.filenamePrefix = argv[++i];
      if (!options.filenamePrefix || /[\\/]/.test(options.filenamePrefix)) {
        throw new Error("--filename-prefix はファイル名として使える文字列で指定してください。");
      }
    } else if (arg === "--session-index") {
      options.sessionIndex = parseNonNegativeInteger(argv[++i], "--session-index");
    } else if (arg === "--session-count") {
      options.sessionCount = parsePositiveInteger(argv[++i], "--session-count");
    } else if (arg === "--session-lock-timeout-ms") {
      options.sessionLockTimeoutMs = parsePositiveInteger(argv[++i], "--session-lock-timeout-ms");
    } else if (arg === "--new-chat") {
      options.newChat = true;
    } else if (arg === "--no-new-chat") {
      options.newChat = false;
    } else if (arg === "--json") {
      options.json = true;
    } else if (arg === "--raw") {
      options.raw = true;
    } else if (arg === "--") {
      promptParts.push(...argv.slice(i + 1));
      break;
    } else {
      promptParts.push(arg);
    }
  }

  if (options.sessionIndex >= options.sessionCount) {
    throw new Error(`--session-index は --session-count 未満にしてください: ${options.sessionIndex} >= ${options.sessionCount}`);
  }

  return { options, argvPrompt: promptParts.join(" ").trim() };
}

async function readStdin() {
  if (process.stdin.isTTY) {
    return "";
  }
  let input = "";
  for await (const chunk of process.stdin) {
    input += chunk;
  }
  return input.trim();
}

async function getPrompt(options, argvPrompt) {
  const filePrompt = options.promptFile ? (await fs.readFile(options.promptFile, "utf8")).trim() : "";
  const stdinPrompt = await readStdin();
  const prompt = argvPrompt || filePrompt || stdinPrompt;
  if (!prompt) {
    throw new Error("画像生成指示を引数、--prompt-file、または標準入力で指定してください。");
  }
  return prompt;
}

async function pageSessionName(page) {
  return page.evaluate(() => window.name || "").catch(() => "");
}

async function findChatPage(browser, options) {
  const context = browser.contexts()[0];
  if (!context) {
    throw new Error("接続先ブラウザにコンテキストがありません。");
  }

  const chatPages = context.pages().filter((candidate) => candidate.url().includes("chatgpt.com"));
  const targetName = `${sessionNamePrefix}${options.sessionIndex}`;
  for (const candidate of chatPages) {
    if ((await pageSessionName(candidate)) === targetName) {
      await candidate.bringToFront();
      await candidate.waitForLoadState("domcontentloaded", { timeout: 10000 }).catch(() => {});
      return candidate;
    }
  }

  throw new Error(`ChatGPT session ${options.sessionIndex} のタブが見つかりません。先に \`npm run chatgpt:open -- --sessions ${options.sessionCount}\` を実行してください。`);
}

async function findEditor(page) {
  const selectors = [
    '[data-testid="composer"] [contenteditable="true"]',
    '#prompt-textarea[contenteditable="true"]',
    '[contenteditable="true"][aria-label="Chat with ChatGPT"]',
    '[contenteditable="true"][aria-label*="ChatGPT"]',
    '[contenteditable="true"]',
    'textarea[aria-label="Chat with ChatGPT"]',
    'textarea[aria-label*="ChatGPT"]:visible',
    "textarea:visible"
  ];
  const deadline = Date.now() + 15000;
  while (Date.now() < deadline) {
    for (const selector of selectors) {
      const candidate = page.locator(selector).last();
      if (await candidate.isVisible({ timeout: 500 }).catch(() => false)) {
        return { selector, locator: candidate };
      }
    }
    await page.waitForTimeout(300);
  }
  throw new Error("ChatGPTの入力欄が見つかりません。ログイン状態と画面表示を確認してください。");
}

async function resetToNewChat(page) {
  await page.goto(process.env.CHATGPT_NEW_CHAT_URL || "https://chatgpt.com/", {
    waitUntil: "domcontentloaded",
    timeout: 15000
  });
  await page.waitForLoadState("domcontentloaded", { timeout: 10000 });
  await page.waitForTimeout(1000);
  await findEditor(page);
  const userCount = await page.locator(userSelector).count().catch(() => -1);
  const assistantCount = await page.locator(assistantSelector).count().catch(() => -1);
  if (userCount !== 0 || assistantCount !== 0) {
    throw new Error(`新規チャット状態を確認できませんでした: user=${userCount} assistant=${assistantCount}`);
  }
}

async function acquireSessionLock(options) {
  await fs.mkdir(stateDir, { recursive: true });
  const lockDir = path.join(stateDir, `session-${options.sessionIndex}.lock`);
  const deadline = Date.now() + options.sessionLockTimeoutMs;
  while (Date.now() < deadline) {
    try {
      await fs.mkdir(lockDir);
      await fs.writeFile(
        path.join(lockDir, "owner.json"),
        `${JSON.stringify({ pid: process.pid, sessionIndex: options.sessionIndex, startedAt: new Date().toISOString() }, null, 2)}\n`,
        "utf8"
      );
      return async () => {
        await fs.rm(lockDir, { recursive: true, force: true }).catch(() => {});
      };
    } catch (error) {
      if (error?.code !== "EEXIST") {
        throw error;
      }
      const stat = await fs.stat(lockDir).catch(() => null);
      if (stat && Date.now() - stat.mtimeMs > Math.max(options.sessionLockTimeoutMs, 600000)) {
        await fs.rm(lockDir, { recursive: true, force: true }).catch(() => {});
        continue;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error(`ChatGPT session ${options.sessionIndex} のlock取得がtimeoutしました。`);
}

async function readEditorText(editor) {
  return editor.locator
    .evaluate((element) => {
      if (element instanceof HTMLTextAreaElement || element instanceof HTMLInputElement) {
        return element.value;
      }
      return element.innerText || element.textContent || "";
    })
    .catch(() => "");
}

function normalizeText(value) {
  return value.replace(/\u00a0/g, " ").replace(/\r\n/g, "\n").replace(/\s+/g, " ").trim();
}

function excerptAround(value, pattern) {
  const text = normalizeText(value || "");
  const match = text.match(pattern);
  if (!match || typeof match.index !== "number") {
    return text.slice(0, 240);
  }
  const start = Math.max(0, match.index - 80);
  const end = Math.min(text.length, match.index + match[0].length + 160);
  return text.slice(start, end);
}

function detectRateLimitText(value) {
  const text = normalizeText(value || "");
  if (!text) {
    return null;
  }
  for (const entry of rateLimitPatterns) {
    if (entry.pattern.test(text)) {
      return {
        code: entry.code,
        excerpt: excerptAround(text, entry.pattern)
      };
    }
  }
  return null;
}

async function fillEditorExactly(page, editor, prompt) {
  await editor.locator.click();
  await editor.locator.fill("");
  await editor.locator.fill(prompt);
  await page.waitForTimeout(300);

  let actual = await readEditorText(editor);
  if (normalizeText(actual) === normalizeText(prompt)) {
    return "fill";
  }

  await editor.locator.click();
  await page.keyboard.press(process.platform === "darwin" ? "Meta+A" : "Control+A");
  await page.keyboard.press("Backspace");
  await page.keyboard.insertText(prompt);
  await page.waitForTimeout(300);
  actual = await readEditorText(editor);
  if (normalizeText(actual) !== normalizeText(prompt)) {
    throw new Error("入力欄へのプロンプト挿入確認に失敗しました。送信を中止します。");
  }
  return "keyboard.insertText";
}

async function clickSend(page) {
  const selectors = [
    'button[data-testid="send-button"]',
    'button[data-testid*="send"]',
    'button[aria-label*="Send"]',
    'button[aria-label*="送信"]',
    'button:has-text("Send")'
  ];
  for (const selector of selectors) {
    const button = page.locator(selector).last();
    if (await button.isVisible({ timeout: 800 }).catch(() => false)) {
      await button.click();
      return selector;
    }
  }
  await page.keyboard.press("Enter");
  return "keyboard:Enter";
}

async function waitForSubmissionAcknowledged(page, beforeUserCount, beforeAssistantCount, timeoutMs) {
  const deadline = Date.now() + Math.min(timeoutMs, 30000);
  while (Date.now() < deadline) {
    const userCount = await page.locator(userSelector).count().catch(() => 0);
    const assistantCount = await page.locator(assistantSelector).count().catch(() => 0);
    if (userCount > beforeUserCount || assistantCount > beforeAssistantCount) {
      return { userCount, assistantCount };
    }
    await page.waitForTimeout(250);
  }
  throw new Error("メッセージ送信後の画面反映を確認できませんでした。");
}

async function getGenerationState(page) {
  return page
    .evaluate(() => {
      const isVisible = (element) => {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== "hidden" && style.display !== "none" && rect.width > 0 && rect.height > 0;
      };
      const controls = Array.from(document.querySelectorAll("button, [role='button']")).map((element) => ({
        testId: element.getAttribute("data-testid") || "",
        ariaLabel: element.getAttribute("aria-label") || "",
        title: element.getAttribute("title") || "",
        text: (element.innerText || element.textContent || "").trim(),
        disabled: Boolean(element.disabled || element.getAttribute("aria-disabled") === "true"),
        visible: isVisible(element)
      }));
      const noticeSelectors = [
        '[role="alert"]',
        "[aria-live]",
        '[data-testid*="toast"]',
        '[data-testid*="error"]',
        '[class*="toast"]'
      ];
      const noticeText = noticeSelectors
        .flatMap((selector) => Array.from(document.querySelectorAll(selector)))
        .filter((element, index, elements) => elements.indexOf(element) === index)
        .filter(isVisible)
        .map((element) => (element.innerText || element.textContent || "").trim())
        .filter(Boolean)
        .join("\n");
      const bodyText = document.body?.innerText || "";
      return { controls, bodyText, noticeText };
    })
    .then((state) => {
      const visibleControls = state.controls.filter((control) => control.visible && !control.disabled);
      const stopControls = visibleControls.filter((control) => {
        const haystack = [control.testId, control.ariaLabel, control.title, control.text].filter(Boolean).join(" ");
        return /stop|停止|中止|cancel|キャンセル/i.test(haystack);
      });
      const bodyGenerating = /generating|creating image|画像を生成|生成中|処理中|uploading|アップロード中/i.test(state.bodyText);
      return {
        generating: stopControls.length > 0,
        bodyGenerating,
        noticeText: state.noticeText,
        stopControls: stopControls.slice(0, 5)
      };
    })
    .catch(() => ({ generating: false, bodyGenerating: false, noticeText: "", stopControls: [] }));
}

async function collectImageCandidates(page, beforeImageSrcs, minDimension) {
  return page.evaluate(
    ({ beforeImageSrcsValue, minDimensionValue }) => {
      const knownSrcs = new Set(beforeImageSrcsValue);
      const candidates = [];
      const images = Array.from(document.querySelectorAll("img"));
      for (const [imageIndex, image] of images.entries()) {
        const src = image.currentSrc || image.src || "";
        const width = image.naturalWidth || image.width || 0;
        const height = image.naturalHeight || image.height || 0;
        const rect = image.getBoundingClientRect();
        const visible = rect.width > 0 && rect.height > 0;
        const alt = image.getAttribute("alt") || "";
        const complete = Boolean(image.complete);
        const validScheme = /^(blob:|data:image\/|https?:\/\/)/.test(src);
        if (
          !validScheme ||
          knownSrcs.has(src) ||
          !visible ||
          width < minDimensionValue ||
          height < minDimensionValue
        ) {
          continue;
        }
        const turn = image.closest("[data-testid^='conversation-turn-']");
        candidates.push({
          id: `${imageIndex}`,
          imageIndex,
          turnTestId: turn?.getAttribute("data-testid") || "",
          src,
          alt,
          width,
          height,
          complete
        });
      }
      const uniqueBySrc = new Map();
      for (const candidate of candidates) {
        const current = uniqueBySrc.get(candidate.src);
        const area = candidate.width * candidate.height;
        const currentArea = current ? current.width * current.height : -1;
        if (!current || area > currentArea || (area === currentArea && candidate.alt && !current.alt)) {
          uniqueBySrc.set(candidate.src, candidate);
        }
      }
      return Array.from(uniqueBySrc.values()).sort((a, b) => b.width * b.height - a.width * a.height);
    },
    {
      beforeImageSrcsValue: beforeImageSrcs,
      minDimensionValue: minDimension
    }
  );
}

function imageSignature(candidates) {
  return candidates.map((item) => `${item.id}:${item.src}:${item.width}x${item.height}:${item.complete}`).join("|");
}

async function latestAssistantText(page) {
  const assistantText = await page.locator(assistantSelector).last().innerText({ timeout: 1000 }).catch(() => "");
  if (assistantText) {
    return assistantText;
  }
  return page
    .locator("[data-testid^='conversation-turn-']")
    .last()
    .innerText({ timeout: 1000 })
    .catch(() => "");
}

async function waitForGeneratedImages(page, beforeImageSrcs, options) {
  const deadline = Date.now() + options.timeoutMs;
  let lastSignature = "";
  let stableRounds = 0;
  let lastCandidates = [];
  let lastText = "";
  let lastGenerationState = null;

  while (Date.now() < deadline) {
    lastText = await latestAssistantText(page);
    const candidates = await collectImageCandidates(page, beforeImageSrcs, options.minDimension).catch(() => []);
    const generationState = await getGenerationState(page);
    const rateLimit = detectRateLimitText(`${lastText}\n${generationState.noticeText || ""}`);
    if (rateLimit) {
      throw new RateLimitedError({
        match: rateLimit,
        candidatesFound: candidates.length,
        expectedImages: options.expectedImages,
        assistantText: lastText,
        noticeText: generationState.noticeText || "",
        generationState
      });
    }
    const signature = imageSignature(candidates);
    const completeEnough =
      candidates.length >= options.expectedImages &&
      candidates.slice(0, options.expectedImages).every((candidate) => candidate.complete);

    if (completeEnough && signature && signature === lastSignature && !generationState.generating) {
      stableRounds += 1;
    } else {
      stableRounds = 0;
      lastSignature = signature;
    }

    lastCandidates = candidates;
    lastGenerationState = generationState;
    if (completeEnough && stableRounds >= options.stableRounds) {
      return {
        candidates: candidates.slice(0, options.expectedImages),
        assistantText: lastText,
        generationState
      };
    }
    await page.waitForTimeout(options.stableIntervalMs);
  }

  throw new Error(
    `画像生成完了を確認できませんでした: found=${lastCandidates.length} expected=${options.expectedImages} generating=${lastGenerationState?.generating ?? "unknown"} text=${lastText.slice(0, 200)}`
  );
}

function extensionForContentType(contentType) {
  const normalized = (contentType || "").toLowerCase().split(";")[0].trim();
  if (normalized === "image/png") return "png";
  if (normalized === "image/jpeg" || normalized === "image/jpg") return "jpg";
  if (normalized === "image/webp") return "webp";
  if (normalized === "image/gif") return "gif";
  return "png";
}

function dataUrlToImage(dataUrl) {
  const match = dataUrl.match(/^data:(image\/[A-Za-z0-9.+-]+);base64,(.+)$/);
  if (!match) {
    throw new Error("未対応のdata URLです。");
  }
  return {
    contentType: match[1],
    buffer: Buffer.from(match[2], "base64"),
    source: "data-url"
  };
}

async function pageFetchImage(page, src) {
  return page.evaluate(async (imageSrc) => {
    const response = await fetch(imageSrc, { credentials: "include" });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    const contentType = response.headers.get("content-type") || "application/octet-stream";
    const arrayBuffer = await response.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);
    let binary = "";
    const chunkSize = 0x8000;
    for (let i = 0; i < bytes.length; i += chunkSize) {
      binary += String.fromCharCode(...bytes.slice(i, i + chunkSize));
    }
    return {
      contentType,
      base64: btoa(binary)
    };
  }, src);
}

async function nodeFetchImage(src) {
  const response = await fetch(src);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  const contentType = response.headers.get("content-type") || "application/octet-stream";
  const arrayBuffer = await response.arrayBuffer();
  return {
    contentType,
    buffer: Buffer.from(arrayBuffer),
    source: "node-fetch"
  };
}

async function downloadImage(page, candidate) {
  if (candidate.src.startsWith("data:image/")) {
    return dataUrlToImage(candidate.src);
  }

  try {
    const fetched = await pageFetchImage(page, candidate.src);
    return {
      contentType: fetched.contentType,
      buffer: Buffer.from(fetched.base64, "base64"),
      source: "page-fetch"
    };
  } catch (pageError) {
    if (candidate.src.startsWith("blob:")) {
      throw new Error(`blob画像の取得に失敗しました: ${pageError.message}`);
    }
    const fetched = await nodeFetchImage(candidate.src);
    return { ...fetched, pageFetchError: pageError.message };
  }
}

async function saveImages(page, candidates, options) {
  const absoluteOutputDir = path.resolve(options.outputDir);
  await fs.mkdir(absoluteOutputDir, { recursive: true });

  const saved = [];
  for (let index = 0; index < candidates.length; index += 1) {
    const candidate = candidates[index];
    const image = await downloadImage(page, candidate);
    const ext = extensionForContentType(image.contentType);
    const filename = `${options.filenamePrefix}_${String(index + 1).padStart(2, "0")}.${ext}`;
    const filePath = path.join(absoluteOutputDir, filename);
    await fs.writeFile(filePath, image.buffer);
    const sha256 = crypto.createHash("sha256").update(image.buffer).digest("hex");
    saved.push({
      filePath,
      filename,
      bytes: image.buffer.length,
      sha256,
      contentType: image.contentType,
      width: candidate.width,
      height: candidate.height,
      alt: candidate.alt,
      downloadSource: image.source,
      pageFetchError: image.pageFetchError || null,
      src: candidate.src.startsWith("data:") ? "data:image/*" : candidate.src
    });
  }
  return saved;
}

async function writeResult(result) {
  await fs.mkdir(stateDir, { recursive: true });
  await fs.mkdir(result.outputDir, { recursive: true });

  const sessionSuffix = Number.isInteger(result.sessionIndex) ? `_session_${result.sessionIndex}` : "";
  const lastJsonPath = path.join(stateDir, `last_image_generation${sessionSuffix}.json`);
  const lastGlobalJsonPath = path.join(stateDir, "last_image_generation.json");
  const metadataPath = path.join(result.outputDir, "metadata.json");

  result.lastJsonPath = lastJsonPath;
  result.metadataPath = metadataPath;
  await fs.writeFile(metadataPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await fs.writeFile(lastJsonPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await fs.writeFile(lastGlobalJsonPath, `${JSON.stringify(result, null, 2)}\n`, "utf8").catch(() => {});
}

function printResult(options, result) {
  if (options.raw) {
    for (const image of result.images) {
      console.log(image.filePath);
    }
    return;
  }
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  console.log("STATUS=OK");
  console.log(`URL=${result.url}`);
  console.log(`SESSION=${result.sessionIndex}/${result.sessionCount}`);
  console.log(`OUTPUT_DIR=${result.outputDir}`);
  console.log(`IMAGES=${result.images.length}`);
  for (const image of result.images) {
    console.log(`IMAGE=${image.filePath}`);
    console.log(`IMAGE_SHA256=${image.sha256}`);
  }
  console.log(`METADATA=${result.metadataPath}`);
  if (result.assistantText) {
    console.log("ASSISTANT_TEXT_START");
    console.log(result.assistantText);
    console.log("ASSISTANT_TEXT_END");
  }
}

function printRateLimitedResult(options, result) {
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  console.log("STATUS=RATE_LIMITED");
  console.log(`URL=${result.url}`);
  console.log(`SESSION=${result.sessionIndex}/${result.sessionCount}`);
  console.log(`OUTPUT_DIR=${result.outputDir}`);
  console.log(`REASON=${result.rateLimit?.code || "unknown"}`);
  console.log(`RETRY_AFTER_MINUTES=${result.rateLimit?.retryAfterMinutes ?? rateLimitRetryAfterMinutes}`);
  if (result.rateLimit?.excerpt) {
    console.log(`EXCERPT=${result.rateLimit.excerpt}`);
  }
  console.log(`METADATA=${result.metadataPath}`);
}

async function main() {
  const { options, argvPrompt } = parseArgs(process.argv.slice(2));
  const prompt = await getPrompt(options, argvPrompt);
  await waitForCdp(10000);

  const releaseLock = await acquireSessionLock(options);
  let browser = null;
  try {
    browser = await chromium.connectOverCDP(cdpBaseUrl);
    const page = await findChatPage(browser, options);
    if (options.newChat) {
      await resetToNewChat(page);
    }

    const beforeAssistantCount = await page.locator(assistantSelector).count().catch(() => 0);
    const beforeUserCount = await page.locator(userSelector).count().catch(() => 0);
    const beforeImages = await collectImageCandidates(page, [], 1).catch(() => []);
    const beforeImageSrcs = beforeImages.map((candidate) => candidate.src);
    const editor = await findEditor(page);
    const inputMethod = await fillEditorExactly(page, editor, prompt);
    const sendMethod = await clickSend(page);
    await waitForSubmissionAcknowledged(page, beforeUserCount, beforeAssistantCount, options.timeoutMs);
    let generated;
    try {
      generated = await waitForGeneratedImages(page, beforeImageSrcs, options);
    } catch (error) {
      if (!(error instanceof RateLimitedError)) {
        throw error;
      }
      const result = {
        ok: false,
        status: "RATE_LIMITED",
        timestamp: new Date().toISOString(),
        url: page.url(),
        sessionIndex: options.sessionIndex,
        sessionCount: options.sessionCount,
        newChat: options.newChat,
        prompt,
        expectedImages: options.expectedImages,
        minDimension: options.minDimension,
        inputMethod,
        sendMethod,
        beforeUserCount,
        beforeAssistantCount,
        assistantText: error.details.assistantText,
        generationState: error.details.generationState,
        rateLimit: {
          code: error.details.match.code,
          excerpt: error.details.match.excerpt,
          retryAfterMinutes: rateLimitRetryAfterMinutes,
          retryAfterAt: new Date(Date.now() + rateLimitRetryAfterMinutes * 60 * 1000).toISOString(),
          candidatesFound: error.details.candidatesFound,
          expectedImages: error.details.expectedImages,
          noticeText: error.details.noticeText
        },
        outputDir: path.resolve(options.outputDir),
        images: []
      };
      await writeResult(result);
      printRateLimitedResult(options, result);
      process.exitCode = 2;
      return;
    }
    const images = await saveImages(page, generated.candidates, options);
    const result = {
      ok: true,
      timestamp: new Date().toISOString(),
      url: page.url(),
      sessionIndex: options.sessionIndex,
      sessionCount: options.sessionCount,
      newChat: options.newChat,
      prompt,
      expectedImages: options.expectedImages,
      minDimension: options.minDimension,
      inputMethod,
      sendMethod,
      beforeUserCount,
      beforeAssistantCount,
      assistantText: generated.assistantText,
      generationState: generated.generationState,
      outputDir: path.resolve(options.outputDir),
      images
    };
    await writeResult(result);
    printResult(options, result);
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
    await releaseLock();
  }
}

main().catch((error) => {
  console.error("STATUS=ERROR");
  console.error(error.message);
  process.exit(1);
});
