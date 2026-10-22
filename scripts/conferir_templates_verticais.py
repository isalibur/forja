"""Confere que todo template T tem variante vertical 9:16 no catalogo do Remotion."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
KIT = RAIZ / "kits" / "cinza-e-brasa"

npm = shutil.which("npm") or shutil.which("npm.cmd") or "npm"
saida = subprocess.run(
    [npm, "exec", "--offline", "--", "remotion", "compositions", "src/index.ts"],
    cwd=KIT,
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
    check=False,
)
texto = saida.stdout
nomes = re.findall(r"^(T\d\d-\S+)\s+\d+\s+(\d+x\d+)", texto, re.MULTILINE)
horizontais = {nome for nome, tam in nomes if tam == "1920x1080"}
verticais = {nome for nome, tam in nomes if tam == "1080x1920"}
faltando = sorted(nome for nome in horizontais if f"{nome}-V" not in verticais)
print(f"templates 16:9: {len(horizontais)} | variantes 9:16: {len(verticais)}")
print(f"sem variante vertical: {faltando}")
raise SystemExit(0 if horizontais and not faltando else 1)
