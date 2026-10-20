import { existsSync } from "node:fs";
import puppeteer from "puppeteer-core";
import { desktopConfig, startFlow } from "lighthouse";

const url = process.env.DOCFORJA_AUDIT_URL ?? "http://127.0.0.1:7862";
const chromeCandidates = [
  process.env.CHROME_PATH,
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
].filter(Boolean);
const executablePath = chromeCandidates.find((path) => existsSync(path));
if (!executablePath) throw new Error("Chrome ou Edge não encontrado; defina CHROME_PATH.");

const telas = [
  { botao: "Plano", titulo: "amostra-m5" },
  { botao: "Ativos", titulo: "Imagens do plano" },
  { botao: "Lista de busca", titulo: "O que precisa de você" },
];
const larguras = [
  { nome: "desktop", width: 1440, height: 900 },
  { nome: "móvel", width: 390, height: 844 },
];

const browser = await puppeteer.launch({ executablePath, headless: true });
let abaixoDaMeta = false;
try {
  for (const largura of larguras) {
    const page = await browser.newPage();
    await page.setViewport({ width: largura.width, height: largura.height });
    await page.goto(url, { waitUntil: "networkidle2" });
    const flow = await startFlow(page, {
      config: desktopConfig,
      flags: { screenEmulation: { disabled: true } },
    });

    for (const tela of telas) {
      if (largura.width < 768) {
        await page.click('button[aria-label="Abrir menu"]');
        await page.waitForSelector('[role="dialog"][aria-label="Menu de navegação"]');
      }
      await page.evaluate((rotulo) => {
        const botao = [...document.querySelectorAll("button")]
          .find((elemento) => elemento.getClientRects().length > 0 && elemento.textContent?.trim() === rotulo);
        if (!botao) throw new Error(`Botão ${rotulo} não encontrado`);
        botao.click();
      }, tela.botao);
      await page.waitForFunction(
        (titulo) => document.querySelector("main h1")?.textContent?.trim() === titulo,
        { timeout: 10000 },
        tela.titulo,
      );
      const larguraConteudo = await page.evaluate(
        () => Math.round(document.querySelector("main")?.getBoundingClientRect().width ?? 0),
      );
      if (larguraConteudo < Math.min(largura.width, 320)) {
        abaixoDaMeta = true;
        console.log(JSON.stringify({ tela: tela.botao, largura: largura.nome, problema: "conteúdo estreito", larguraConteudo }));
      }
      const transbordamento = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      if (transbordamento) {
        abaixoDaMeta = true;
        console.log(JSON.stringify({ tela: tela.botao, largura: largura.nome, problema: "transbordamento horizontal" }));
      }
      await flow.snapshot({ stepName: `${largura.nome} · ${tela.botao}` });
    }

    const resultado = await flow.createFlowResult();
    for (const [indice, passo] of resultado.steps.entries()) {
      const lhr = passo.lhr;
      const categoria = lhr.categories.accessibility;
      const pontuacao = Math.round((categoria.score ?? 0) * 100);
      const falhas = categoria.auditRefs
        .map(({ id }) => lhr.audits[id])
        .filter((auditoria) => auditoria?.score !== null && auditoria?.score < 1)
        .map((auditoria) => ({
          id: auditoria.id,
          titulo: auditoria.title,
          alvos: auditoria.details?.items?.slice(0, 3).map((item) => item.node?.selector).filter(Boolean),
        }));
      console.log(JSON.stringify({ tela: telas[indice].botao, largura: largura.nome, pontuacao, falhas }));
      if (pontuacao < 90) abaixoDaMeta = true;
    }
    await page.close();
  }
} finally {
  await browser.close();
}
if (abaixoDaMeta) process.exitCode = 1;
