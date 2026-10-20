from docforja.audio.adaptadores.base import AdaptadorTTS
from docforja.audio.adaptadores.chatterbox import AdaptadorChatterbox
from docforja.audio.adaptadores.kokoro import AdaptadorKokoro
from docforja.audio.adaptadores.openai_compat import AdaptadorOpenAITTS
from docforja.audio.adaptadores.pronta import (
    AdaptadorNarracaoPronta,
    processar_narracao_pronta_completa,
)
from docforja.audio.adaptadores.voicestudio import AdaptadorVoiceStudio

__all__ = [
    "AdaptadorChatterbox",
    "AdaptadorKokoro",
    "AdaptadorNarracaoPronta",
    "AdaptadorOpenAITTS",
    "AdaptadorTTS",
    "AdaptadorVoiceStudio",
    "processar_narracao_pronta_completa",
]
