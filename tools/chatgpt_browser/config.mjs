import path from "node:path";
import { fileURLToPath } from "node:url";

const thisFile = fileURLToPath(import.meta.url);
const thisDir = path.dirname(thisFile);
export const repoRoot = path.resolve(thisDir, "../..");

export const stateDir = path.join(repoRoot, ".local", "chatgpt-browser");
export const profileDir =
  process.env.CHATGPT_PROFILE_DIR ||
  path.join(repoRoot, ".local", "chatgpt-browser-profile");

export const cdpPort = Number.parseInt(process.env.CHATGPT_CDP_PORT || "9333", 10);
export const cdpBaseUrl = `http://127.0.0.1:${cdpPort}`;
export const loginUrl = process.env.CHATGPT_URL || "https://chatgpt.com/auth/login";
export const sessionNamePrefix =
  process.env.CHATGPT_SESSION_NAME_PREFIX || "codex-loop-chatgpt-session-";

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${url}`);
  }
  return response.json();
}

export async function waitForCdp(timeoutMs = 30000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;

  while (Date.now() < deadline) {
    try {
      return await fetchJson(`${cdpBaseUrl}/json/version`);
    } catch (error) {
      lastError = error;
      await sleep(500);
    }
  }

  throw new Error(`CDP接続に失敗しました: ${lastError?.message || "timeout"}`);
}

export async function listPages() {
  return fetchJson(`${cdpBaseUrl}/json/list`);
}
