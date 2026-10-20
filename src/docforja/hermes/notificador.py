"""Notificador do DocForja para Hermes Agent e canais autorizados (07 §2)."""

from __future__ import annotations

import os
from typing import Protocol

import httpx

from docforja.nucleo.eventos import Evento


class Notificador(Protocol):
    """Protocolo oficial de notificação para eventos do pipeline (07 §2)."""

    def avisar(self, evento: Evento) -> None: ...


class NotificadorNenhum:
    """Implementação no-op que descarta notificações silenciosamente."""

    def avisar(self, evento: Evento) -> None:
        pass


class NotificadorTelegram:
    """Envia notificações estritamente para o TELEGRAM_CHAT_ID autorizado."""

    def __init__(
        self, bot_token: str | None = None, chat_id: str | None = None, timeout: float = 5.0
    ) -> None:
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.timeout = timeout

    def disponivel(self) -> bool:
        return bool(self.bot_token.strip() and self.chat_id.strip())

    def avisar(self, evento: Evento) -> None:
        if not self.disponivel():
            return
        mensagem = self.formatar_mensagem(evento)
        if not mensagem:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": mensagem,
            "parse_mode": "Markdown",
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.post(url, json=payload)
        except Exception:
            # Notificação é de melhor esforço: não interrompe o pipeline
            pass

    def formatar_mensagem(self, evento: Evento) -> str:
        if evento.tipo == "plano_pronto":
            return (
                f"🎬 *Plano Pronto — {evento.projeto}*\n"
                f"A prévia e o plano foram concluídos.\n"
                f"Verifique a lista de busca e aprove com `PRODUZIR` quando desejar."
            )
        if evento.tipo == "producao_concluida":
            return (
                f"✅ *Produção Concluída — {evento.projeto}*\n"
                f"Todos os vídeos, legendas e pacotes foram gerados com sucesso."
            )
        if evento.tipo == "gate_revisao":
            return (
                f"⚠️ *Aguardando Revisão — {evento.projeto}*\n"
                f"A produção aguarda confirmação humana com o código `PRODUZIR`."
            )
        if evento.tipo == "falha":
            etapa = evento.etapa_id or "desconhecida"
            return f"❌ *Falha no DocForja — {evento.projeto}*\nEtapa afetada: `{etapa}`."
        return ""


class NotificadorHermes:
    """Formatador de eventos para consumo pelo Hermes Agent."""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.getenv("HERMES_NOTIFICADOR_URL", "")

    def avisar(self, evento: Evento) -> None:
        if not self.webhook_url:
            return
        payload = {
            "projeto": evento.projeto,
            "tipo": evento.tipo,
            "etapa": evento.etapa_id,
            "timestamp": evento.timestamp,
            "dados": evento.dados,
        }
        try:
            with httpx.Client(timeout=3.0) as client:
                client.post(self.webhook_url, json=payload)
        except Exception:
            pass


def obter_notificador(tipo: str | None = None) -> Notificador:
    """Fábrica para instanciar o notificador configurado."""
    tipo_efetivo = (tipo or os.getenv("DOCFORJA_NOTIFICADOR", "nenhum")).strip().lower()
    if tipo_efetivo == "telegram":
        return NotificadorTelegram()
    if tipo_efetivo == "hermes":
        return NotificadorHermes()
    return NotificadorNenhum()
