from docforja.nucleo.banco import BancoProjeto
from docforja.nucleo.projeto import Projeto, slugificar


def test_slugificar():
    assert slugificar("O Mistério do Vesúvio 79 d.C.!") == "o-misterio-do-vesuvio-79-dc"
    assert slugificar("Pompeii: The Lost City") == "pompeii-the-lost-city"


def test_criacao_projeto_e_arvore_pastas(tmp_path):
    projeto = Projeto.criar(
        nome="Vesúvio 79",
        roteiro="# Roteiro\nEra uma vez...",
        idioma_principal="pt-BR",
        idiomas_extras=["en", "es"],
        raiz_projetos=tmp_path,
    )
    assert projeto.slug == "vesuvio-79"
    assert projeto.raiz.is_dir()
    assert (projeto.pastas.entrada / "roteiro.md").is_file()
    assert (projeto.pastas.entrada / "opcoes.yaml").is_file()
    assert (projeto.pastas.entrada / "glossario.yaml").is_file()

    # Confere subpastas principais (07 §4)
    assert (projeto.pastas.midias / "manual").is_dir()
    assert (projeto.pastas.midias / "biblioteca").is_dir()
    assert (projeto.pastas.midias / "geradas").is_dir()
    assert (projeto.pastas.audio / "pt-BR").is_dir()
    assert (projeto.pastas.audio / "en").is_dir()
    assert (projeto.pastas.audio / "es").is_dir()
    assert (projeto.pastas.montagem / "pt-BR" / "blocos").is_dir()
    assert (projeto.pastas.saida / "pt-BR").is_dir()
    assert (projeto.pastas.sistema / "logs").is_dir()
    assert (projeto.pastas.sistema / "cache").is_dir()

    # Recarrega projeto existente
    carregado = Projeto.carregar(projeto.raiz)
    assert carregado.slug == "vesuvio-79"
    assert "Era uma vez" in carregado.obter_roteiro()


def test_banco_projeto_crud_e_invalidacao(tmp_path):
    banco = BancoProjeto(tmp_path / "banco.db")
    banco.salvar_etapa("P1_leitura", status="concluida", hash_entrada="hash1", duracao_s=2.5)
    banco.salvar_etapa("P2_narracao", status="executando", hash_entrada="hash2")

    etapa1 = banco.obter_etapa("P1_leitura")
    assert etapa1 is not None
    assert etapa1["status"] == "concluida"
    assert etapa1["hash_entrada"] == "hash1"
    assert etapa1["duracao_s"] == 2.5

    banco.salvar_subetapa(
        subetapa_id="P4_shots_B1",
        etapa_pai="P4_shots",
        alvo="B1",
        status="concluida",
        duracao_s=1.2,
    )
    subetapas = banco.listar_subetapas("P4_shots")
    assert len(subetapas) == 1
    assert subetapas[0]["alvo"] == "B1"

    # Invalidação
    banco.invalidar_etapas(["P1_leitura"])
    etapa1_inv = banco.obter_etapa("P1_leitura")
    assert etapa1_inv["status"] == "pendente"
    assert etapa1_inv["hash_entrada"] == ""

    # Metadados
    banco.definir_meta("revisao_aprovada", "sim")
    assert banco.obter_meta("revisao_aprovada") == "sim"
