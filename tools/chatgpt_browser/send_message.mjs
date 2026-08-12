import fs from "node:fs/promises";
import path from "node:path";
import { chromium } from "playwright";
import { cdpBaseUrl, sessionNamePrefix, stateDir, waitForCdp } from "./config.mjs";

const assistantSelector = "[data-message-author-role='assistant']";
const userSelector = "[data-message-author-role='user']";

function parsePositiveInteger(value, name) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${name} は正の整数で指定してください: ${value}`);
  }
  return parsed;
}

function parseArgs(argv) {
  const options = {
    timeoutMs: 180000,
    stableRounds: 3,
    stableIntervalMs: 2000,
    outputPath: null,
    promptFile: null,
    attachments: [],
    attachTimeoutMs: 60000,
    sessionIndex: Number.parseInt(process.env.CHATGPT_SESSION_INDEX || "0", 10),
    sessionCount: Number.parseInt(process.env.CHATGPT_SESSION_COUNT || "5", 10),
    sessionLockTimeoutMs: 300000,
    newChat: false,
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
    } else if (arg === "--output") {
      options.outputPath = argv[++i];
      if (!options.outputPath) {
        throw new Error("--output の保存先パスを指定してください。");
      }
    } else if (arg === "--prompt-file") {
      options.promptFile = argv[++i];
      if (!options.promptFile) {
        throw new Error("--prompt-file のパスを指定してください。");
      }
    } else if (arg === "--attach") {
      const attachPath = argv[++i];
      if (!attachPath) {
        throw new Error("--attach のファイルパスを指定してください。");
      }
      options.attachments.push(attachPath);
    } else if (arg === "--attach-timeout-ms") {
      options.attachTimeoutMs = parsePositiveInteger(argv[++i], "--attach-timeout-ms");
    } else if (arg === "--session-index") {
      options.sessionIndex = Number.parseInt(argv[++i], 10);
      if (!Number.isInteger(options.sessionIndex) || options.sessionIndex < 0) {
        throw new Error(`--session-index は0以上の整数で指定してください: ${options.sessionIndex}`);
      }
    } else if (arg === "--session-count") {
      options.sessionCount = parsePositiveInteger(argv[++i], "--session-count");
    } else if (arg === "--session-lock-timeout-ms") {
      options.sessionLockTimeoutMs = parsePositiveInteger(argv[++i], "--session-lock-timeout-ms");
    } else if (arg === "--new-chat") {
      options.newChat = true;
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

  if (!Number.isInteger(options.sessionIndex) || options.sessionIndex < 0) {
    throw new Error(`CHATGPT_SESSION_INDEX/--session-index は0以上の整数で指定してください: ${options.sessionIndex}`);
  }
  if (!Number.isInteger(options.sessionCount) || options.sessionCount <= 0) {
    throw new Error(`CHATGPT_SESSION_COUNT/--session-count は正の整数で指定してください: ${options.sessionCount}`);
  }
  if (options.sessionIndex >= options.sessionCount) {
    throw new Error(`--session-index は --session-count 未満にしてください: ${options.sessionIndex} >= ${options.sessionCount}`);
  }

  return { options, argvPrompt: promptParts.join(" ").trim() };
}

async function resolveAttachments(attachments) {
  const resolved = [];
  for (const attachment of attachments) {
    const absolutePath = path.resolve(attachment);
    const stat = await fs.stat(absolutePath).catch((error) => {
      throw new Error(`添付ファイルを確認できません: ${attachment}: ${error.message}`);
    });
    if (!stat.isFile()) {
      throw new Error(`添付対象は通常ファイルである必要があります: ${attachment}`);
    }
    resolved.push({ input: attachment, path: absolutePath, size: stat.size });
  }
  return resolved;
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
    throw new Error("送信するメッセージを引数、--prompt-file、または標準入力で指定してください。");
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
  let page = null;
  for (const candidate of chatPages) {
    if ((await pageSessionName(candidate)) === targetName) {
      page = candidate;
      break;
    }
  }

  if (!page) {
    throw new Error(`ChatGPT session ${options.sessionIndex} のタブが見つかりません。先に \`npm run chatgpt:open -- --sessions ${options.sessionCount}\` を実行してください。`);
  }

  await page.bringToFront();
  await page.waitForLoadState("domcontentloaded", { timeout: 10000 }).catch(() => {});
  if (!page.url().includes("chatgpt.com")) {
    throw new Error(`ChatGPT session ${options.sessionIndex} のURLがchatgpt.comではありません: ${page.url()}`);
  }
  const actualName = await pageSessionName(page);
  if (actualName !== targetName) {
    throw new Error(`ChatGPT session ${options.sessionIndex} のタブ識別に失敗しました: ${actualName || "-"}`);
  }
  return page;
}

