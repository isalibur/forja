"""Testes unitários das ferramentas, limites de segurança e notificações do Hermes Agent."""

from __future__ import annotations

import pytest

from docforja.hermes import (
    NotificadorHermes,
    NotificadorNenhum,
    NotificadorTelegram,
    docforja_imagens_nao_atribuidas,
    docforja_novo,
    docforja_produzir,
    docforja_resumo_plano,
    docforja_status,
    docforja_status_producao,
    obter_notificador,
    obter_projeto_seguro,
    validar_chat_telegram,
    validar_slug,
)
from docforja.io import atomic_write_text
from docforja.nucleo.eventos import Evento


def test_validar_slug_seguranca():
    assert validar_slug("meu-documentario") == "meu-documentario"
    assert validar_slug("Doc_79") == "doc_79"

    # Tentativas de travessia de diretório
    with pytest.raises(ValueError, match="Slug inválido"):
        validar_slug("../projeto")
    with pytest.raises(ValueError, match="Slug inválido"):
        validar_slug("pasta/subpasta")
    with pytest.raises(ValueError, match="Slug inválido"):
        validar_slug("c:\\projetos")
    with pytest.raises(ValueError, match="Slug inválido"):
        validar_slug("projeto com espaco")


def test_obter_projeto_seguro_bloqueia_fora_da_raiz(tmp_path):
    with pytest.raises(FileNotFoundError):
        obter_projeto_seguro("inexistente", raiz_projetos=tmp_path)


def test_docforja_novo_e_status(tmp_path):
    res_novo = docforja_novo(
        nome="Projeto Hermes",
        tipo="longo",
        roteiro="## B0\n**B0-S01**\nTexto.",
        idioma_principal="pt-BR",
        idiomas_extras=["en"],
        raiz_projetos=tmp_path,
    )
    assert res_novo["status"] == "criado"
    slug = res_novo["slug"]

    status = docforja_status(slug, raiz_projetos=tmp_path)
    assert status["slug"] == slug
    assert "gpu" in status
    assert "cotas" in status
    assert isinstance(status["etapas"], list)


def test_resumo_plano_e_imagens_nao_atribuidas(tmp_path):
    res_novo = docforja_novo(nome="Resumo Teste", raiz_projetos=tmp_path)
    slug = res_novo["slug"]
    projeto = obter_projeto_seguro(slug, raiz_projetos=tmp_path)

    # Cria lista de busca e estimativa
    atomic_write_text(
        projeto.pastas.plano / "lista_de_busca.md",
        "# Lista de busca\n"
        "- [ ] Imagem do fórum romano\n"
        "- [x] Mapa do golfo\n"
        "- [ ] Templo de Júpiter\n",
    )
    atomic_write_text(projeto.pastas.plano / "estimativa.md", "Tempo estimado: 45 min\n")

    res_plano = docforja_resumo_plano(slug, raiz_projetos=tmp_path)
    assert res_plano["total_buscas"] == 3
    assert len(res_plano["buscas_pendentes"]) == 2
    assert res_plano["estimativa_minutos"] == 45

    # Cria imagens não atribuídas na pasta manual
    pasta_nao_atribuidas = projeto.pastas.midias / "manual" / "nao_atribuidas"
    pasta_nao_atribuidas.mkdir(parents=True, exist_ok=True)
    (pasta_nao_atribuidas / "desconhecida1.jpg").write_bytes(b"jpg1")
    (pasta_nao_atribuidas / "desconhecida2.png").write_bytes(b"png2")

    res_imgs = docforja_imagens_nao_atribuidas(slug, raiz_projetos=tmp_path)
    assert res_imgs["quantidade"] == 2
    assert "desconhecida1.jpg" in res_imgs["arquivos"]
    assert "desconhecida2.png" in res_imgs["arquivos"]


