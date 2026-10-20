import assert from "node:assert/strict";
import { existsSync, mkdirSync } from "node:fs";
import puppeteer from "puppeteer-core";

const url = process.env.DOCFORJA_AUDIT_URL ?? "http://127.0.0.1:7862";
const executablePath = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
].find((path) => path && existsSync(path));
if (!executablePath) throw new Error("Chrome ou Edge não encontrado; defina CHROME_PATH.");

const browser = await puppeteer.launch({ executablePath, headless: true });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.goto(url, { waitUntil: "networkidle2" });
  const navegar = async (nome, titulo) => {
    await page.evaluate((rotulo) => {
      const botao = [...document.querySelectorAll("button")]
        .find((item) => item.getClientRects().length && item.textContent?.trim() === rotulo);
      if (!botao) throw new Error(`Navegação ${rotulo} indisponível`);
      botao.click();
    }, nome);
    await page.waitForFunction(
      (esperado) => document.querySelector("main h1")?.textContent?.trim() === esperado,
      { timeout: 10000 },
      titulo,
    );
  };
  const plano = async () => page.evaluate(async () => {
    const resposta = await fetch("/api/projetos/amostra-m5/plano");
    if (!resposta.ok) throw new Error("Plano da amostra indisponível");
    return resposta.json();
  });

  await navegar("Ativos", "Imagens do plano");
  const original = await plano();
  assert.equal(original.ativos["A-001"].candidata_selecionada, null);
  const artigo = await page.$("article");
  assert.ok(artigo);
  await artigo.evaluate((item) => [...item.querySelectorAll("button")]
    .find((botao) => botao.textContent?.includes("Ver alternativas"))?.click());
  await page.waitForFunction(() => document.querySelector("article")?.textContent?.includes("cand_amostra_1.png"));
  const saida = process.env.DOCFORJA_SMOKE_SHOTS_DIR ?? "../.pytest_tmp";
  mkdirSync(saida, { recursive: true });
  if (saida) await artigo.screenshot({ path: `${saida}/m5-original.png` });
  await artigo.evaluate((item) => [...item.querySelectorAll("button")]
    .find((botao) => botao.textContent?.includes("Usar nesta prévia"))?.click());
  await page.waitForFunction(() => document.querySelector('[role="status"]')?.textContent?.includes("escolhida"));
  const escolhida = await plano();
  assert.equal(escolhida.ativos["A-001"].candidata_selecionada, "cand_amostra_1.png");
  assert.ok(escolhida.imagens_por_shot["B0-01"].includes("revisao="));
  assert.equal(escolhida.previa_mp4_desatualizada, true);
  if (saida) await artigo.screenshot({ path: `${saida}/m5-escolhida.png` });
  await navegar("Plano", "amostra-m5");
  await page.waitForFunction(() => document.querySelector("main")?.textContent?.includes("O MP4 existente não incorpora essas trocas"));
  if (saida) await page.screenshot({ path: `${saida}/m5-player-escolhida.png` });
  await navegar("Ativos", "Imagens do plano");
  await page.evaluate(() => [...document.querySelectorAll("button")]
    .find((botao) => botao.textContent?.includes("Restaurar escolha original"))?.click());
  await page.waitForFunction(() => document.querySelector('[role="status"]')?.textContent?.includes("restaurada"));
  const restaurada = await plano();
  assert.equal(restaurada.ativos["A-001"].candidata_selecionada, null);
  assert.equal(restaurada.previa_mp4_desatualizada, false);
  assert.notEqual(restaurada.ativos["A-001"].imagem_url, escolhida.ativos["A-001"].imagem_url);
  console.log("Troca, player e restauração da candidata M5: OK");
} finally {
  await browser.close();
}
