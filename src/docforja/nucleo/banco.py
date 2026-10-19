"""Persistência de estado de etapas e pipeline em SQLite."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class BancoProjeto:
    """Gerenciador do banco SQLite em <projeto>/sistema/banco.db."""

    def __init__(self, caminho_banco: Path) -> None:
        self.caminho = caminho_banco
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.inicializar()

    @contextmanager
    def _conexao(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.caminho), timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def inicializar(self) -> None:
        """Cria tabelas se não existirem."""
        with self._conexao() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS etapas (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    hash_entrada TEXT DEFAULT '',
                    duracao_s REAL DEFAULT 0.0,
                    erro TEXT,
                    saida_resumo TEXT,
                    started_at TEXT,
                    completed_at TEXT
                );

                CREATE TABLE IF NOT EXISTS subetapas (
                    id TEXT PRIMARY KEY,
                    etapa_pai TEXT NOT NULL,
                    alvo TEXT NOT NULL,
                    status TEXT NOT NULL,
                    hash_entrada TEXT DEFAULT '',
                    duracao_s REAL DEFAULT 0.0,
                    erro TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    FOREIGN KEY(etapa_pai) REFERENCES etapas(id)
                );

                CREATE TABLE IF NOT EXISTS meta (
                    chave TEXT PRIMARY KEY,
                    valor TEXT
                );
                """
            )

    def obter_etapa(self, etapa_id: str) -> dict[str, Any] | None:
        with self._conexao() as conn:
            cur = conn.execute("SELECT * FROM etapas WHERE id = ?", (etapa_id,))
            row = cur.fetchone()
            return dict(row) if row else None

    def listar_etapas(self) -> list[dict[str, Any]]:
        with self._conexao() as conn:
            cur = conn.execute("SELECT * FROM etapas ORDER BY rowid ASC")
            return [dict(r) for r in cur.fetchall()]

    def salvar_etapa(
        self,
        etapa_id: str,
        status: str,
        hash_entrada: str = "",
        duracao_s: float = 0.0,
        erro: str | None = None,
        saida_resumo: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._conexao() as conn:
            row = conn.execute("SELECT started_at FROM etapas WHERE id = ?", (etapa_id,)).fetchone()
            started_at = (
                row["started_at"]
                if row and row["started_at"]
                else (now if status == "executando" else None)
            )
            completed_at = now if status in ("concluida", "falhou", "cancelada") else None

            conn.execute(
                """
                INSERT INTO etapas (
                    id, status, hash_entrada, duracao_s, erro,
                    saida_resumo, started_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    hash_entrada=CASE
                        WHEN excluded.hash_entrada != '' THEN excluded.hash_entrada
                        ELSE etapas.hash_entrada
                    END,
                    duracao_s=excluded.duracao_s,
                    erro=excluded.erro,
                    saida_resumo=COALESCE(excluded.saida_resumo, etapas.saida_resumo),
                    started_at=COALESCE(etapas.started_at, excluded.started_at),
                    completed_at=excluded.completed_at
                """,
                (
                    etapa_id,
                    status,
                    hash_entrada,
                    duracao_s,
                    erro,
                    saida_resumo,
                    started_at,
                    completed_at,
                ),
            )

    def salvar_subetapa(
        self,
        subetapa_id: str,
        etapa_pai: str,
        alvo: str,
        status: str,
        hash_entrada: str = "",
        duracao_s: float = 0.0,
        erro: str | None = None,
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._conexao() as conn:
            row = conn.execute(
                "SELECT started_at FROM subetapas WHERE id = ?", (subetapa_id,)
            ).fetchone()
            started_at = (
                row["started_at"]
                if row and row["started_at"]
                else (now if status == "executando" else None)
            )
            completed_at = now if status in ("concluida", "falhou", "cancelada") else None

            conn.execute(
                """
                INSERT INTO subetapas (
                    id, etapa_pai, alvo, status, hash_entrada,
                    duracao_s, erro, started_at, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    hash_entrada=CASE
                        WHEN excluded.hash_entrada != '' THEN excluded.hash_entrada
                        ELSE subetapas.hash_entrada
                    END,
                    duracao_s=excluded.duracao_s,
                    erro=excluded.erro,
                    started_at=COALESCE(subetapas.started_at, excluded.started_at),
                    completed_at=excluded.completed_at
                """,
                (
                    subetapa_id,
                    etapa_pai,
                    alvo,
                    status,
                    hash_entrada,
                    duracao_s,
                    erro,
                    started_at,
                    completed_at,
                ),
            )

    def listar_subetapas(self, etapa_pai: str | None = None) -> list[dict[str, Any]]:
        with self._conexao() as conn:
            if etapa_pai:
                cur = conn.execute(
                    "SELECT * FROM subetapas WHERE etapa_pai = ? ORDER BY rowid ASC",
                    (etapa_pai,),
                )
            else:
                cur = conn.execute("SELECT * FROM subetapas ORDER BY rowid ASC")
            return [dict(r) for r in cur.fetchall()]

    def invalidar_etapas(self, etapas_ids: list[str]) -> None:
        """Marca etapas e suas subetapas como pendentes e zera hash para forçar reexecução."""
        if not etapas_ids:
            return
        placeholders = ",".join("?" for _ in etapas_ids)
        with self._conexao() as conn:
            conn.execute(
                f"UPDATE etapas SET status = 'pendente', hash_entrada = '', erro = NULL "
                f"WHERE id IN ({placeholders})",
                etapas_ids,
            )
            conn.execute(
                f"UPDATE subetapas SET status = 'pendente', hash_entrada = '', erro = NULL "
                f"WHERE etapa_pai IN ({placeholders})",
                etapas_ids,
            )

    def obter_meta(self, chave: str) -> str | None:
        with self._conexao() as conn:
            row = conn.execute("SELECT valor FROM meta WHERE chave = ?", (chave,)).fetchone()
            return row["valor"] if row else None

    def definir_meta(self, chave: str, valor: str) -> None:
        with self._conexao() as conn:
            conn.execute(
                """
                INSERT INTO meta (chave, valor) VALUES (?, ?)
                ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor
                """,
                (chave, valor),
            )