async function resetToNewChat(page) {
  await page.goto(process.env.CHATGPT_NEW_CHAT_URL || "https://chatgpt.com/", {
    waitUntil: "domcontentloaded",
    timeout: 15000
  });
  await page.waitForLoadState("domcontentloaded", { timeout: 10000 });
  await page.waitForTimeout(1000);
  if (!page.url().startsWith("https://chatgpt.com/")) {
    throw new Error(`新規チャット遷移後のURLが不正です: ${page.url()}`);
  }
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
  return value
    .replace(/\u00a0/g, " ")
    .replace(/\r\n/g, "\n")
    .replace(/\s+/g, " ")
    .trim();
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
  const isMac = process.platform === "darwin";
  await page.keyboard.press(isMac ? "Meta+A" : "Control+A");
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

async function waitForAttachmentsReady(page, files, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const names = files.map((item) => path.basename(item.path));

  while (Date.now() < deadline) {
    const state = await page.evaluate((expectedNames) => {
      const bodyText = document.body?.innerText || "";
      const visibleNames = expectedNames.filter((name) => bodyText.includes(name));
      const uploadTextVisible = /uploading|アップロード中|処理中/i.test(bodyText);
      const disabledSend = Boolean(document.querySelector('button[data-testid="send-button"][disabled]'));
      return { visibleNames, uploadTextVisible, disabledSend };
    }, names);

    if (state.visibleNames.length >= names.length && !state.uploadTextVisible && !state.disabledSend) {
      await page.waitForTimeout(1000);
      return;
    }
    await page.waitForTimeout(500);
  }

  throw new Error(`添付ファイルのアップロード完了を確認できませんでした: ${names.join(", ")}`);
}

async function uploadAttachments(page, attachments, timeoutMs) {
  if (!attachments.length) {
    return { method: "none", files: [] };
  }

  const resolved = await resolveAttachments(attachments);
  const selectors = [
    'input[type="file"]#upload-files',
    'input[type="file"][multiple]:not([accept="image/*"])',
    'input[type="file"]'
  ];

  let input = null;
  let selectorUsed = null;
  for (const selector of selectors) {
    const candidate = page.locator(selector).first();
    if ((await candidate.count().catch(() => 0)) > 0) {
      input = candidate;
      selectorUsed = selector;
      break;
    }
  }

  if (!input) {
    const plusButton = page
      .locator('button[data-testid="composer-plus-btn"], button[aria-label*="ファイル"], button[aria-label*="Attach"], button[aria-label*="Upload"]')
      .first();
    if (await plusButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await plusButton.click();
      await page.waitForTimeout(500);
    }
    for (const selector of selectors) {
      const candidate = page.locator(selector).first();
      if ((await candidate.count().catch(() => 0)) > 0) {
        input = candidate;
        selectorUsed = selector;
        break;
      }
    }
  }

  if (!input) {
    throw new Error("ChatGPTのファイル添付inputが見つかりません。");
  }

  await input.setInputFiles(resolved.map((item) => item.path));
  await waitForAttachmentsReady(page, resolved, timeoutMs);
  return { method: selectorUsed, files: resolved };
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

async function isGenerating(page) {
  return page
    .locator('button[data-testid="stop-button"], button[aria-label*="Stop generating"], button[aria-label*="Stop streaming"]')
    .first()
    .isVisible({ timeout: 300 })
    .catch(() => false);
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

    if (text && text === lastText && !(await isGenerating(page))) {
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

async function writeOutputs(options, result) {
  await fs.mkdir(stateDir, { recursive: true });
  const sessionSuffix = Number.isInteger(result.sessionIndex) ? `_session_${result.sessionIndex}` : "";
  const lastResponsePath = path.join(stateDir, `last_response${sessionSuffix}.txt`);
  const lastJsonPath = path.join(stateDir, `last_response${sessionSuffix}.json`);
  result.lastResponsePath = lastResponsePath;
  result.lastJsonPath = lastJsonPath;

  await fs.writeFile(lastResponsePath, result.responseText, "utf8");
  const jsonTmpPath = `${lastJsonPath}.${process.pid}.tmp`;
  await fs.writeFile(jsonTmpPath, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  await fs.rename(jsonTmpPath, lastJsonPath);

  const globalResponsePath = path.join(stateDir, "last_response.txt");
  const globalJsonPath = path.join(stateDir, "last_response.json");
  const globalJsonTmpPath = `${globalJsonPath}.${process.pid}.tmp`;
  await fs.writeFile(globalResponsePath, result.responseText, "utf8").catch(() => {});
  await fs.writeFile(globalJsonTmpPath, `${JSON.stringify(result, null, 2)}\n`, "utf8").catch(() => {});
  await fs.rename(globalJsonTmpPath, globalJsonPath).catch(() => {});

  if (options.outputPath) {
    await fs.mkdir(path.dirname(path.resolve(options.outputPath)), { recursive: true });
    await fs.writeFile(options.outputPath, result.responseText, "utf8");
  }

  return { lastResponsePath, lastJsonPath };
}

function printResult(options, result) {
  if (options.raw) {
    console.log(result.responseText);
    return;
  }

  if (options.json) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  console.log("STATUS=OK");
  console.log(`URL=${result.url}`);
  console.log(`SESSION=${result.sessionIndex}/${result.sessionCount}`);
  console.log(`EDITOR=${result.editorSelector}`);
  console.log(`INPUT_METHOD=${result.inputMethod}`);
  console.log(`SEND=${result.sendMethod}`);
  if (result.attachments?.length) {
    console.log(`ATTACH=${result.attachments.length}`);
    for (const attachment of result.attachments) {
      console.log(`ATTACH_FILE=${attachment.path}`);
    }
  }
  console.log(`USER_MESSAGES=${result.beforeUserCount}->${result.afterUserCount}`);
  console.log(`ASSISTANT_MESSAGES=${result.beforeAssistantCount}->${result.afterAssistantCount}`);
  console.log(`LAST_RESPONSE=${result.lastResponsePath}`);
  console.log(`LAST_JSON=${result.lastJsonPath}`);
  if (result.outputPath) {
    console.log(`OUTPUT=${result.outputPath}`);
  }
  console.log("RESPONSE_START");
  console.log(result.responseText);
  console.log("RESPONSE_END");
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
    const editor = await findEditor(page);

    const attachmentResult = await uploadAttachments(page, options.attachments, options.attachTimeoutMs);
    const inputMethod = await fillEditorExactly(page, editor, prompt);
    const sendMethod = await clickSend(page);
    await waitForSubmissionAcknowledged(page, beforeUserCount, beforeAssistantCount, options.timeoutMs);
    const responseText = await waitForAssistantResponse(page, beforeAssistantCount, options);
    const afterUserCount = await page.locator(userSelector).count().catch(() => beforeUserCount);
    const afterAssistantCount = await page.locator(assistantSelector).count().catch(() => beforeAssistantCount);

    const result = {
      ok: true,
      url: page.url(),
      sessionIndex: options.sessionIndex,
      sessionCount: options.sessionCount,
      newChat: options.newChat,
      timestamp: new Date().toISOString(),
      prompt,
      editorSelector: editor.selector,
      inputMethod,
      sendMethod,
      attachmentMethod: attachmentResult.method,
      attachments: attachmentResult.files,
      beforeUserCount,
      afterUserCount,
      beforeAssistantCount,
      afterAssistantCount,
      responseText,
      outputPath: options.outputPath
    };
    await writeOutputs(options, result);

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