def test_docforja_produzir_exige_codigo_inviolavel(tmp_path, monkeypatch):
    res_novo = docforja_novo(nome="Produzir Teste", raiz_projetos=tmp_path)
    slug = res_novo["slug"]

    # Tentativas sem o código PRODUZIR devem falhar imediatamente
    with pytest.raises(ValueError, match="Código de confirmação inválido"):
        docforja_produzir(slug, codigo_confirmacao="", raiz_projetos=tmp_path)

    with pytest.raises(ValueError, match="Código de confirmação inválido"):
        docforja_produzir(slug, codigo_confirmacao="pode_produzir", raiz_projetos=tmp_path)

    with pytest.raises(ValueError, match="Código de confirmação inválido"):
        docforja_produzir(slug, codigo_confirmacao="SIM", raiz_projetos=tmp_path)

    # Com o código 'PRODUZIR', o portão REVISAO é aprovado
    gate_aprovado = []

    class MockExecutor:
        def aprovar_gate(self, gate: str):
            gate_aprovado.append(gate)

        async def executar(self):
            return {"R1_imagens": "concluida", "R9_pacote": "concluida"}

    monkeypatch.setattr(
        "docforja.hermes.ferramentas.criar_executor_projeto",
        lambda proj: MockExecutor(),
    )

    res_prod = docforja_produzir(slug, codigo_confirmacao="PRODUZIR", raiz_projetos=tmp_path)
    assert res_prod["sucesso"] is True
    assert gate_aprovado == ["REVISAO"]


def test_docforja_status_producao(tmp_path):
    res_novo = docforja_novo(nome="Status Producao", raiz_projetos=tmp_path)
    slug = res_novo["slug"]

    res_st = docforja_status_producao(slug, raiz_projetos=tmp_path)
    assert res_st["slug"] == slug
    assert res_st["concluido"] is False
    assert res_st["progresso_percentual"] == 0.0


def test_validar_chat_telegram():
    assert validar_chat_telegram("123456", chat_autorizado="123456") is True
    assert validar_chat_telegram(123456, chat_autorizado="123456") is True
    assert validar_chat_telegram("999999", chat_autorizado="123456") is False
    assert validar_chat_telegram("123456", chat_autorizado="") is False


def test_notificadores_hermes_e_telegram(monkeypatch):
    # Notificador Nenhum
    nenhum = obter_notificador("nenhum")
    assert isinstance(nenhum, NotificadorNenhum)
    nenhum.avisar(Evento(projeto="teste", tipo="plano_pronto"))

    # Notificador Telegram formatação e disponibilidade
    tel_sem_token = NotificadorTelegram(bot_token="", chat_id="123")
    assert tel_sem_token.disponivel() is False

    tel = NotificadorTelegram(bot_token="token_fake", chat_id="123")
    assert tel.disponivel() is True
    msg_plano = tel.formatar_mensagem(Evento(projeto="vesuvio", tipo="plano_pronto"))
    assert "Plano Pronto" in msg_plano and "PRODUZIR" in msg_plano

    msg_prod = tel.formatar_mensagem(Evento(projeto="vesuvio", tipo="producao_concluida"))
    assert "Produção Concluída" in msg_prod

    msg_falha = tel.formatar_mensagem(Evento(projeto="vesuvio", tipo="falha", etapa_id="R7_render"))
    assert "R7_render" in msg_falha

    # Notificador Hermes
    chamadas_http = []

    def mock_post(self, url, json, **kwargs):
        chamadas_http.append((url, json))

    monkeypatch.setattr("httpx.Client.post", mock_post)
    hermes_notif = NotificadorHermes(webhook_url="http://127.0.0.1:20128/webhook")
    hermes_notif.avisar(Evento(projeto="vesuvio", tipo="plano_pronto", dados={"duracao": 845}))
    assert len(chamadas_http) == 1
    assert chamadas_http[0][1]["projeto"] == "vesuvio"
    assert chamadas_http[0][1]["tipo"] == "plano_pronto"
