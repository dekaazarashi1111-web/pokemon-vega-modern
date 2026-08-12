import fs from "node:fs/promises";
import crypto from "node:crypto";
import path from "node:path";
import { chromium } from "playwright";
import { cdpBaseUrl, stateDir, waitForCdp } from "./config.mjs";

const assistantSelector = "[data-message-author-role='assistant']";
const userSelector = "[data-message-author-role='user']";
const messageSelector = "[data-message-author-role]";
const generatingButtonPattern = /(stop|停止|中止|cancel|キャンセル|generating|streaming|responding|回答|応答|生成)/i;

function parsePositiveInteger(value, name) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${name} は正の整数で指定してください: ${value}`);
  }
  return parsed;
}

function normalizeConversationUrl(value) {
  if (!value) {
    throw new Error("--url にChatGPT会話URLを指定してください。");
  }
  const url = new URL(value);
  if (url.hostname !== "chatgpt.com" || !url.pathname.startsWith("/c/")) {
    throw new Error(`ChatGPT会話URLではありません: ${value}`);
  }
  return url.toString();
}

function conversationIdFromUrl(value) {
  const match = value.match(/\/c\/([^/?#]+)/);
  if (!match) {
    throw new Error(`会話IDをURLから取得できません: ${value}`);
  }
  return match[1];
}

function parseArgs(argv) {
  const options = {
    url: null,
    mode: "read",
    timeoutMs: 180000,
    stableRounds: 3,
    stableIntervalMs: 2000,
    lockTimeoutMs: 300000,
    outputPath: null,
    json: false,
    raw: false,
    allowPartial: false,
    lastOnly: false,
    tail: null,
    waitNew: false
  };
  const promptParts = [];

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--url") {
      options.url = normalizeConversationUrl(argv[++i]);
    } else if (arg === "--read") {
      options.mode = "read";
    } else if (arg === "--send") {
      options.mode = "send";
    } else if (arg === "--timeout-ms") {
      options.timeoutMs = parsePositiveInteger(argv[++i], "--timeout-ms");
    } else if (arg === "--stable-rounds") {
      options.stableRounds = parsePositiveInteger(argv[++i], "--stable-rounds");
    } else if (arg === "--stable-interval-ms") {
      options.stableIntervalMs = parsePositiveInteger(argv[++i], "--stable-interval-ms");
    } else if (arg === "--lock-timeout-ms") {
      options.lockTimeoutMs = parsePositiveInteger(argv[++i], "--lock-timeout-ms");
    } else if (arg === "--output") {
      options.outputPath = argv[++i];
      if (!options.outputPath) {
        throw new Error("--output の保存先パスを指定してください。");
      }
    } else if (arg === "--json") {
      options.json = true;
    } else if (arg === "--raw") {
      options.raw = true;
    } else if (arg === "--allow-partial") {
      options.allowPartial = true;
    } else if (arg === "--last-only") {
      options.lastOnly = true;
    } else if (arg === "--tail") {
      options.tail = parsePositiveInteger(argv[++i], "--tail");
    } else if (arg === "--wait-new") {
      options.waitNew = true;
    } else if (arg === "--") {
      promptParts.push(...argv.slice(i + 1));
      break;
    } else {
      options.mode = "send";
      promptParts.push(arg);
    }
  }

  if (!options.url) {
    throw new Error("--url は必須です。");
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
  const stdinPrompt = await readStdin();
  const prompt = argvPrompt || stdinPrompt;
  if (options.mode === "send" && !prompt) {
    throw new Error("送信するメッセージを引数または標準入力で指定してください。");
  }
  return prompt;
}

async function acquireConversationLock(conversationId, timeoutMs) {
  await fs.mkdir(stateDir, { recursive: true });
  const lockDir = path.join(stateDir, `conversation-${conversationId}.lock`);
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      await fs.mkdir(lockDir);
      await fs.writeFile(
        path.join(lockDir, "owner.json"),
        `${JSON.stringify({ pid: process.pid, conversationId, startedAt: new Date().toISOString() }, null, 2)}\n`,
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
      if (stat && Date.now() - stat.mtimeMs > Math.max(timeoutMs, 600000)) {
        await fs.rm(lockDir, { recursive: true, force: true }).catch(() => {});
        continue;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
    }
  }
  throw new Error(`ChatGPT conversation ${conversationId} のlock取得がtimeoutしました。`);
}

async function findOrOpenConversationPage(browser, url) {
  const context = browser.contexts()[0];
  if (!context) {
    throw new Error("接続先ブラウザにコンテキストがありません。");
  }
  const id = conversationIdFromUrl(url);
  let page = context.pages().find((candidate) => candidate.url().includes(`/c/${id}`));
  if (!page) {
    page = await context.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }).catch(() => {});
  }
  await page.bringToFront().catch(() => {});
  await page.waitForLoadState("domcontentloaded", { timeout: 30000 }).catch(() => {});
  return page;
}

async function waitForConversationReadable(page, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const state = await page
      .evaluate(() => ({
        title: document.title,
        messageCount: document.querySelectorAll("[data-message-author-role]").length,
        bodyTextLength: document.body?.innerText?.length || 0,
        hasComposer: Boolean(document.querySelector('textarea, [contenteditable="true"], div.ProseMirror'))
      }))
      .catch(() => ({ title: "", messageCount: 0, bodyTextLength: 0, hasComposer: false }));
    if (state.messageCount > 0 && state.hasComposer) {
      return state;
    }
    await page.waitForTimeout(500);
  }
  throw new Error("ChatGPT会話本文を読み取れる状態になりませんでした。");
}

async function extractConversation(page) {
  await waitForConversationReadable(page, 30000);
  const generationState = await getGenerationState(page);
  const conversation = await page.evaluate(() => {
    const messages = Array.from(document.querySelectorAll("[data-message-author-role]")).map((element, index) => ({
      index,
      role: element.getAttribute("data-message-author-role") || "",
      text: (element.innerText || element.textContent || "").trim()
    }));
    return {
      title: document.title,
      url: location.href,
      timestamp: new Date().toISOString(),
      messageCount: messages.length,
      messages
    };
  });
  return { ...conversation, generationState, generating: generationState.generating };
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
  throw new Error("ChatGPTの入力欄が見つかりません。");
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

function hashText(value) {
  return crypto.createHash("sha256").update(value || "", "utf8").digest("hex");
}

function safeConversationId(conversationId) {
  return conversationId.replace(/[^A-Za-z0-9_-]/g, "_");
}

function conversationStatePath(conversationId) {
  return path.join(stateDir, `conversation_${safeConversationId(conversationId)}_state.json`);
}

async function readConversationState(conversationId) {
  const statePath = conversationStatePath(conversationId);
  const raw = await fs.readFile(statePath, "utf8").catch(() => "");
  if (!raw) {
    return { statePath, state: null };
  }
  try {
    return { statePath, state: JSON.parse(raw) };
  } catch {
    return { statePath, state: null };
  }
}

function getLastAssistantMessage(messages) {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    if (messages[i]?.role === "assistant") {
      return messages[i];
    }
  }
  return null;
}

function outputScopeFor(options) {
  if (options.lastOnly || options.waitNew) {
    return "last-assistant";
  }
  if (options.tail) {
    return "tail";
  }
  return "full";
}

function selectOutputMessages(messages, options) {
  if (options.lastOnly || options.waitNew) {
    const lastAssistant = getLastAssistantMessage(messages);
    return lastAssistant ? [lastAssistant] : [];
  }
  if (options.tail) {
    return messages.slice(-options.tail);
  }
  return messages;
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

function looksLikeGeneratingControl(control) {
  const haystack = [
    control.testId,
    control.ariaLabel,
    control.title,
    control.text,
    control.htmlClass
  ]
    .filter(Boolean)
    .join(" ");
  if (!generatingButtonPattern.test(haystack)) {
    return false;
  }
  return /stop|停止|中止|cancel|キャンセル/.test(haystack.toLowerCase()) || /停止|中止|キャンセル/.test(haystack);
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
        tagName: element.tagName,
        testId: element.getAttribute("data-testid") || "",
        ariaLabel: element.getAttribute("aria-label") || "",
        title: element.getAttribute("title") || "",
        text: (element.innerText || element.textContent || "").trim(),
        htmlClass: element.getAttribute("class") || "",
        disabled: Boolean(element.disabled || element.getAttribute("aria-disabled") === "true"),
        visible: isVisible(element)
      }));
      const visibleControls = controls.filter((control) => control.visible && !control.disabled);
      const bodyText = document.body?.innerText || "";
      const streamingTextVisible = /generating|streaming|stop generating|stop streaming|回答を停止|応答を停止|生成を停止|停止する/i.test(bodyText);
      return { visibleControls, streamingTextVisible };
    })
    .then((state) => {
      const stopControls = state.visibleControls.filter(looksLikeGeneratingControl);
      return {
        generating: stopControls.length > 0,
        stopControls: stopControls.slice(0, 5),
        streamingTextVisible: state.streamingTextVisible,
        streamingTextIgnoredWithoutStopControl: state.streamingTextVisible && stopControls.length === 0
      };
    })
    .catch(() => ({ generating: false, stopControls: [], streamingTextVisible: false }));
}

async function isGenerating(page) {
  const state = await getGenerationState(page);
  return state.generating;
}

async function waitForAssistantResponse(page, beforeAssistantCount, options) {
  const deadline = Date.now() + options.timeoutMs;
  let currentCount = beforeAssistantCount;
  while (Date.now() < deadline) {
    currentCount = await page.locator(assistantSelector).count().catch(() => 0);
    if (currentCount > beforeAssistantCount) {
      break;
    }
    await page.waitForTimeout(500);
  }
  if (currentCount <= beforeAssistantCount) {
    throw new Error("ChatGPTの返信開始を確認できませんでした。");
  }
  let lastText = "";
  let stableRounds = 0;
  while (Date.now() < deadline) {
    const messages = page.locator(assistantSelector);
    const count = await messages.count();
    const text = (await messages.nth(count - 1).innerText().catch(() => "")).trim();
    const generationState = await getGenerationState(page);
    if (text && text === lastText && !generationState.generating) {
      stableRounds += 1;
    } else {
      stableRounds = 0;
      lastText = text;
    }
    if (text && stableRounds >= options.stableRounds) {
      return text;
    }
    await page.waitForTimeout(options.stableIntervalMs);
  }
  if (!lastText) {
    throw new Error("ChatGPTの返信本文を取得できませんでした。");
  }
  return lastText;
}

async function waitForConversationIdle(page, options) {
  if (options.allowPartial) {
    return { idle: false, skipped: true };
  }
  const deadline = Date.now() + options.timeoutMs;
  let lastText = "";
  let stableRounds = 0;
  while (Date.now() < deadline) {
    const messages = page.locator(assistantSelector);
    const count = await messages.count().catch(() => 0);
    const text = count > 0 ? (await messages.nth(count - 1).innerText().catch(() => "")).trim() : "";
    const generationState = await getGenerationState(page);
    if (!generationState.generating && text && text === lastText) {
      stableRounds += 1;
    } else {
      stableRounds = 0;
      lastText = text;
    }
    if (!generationState.generating && stableRounds >= options.stableRounds) {
      return { idle: true, skipped: false };
    }
    await page.waitForTimeout(options.stableIntervalMs);
  }
  throw new Error("ChatGPT会話が生成完了状態になりませんでした。必要なら --allow-partial で途中本文を明示取得してください。");
}

async function waitForNewAssistantReply(page, beforeAssistantCount, options) {
  const text = await waitForAssistantResponse(page, beforeAssistantCount, options);
  return { responseText: text, beforeAssistantCount };
}

async function sendMessage(page, prompt, options) {
  const beforeAssistantCount = await page.locator(assistantSelector).count().catch(() => 0);
  const beforeUserCount = await page.locator(userSelector).count().catch(() => 0);
  const editor = await findEditor(page);
  const inputMethod = await fillEditorExactly(page, editor, prompt);
  const sendMethod = await clickSend(page);
  const responseText = await waitForAssistantResponse(page, beforeAssistantCount, options);
  const afterAssistantCount = await page.locator(assistantSelector).count().catch(() => beforeAssistantCount);
  const afterUserCount = await page.locator(userSelector).count().catch(() => beforeUserCount);
  return {
    prompt,
    inputMethod,
    sendMethod,
    beforeUserCount,
    afterUserCount,
    beforeAssistantCount,
    afterAssistantCount,
    responseText
  };
}

function buildResult(options, conversationId, before, after, sendResult = {}) {
  const lastAssistantMessage = getLastAssistantMessage(after.messages);
  const lastAssistantText = lastAssistantMessage?.text || sendResult.responseText || "";
  const messages = selectOutputMessages(after.messages, options);
  const assistantMessageCount = after.messages.filter((message) => message.role === "assistant").length;
  return {
    ok: true,
    mode: options.mode,
    conversationId,
    title: after.title,
    url: after.url,
    timestamp: new Date().toISOString(),
    messageCount: after.messageCount,
    assistantMessageCount,
    savedMessageCount: messages.length,
    messagesTruncated: messages.length !== after.messages.length,
    outputScope: outputScopeFor(options),
    lastOnly: options.lastOnly,
    tail: options.tail,
    waitNew: options.waitNew,
    messages,
    lastAssistantMessage,
    lastAssistantText,
    lastAssistantTextHash: hashText(lastAssistantText),
    generating: after.generating,
    generationState: after.generationState,
    beforeMessageCount: before.messageCount,
    beforeAssistantMessageCount: before.assistantMessageCount ?? null,
    ...sendResult
  };
}

function textForResult(result) {
  if (result.mode === "send") {
    return result.responseText || result.lastAssistantText || "";
  }
  if (result.outputScope === "last-assistant") {
    return result.lastAssistantText || "";
  }
  return result.messages.map((message) => `${message.role}: ${message.text}`).join("\n\n");
}

async function writeConversationState(conversationId, result) {
  const statePath = conversationStatePath(conversationId);
  const state = {
    conversationId,
    url: result.url,
    title: result.title,
    updatedAt: result.timestamp,
    mode: result.mode,
    lastMessageCount: result.messageCount,
    lastAssistantCount: result.assistantMessageCount,
    lastAssistantMessageIndex: result.lastAssistantMessage?.index ?? null,
    lastAssistantTextHash: result.lastAssistantTextHash,
    lastJsonPath: result.lastJsonPath || null,
    lastTextPath: result.lastTextPath || null
  };
  const tmpPath = `${statePath}.${process.pid}.tmp`;
  await fs.writeFile(tmpPath, `${JSON.stringify(state, null, 2)}\n`, "utf8");
  await fs.rename(tmpPath, statePath);
  result.statePath = statePath;
}

async function writeResult(options, conversationId, result) {
  await fs.mkdir(stateDir, { recursive: true });
  const safeId = safeConversationId(conversationId);
  const jsonPath = path.join(stateDir, `conversation_${safeId}_last.json`);
  const textPath = path.join(stateDir, `conversation_${safeId}_last.txt`);
  const text = textForResult(result);
  result.lastJsonPath = jsonPath;
  result.lastTextPath = textPath;
  result.statePath = conversationStatePath(conversationId);
  await fs.writeFile(`${jsonPath}.${process.pid}.tmp`, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await fs.rename(`${jsonPath}.${process.pid}.tmp`, jsonPath);
  await fs.writeFile(`${textPath}.${process.pid}.tmp`, text, "utf8");
  await fs.rename(`${textPath}.${process.pid}.tmp`, textPath);
  if (options.outputPath) {
    await fs.mkdir(path.dirname(path.resolve(options.outputPath)), { recursive: true });
    await fs.writeFile(options.outputPath, text, "utf8");
  }
  await writeConversationState(conversationId, result);
}

function printResult(options, result) {
  if (options.raw) {
    console.log(textForResult(result));
    return;
  }
  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }
  console.log("STATUS=OK");
  console.log(`MODE=${result.mode}`);
  console.log(`TITLE=${result.title}`);
  console.log(`URL=${result.url}`);
  console.log(`MESSAGES=${result.messageCount}`);
  console.log(`SAVED_MESSAGES=${result.savedMessageCount}`);
  console.log(`OUTPUT_SCOPE=${result.outputScope}`);
  console.log(`GENERATING=${Boolean(result.generating)}`);
  console.log(`LAST_JSON=${result.lastJsonPath}`);
  console.log(`LAST_TEXT=${result.lastTextPath}`);
  if (result.statePath) {
    console.log(`STATE=${result.statePath}`);
  }
  if (result.mode === "send") {
    console.log("RESPONSE_START");
    console.log(textForResult(result));
    console.log("RESPONSE_END");
  } else if (result.outputScope === "last-assistant") {
    console.log("RESPONSE_START");
    console.log(result.lastAssistantText || "");
    console.log("RESPONSE_END");
  }
}

async function main() {
  const { options, argvPrompt } = parseArgs(process.argv.slice(2));
  const prompt = await getPrompt(options, argvPrompt);
  const conversationId = conversationIdFromUrl(options.url);
  await waitForCdp(10000);

  let releaseLock = async () => {};
  if (options.mode === "send" || options.waitNew) {
    releaseLock = await acquireConversationLock(conversationId, options.lockTimeoutMs);
  }

  let browser = null;
  try {
    browser = await chromium.connectOverCDP(cdpBaseUrl);
    const page = await findOrOpenConversationPage(browser, options.url);
    await waitForConversationReadable(page, Math.min(options.timeoutMs, 60000));
    const previousState = await readConversationState(conversationId);
    if (options.mode === "read" && !options.waitNew) {
      await waitForConversationIdle(page, options);
    }
    const before = await extractConversation(page);
    before.assistantMessageCount = before.messages.filter((message) => message.role === "assistant").length;
    let sendResult = {};
    if (options.mode === "read" && options.waitNew) {
      const stateAssistantCount = Number.parseInt(previousState.state?.lastAssistantCount ?? "", 10);
      const beforeAssistantCount = before.assistantMessageCount;
      const beforeLastAssistantText = getLastAssistantMessage(before.messages)?.text || "";
      const beforeLastAssistantHash = hashText(beforeLastAssistantText);
      const stateLastAssistantHash = previousState.state?.lastAssistantTextHash || "";
      const baselineAssistantCount =
        Number.isInteger(stateAssistantCount) && stateAssistantCount >= 0
          ? Math.min(stateAssistantCount, beforeAssistantCount)
          : beforeAssistantCount;
      if (
        stateLastAssistantHash &&
        beforeLastAssistantText &&
        beforeAssistantCount === baselineAssistantCount &&
        beforeLastAssistantHash !== stateLastAssistantHash
      ) {
        sendResult = {
          responseText: beforeLastAssistantText,
          beforeAssistantCount: baselineAssistantCount,
          afterAssistantCount: beforeAssistantCount,
          reusedUnreadState: true,
          detectedSameCountHashChange: true
        };
      } else if (beforeAssistantCount <= baselineAssistantCount) {
        sendResult = await waitForNewAssistantReply(page, beforeAssistantCount, options);
      } else {
        sendResult = {
          responseText: beforeLastAssistantText,
          beforeAssistantCount: baselineAssistantCount,
          afterAssistantCount: beforeAssistantCount,
          reusedUnreadState: true
        };
      }
    }
    if (options.mode === "send") {
      sendResult = await sendMessage(page, prompt, options);
    }
    await waitForConversationIdle(page, options);
    const after = await extractConversation(page);
    const result = buildResult(options, conversationId, before, after, sendResult);
    await writeResult(options, conversationId, result);
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
