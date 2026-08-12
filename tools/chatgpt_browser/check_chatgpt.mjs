import { chromium } from "playwright";
import { cdpBaseUrl, listPages, waitForCdp } from "./config.mjs";

async function inspectLivePage(targetMeta) {
  const browser = await chromium.connectOverCDP(cdpBaseUrl);
  const context = browser.contexts()[0];
  const pages = context?.pages() || [];
  const page =
    pages.find((candidate) => candidate.url().includes("chatgpt.com")) ||
    pages.find((candidate) => candidate.url() === targetMeta.url) ||
    pages[0];

  if (!page) {
    return { title: targetMeta.title || "-", url: targetMeta.url || "-", hasLoginText: false, hasComposer: false };
  }

  await page.waitForLoadState("domcontentloaded", { timeout: 5000 }).catch(() => {});
  await page.waitForTimeout(500);

  const title = await page.title().catch(() => targetMeta.title || "-");
  const url = page.url();
  const hasLoginText = await page
    .locator("text=/Log in|ログイン|Sign up|新規登録|Continue with Google|メールアドレス|Email/i")
    .first()
    .isVisible({ timeout: 1500 })
    .catch(() => false);
  const hasComposer = await page
    .locator("textarea, [contenteditable='true'], [data-testid*='composer']")
    .first()
    .isVisible({ timeout: 1500 })
    .catch(() => false);

  return { title, url, hasLoginText, hasComposer };
}

function classifyPage({ url, title, hasLoginText, hasComposer }) {
  url ||= "";
  title ||= "";

  if (url.includes("/auth/login") || url.includes("/auth")) {
    return "LOGIN_REQUIRED";
  }

  if (hasLoginText) {
    return "LOGIN_REQUIRED";
  }

  if (hasComposer && url.startsWith("https://chatgpt.com/")) {
    return "CHATGPT_READY";
  }

  if (url.startsWith("https://chatgpt.com/") && !url.includes("/auth")) {
    return "CHATGPT_PAGE";
  }

  if (title.toLowerCase().includes("chatgpt")) {
    return "CHATGPT_PAGE";
  }

  return "UNKNOWN";
}

async function main() {
  await waitForCdp(10000);
  const pages = await listPages();
  const chatgptPages = pages.filter((page) => (page.url || "").includes("chatgpt.com"));
  const targetMeta = chatgptPages[0] || pages[0];

  if (!targetMeta) {
    console.log("STATUS=NO_PAGE");
    console.log(`CDP=${cdpBaseUrl}`);
    return;
  }

  const target = await inspectLivePage(targetMeta);
  const status = classifyPage(target);
  console.log(`STATUS=${status}`);
  console.log(`TITLE=${target.title || "-"}`);
  console.log(`URL=${target.url || "-"}`);
  console.log(`CDP=${cdpBaseUrl}`);
  process.exit(0);
}

main().catch((error) => {
  console.error(`STATUS=ERROR`);
  console.error(error.message);
  process.exit(1);
});
