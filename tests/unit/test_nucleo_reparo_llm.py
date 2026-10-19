import pytest
from pydantic import BaseModel

from docforja.llm.reparo import extrair_bloco_json, sanitizar_json_leniente, validar_ou_reparar


class ExemploSchema(BaseModel):
    titulo: str
    shots: int
    aprovado: bool


def test_extrair_bloco_json():
    # Markdown
    com_md = 'Aqui está a resposta:\n```json\n{"chave": 123}\n```\nObrigado!'
    assert extrair_bloco_json(com_md) == '{"chave": 123}'

    # Objeto bruto no meio do texto
    texto_livre = 'Com certeza! Segue o resultado: {"chave": 456} pronto.'
    assert extrair_bloco_json(texto_livre) == '{"chave": 456}'


def test_sanitizar_json_leniente():
    json_malformado = '{"titulo": "Vesúvio", "shots": 10, "itens": [1, 2, ], }'
    sanitizado = sanitizar_json_leniente(json_malformado)
    assert ", }" not in sanitizado
    assert ", ]" not in sanitizado


def test_validar_ou_reparar_direto():
    json_valido = '{"titulo": "Pompeia", "shots": 5, "aprovado": true}'
    obj = validar_ou_reparar(json_valido, ExemploSchema)
    assert obj.titulo == "Pompeia"
    assert obj.shots == 5
    assert obj.aprovado is True


def test_validar_ou_reparar_com_llm_callback():
    # JSON severamente quebrado
    json_quebrado = "titulo: Pompeia shots: 5 aprovado: yes"

    def mock_reparo(prompt: str, schema_name: str) -> str:
        return '{"titulo": "Pompeia Corrigida", "shots": 5, "aprovado": true}'

    obj = validar_ou_reparar(json_quebrado, ExemploSchema, funcao_reparo_llm=mock_reparo)
    assert obj.titulo == "Pompeia Corrigida"
    assert obj.shots == 5

    with pytest.raises(ValueError, match="Não foi possível validar"):
        validar_ou_reparar(json_quebrado, ExemploSchema, funcao_reparo_llm=None)
