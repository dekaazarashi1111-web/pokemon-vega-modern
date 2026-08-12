import fs from "node:fs";
import { spawn } from "node:child_process";
import { chromium } from "playwright";
import {
  cdpBaseUrl,
  cdpPort,
  listPages,
  loginUrl,
  profileDir,
  sessionNamePrefix,
  stateDir,
  waitForCdp
} from "./config.mjs";

function parsePositiveInteger(value, name) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    throw new Error(`${name} は正の整数で指定してください: ${value}`);
  }
  return parsed;
}

function parseArgs(argv) {
  const options = { sessions: 5 };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--sessions") {
      options.sessions = parsePositiveInteger(argv[++i], "--sessions");
    } else {
      throw new Error(`未知の引数です: ${arg}`);
    }
  }
  return options;
}

async function isBrowserRunning() {
  try {
    await waitForCdp(1500);
    return true;
  } catch {
    return false;
  }
}

async function openNewTab(url) {
  const response = await fetch(`${cdpBaseUrl}/json/new?${encodeURIComponent(url)}`, {
    method: "PUT"
  });
  if (!response.ok) {
    throw new Error(`新規タブ作成に失敗しました: ${response.status} ${response.statusText}`);
  }
}

async function waitForChatGptPage(timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const pages = await listPages();
    const page = pages.find((candidate) => (candidate.url || "").includes("chatgpt.com"));
    if (page) {
      return page;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error("ChatGPTタブを確認できませんでした。");
}

async function waitForChatGptPages(count, timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {
    const pages = await listPages();
    const chatgptPages = pages.filter((candidate) => (candidate.url || "").includes("chatgpt.com"));
    if (chatgptPages.length >= count) {
      return chatgptPages;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error(`ChatGPTタブを${count}個確認できませんでした。`);
}

async function ensureChatGptTabs(count) {
  await waitForCdp(30000);
  let pages = await listPages();
  let chatgptPages = pages.filter((candidate) => (candidate.url || "").includes("chatgpt.com"));
  for (let index = chatgptPages.length; index < count; index += 1) {
    await openNewTab(`${loginUrl}${loginUrl.includes("?") ? "&" : "?"}codex_loop_session=${index + 1}-${Date.now()}`);
  }
  chatgptPages = await waitForChatGptPages(count, 30000);

  const browser = await chromium.connectOverCDP(cdpBaseUrl);
  const context = browser.contexts()[0];
  const livePages = (context?.pages() || []).filter((page) => page.url().includes("chatgpt.com"));
  for (let index = 0; index < Math.min(count, livePages.length); index += 1) {
    const page = livePages[index];
    await page.waitForLoadState("domcontentloaded", { timeout: 10000 }).catch(() => {});
    await page.evaluate((name) => {
      window.name = name;
    }, `${sessionNamePrefix}${index}`).catch(() => {});
  }
  await browser.close();
  return chatgptPages;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  fs.mkdirSync(stateDir, { recursive: true });
  fs.mkdirSync(profileDir, { recursive: true });

  const executablePath = chromium.executablePath();
  if (!fs.existsSync(executablePath)) {
    throw new Error("PlaywrightのChromiumが見つかりません。先に `npx playwright install chromium` を実行してください。");
  }

  if (await isBrowserRunning()) {
    await openNewTab(loginUrl);
  } else {
    const child = spawn(executablePath, [
      `--user-data-dir=${profileDir}`,
      `--remote-debugging-port=${cdpPort}`,
      "--no-first-run",
      "--no-default-browser-check",
      "--disable-dev-shm-usage",
      "--new-window",
      loginUrl
    ], {
      detached: true,
      stdio: "ignore"
    });
    child.unref();
    fs.writeFileSync(`${stateDir}/browser.pid`, `${child.pid}\n`, "utf8");
  }

  await waitForCdp(30000);
  await ensureChatGptTabs(options.sessions);
  const page = await waitForChatGptPage(30000);

  console.log("STATUS=LOGIN_SCREEN_READY");
  console.log(`TITLE=${page.title || "-"}`);
  console.log(`URL=${page.url || "-"}`);
  console.log(`SESSIONS=${options.sessions}`);
  console.log(`PROFILE_DIR=${profileDir}`);
  console.log(`CDP=${cdpBaseUrl}`);
}

main().catch((error) => {
  console.error("STATUS=ERROR");
  console.error(error.message);
  process.exit(1);
});
