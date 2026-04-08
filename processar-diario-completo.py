#!/usr/bin/env python3
"""
Processador de Diários Oficiais — DPE/AM 2026
Polo Médio Amazonas

Baixa os PDFs do Diário Oficial, extrai o texto completo e usa
o Claude Sonnet para identificar portarias relevantes.

Uso:
    python processar-diario-completo.py --api-key sk-ant-...
    python processar-diario-completo.py  (usa variável ANTHROPIC_API_KEY)
    python processar-diario-completo.py --edicao 2564  (só uma edição, para teste)
    python processar-diario-completo.py --forcar       (reprocessa tudo)
"""

import json
import os
import sys
import time
import argparse
import urllib.request
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Erro: PyMuPDF não instalado. Execute:")
    print('  "C:/Users/lucia/AppData/Local/Python/bin/python.exe" -m pip install pymupdf')
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("Erro: anthropic não instalado. Execute:")
    print('  "C:/Users/lucia/AppData/Local/Python/bin/python.exe" -m pip install anthropic')
    sys.exit(1)

# ── Caminhos ───────────────────────────────────────────────────────────────────

BASE_DIR     = Path(__file__).parent
JSON_ENTRADA = BASE_DIR / "docs" / "diario-oficial-polo-medio-2026.json"
JSON_SAIDA   = BASE_DIR / "docs" / "diario-oficial-completo-2026.json"
CACHE_DIR    = BASE_DIR / "docs" / "pdfs-cache"

# ── Modelo ─────────────────────────────────────────────────────────────────────
MODEL = "claude-sonnet-4-6"

CONFIG_FILE = BASE_DIR / "docs" / "config.json"

# ── Carrega defensores titulares do config.json ────────────────────────────────

def carregar_defensores() -> list:
    """Lê a lista de defensores titulares atuais do Polo Médio em config.json."""
    if not CONFIG_FILE.exists():
        print("⚠  config.json não encontrado — usando lista vazia de defensores.")
        return []
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = json.load(f)
    defensores = cfg.get("defensores_polo_medio", [])
    if not defensores:
        print("⚠  Nenhum defensor encontrado em config.json > defensores_polo_medio.")
    return defensores


def construir_keywords(defensores: list) -> list:
    """Monta a lista de palavras-chave para pré-filtro a partir dos defensores atuais."""
    keywords = [
        # Polo
        "Polo Médio Amazonas", "Polo do Médio Amazonas", "Polo Medio Amazonas",
        # Servidores (fixos — não mudam com a titularidade das DPs)
        "Natalia Cristina de Moraes", "NATALIA CRISTINA",
        "Arnoud Lucas", "ARNOUD LUCAS",
        "Luma Karolyne", "LUMA KAROLYNE",
        "Fabio Bastos de Souza", "FABIO BASTOS",
        "Larice Bruce", "LARICE BRUCE",
        # Comarcas do Polo Médio Amazonas
        "Itacoatiara", "Itapiranga",
        "São Sebastião do Uatumã", "Sao Sebastiao do Uatuma",
        "Silves", "Urucará", "Urucara", "Urucurituba",
        # Projetos institucionais do polo
        "Projeto Adote", "Adote", "Projeto Expandir Direitos", "Projeto Expandir",
        "Expandir Direitos",
        # Nomeações para diretoria (termos gerais — Claude filtra o que é relevante)
        "nomeado para", "nomeação para", "nomeação ao cargo",
        "Diretor de", "Diretora de", "Diretor Geral", "Diretora Geral",
        "Diretor Administrativo", "Diretor Financeiro", "Diretor Jurídico",
        "Coordenador Geral", "Coordenadora Geral",
        "Subdefensor Público Geral", "Subdefensora Pública Geral",
        "cargo de direção", "cargo de chefia", "função de direção",
        "Defensoria Pública Geral", "GDPG", "GSPG",
    ]
    # Adiciona os nomes de busca de cada defensor titular atual
    for d in defensores:
        for nome in d.get("nome_busca", []):
            if nome not in keywords:
                keywords.append(nome)
    return keywords


def construir_sistema_prompt(defensores: list) -> str:
    """Gera o SISTEMA_PROMPT com a lista atualizada de defensores titulares."""
    lista_defensores = "\n".join(
        f"   • {d['nome_completo']} (titular: {', '.join(d['dps'])})"
        for d in defensores
    )
    return f"""Você analisa textos do Diário Oficial Eletrônico da Defensoria Pública do Amazonas (DPE/AM).

O texto foi extraído de um PDF diagramado em DUAS COLUNAS. A extração pode intercalar linhas
da coluna esquerda com linhas da coluna direita. Seu trabalho é identificar atos relevantes
mesmo com esse embaralhamento, e reconstituir os trechos de forma legível.

IGNORE: cabeçalhos de página (ex: "SEGUNDA-FEIRA, 2 DE JANEIRO DE 2026 Ano 12, Edição 2564 Pág. X de Y"),
rodapés, assinaturas digitais longas e metadados de certificação digital.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITÉRIOS DE RELEVÂNCIA — um ato é relevante se contiver qualquer um dos itens abaixo:

1. POLO MÉDIO — menção a "Polo Médio Amazonas" ou "Polo do Médio Amazonas"

2. DEFENSORES TITULARES DO POLO (lista atual — pode mudar por remoção ou transferência):
{lista_defensores}
   ATENÇÃO: estes são os titulares NO MOMENTO da análise. Se o ato mencionar o nome
   de qualquer um deles, ele é relevante independentemente do assunto (afastamento,
   substituição, remoção, exoneração, nomeação, licença, estudo, cedência etc.).

3. SERVIDORES DO POLO:
   • Natalia Cristina de Moraes
   • Arnoud Lucas Andrade da Silva
   • Luma Karolyne Pantoja Bandeira
   • Fabio Bastos de Souza
   • Larice Bruce Pereira

4. NOMEAÇÃO PARA DIRETORIA DPE/AM — qualquer defensor (de qualquer polo ou da capital)
   nomeado, designado ou reconduzido para cargo de direção, diretoria, subdireção,
   coordenação geral ou chefia no âmbito da DPE/AM
   (ex: Diretor de Administração, Diretor Financeiro, Subdefensor Público Geral,
   Coordenador do Polo, Diretor da ESUDPAM, etc.)
   ATENÇÃO: inclua mesmo que o defensor não seja do Polo Médio — nomeações de diretoria
   interessam independentemente do polo de origem do defensor.

5. COMARCAS DO POLO MÉDIO — qualquer ato que mencione as cidades:
   Itacoatiara, Itapiranga, São Sebastião do Uatumã, Silves, Urucará ou Urucurituba
   em contexto institucional da DPE/AM (designações, projetos, escalas, audiências etc.)
   ATENÇÃO: ignore menções puramente geográficas sem relação com a Defensoria.

6. PROJETOS INSTITUCIONAIS — atos que mencionem:
   • "Projeto Adote" ou "Adote" — projeto de audiências judiciais e fila do Projudi
   • "Projeto Expandir Direitos" ou "Projeto Expandir" — idem
   Relevante APENAS quando relacionado às comarcas do polo (Itacoatiara, Itapiranga,
   São Sebastião do Uatumã, Silves, Urucará ou Urucurituba) ou ao Polo Médio Amazonas.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATEGORIAS disponíveis (use uma ou mais por ato):
  "polo_medio"          — menção direta ao Polo Médio Amazonas
  "defensor"            — nome de defensor titular do polo
  "servidor"            — nome de servidor do polo
  "substituicao"        — remoção/substituição de defensor titular
  "nomeacao_diretoria"  — nomeação para cargo de direção da DPE/AM
  "comarca"             — menção a comarca do polo (Itacoatiara, Itapiranga etc.)
  "projeto"             — Projeto Adote ou Projeto Expandir Direitos

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORMATO DE SAÍDA — JSON válido, sem texto antes ou depois:

{{
  "atos": [
    {{
      "numero": "Portaria nº 10/2026-GSPG/DPE/AM",
      "sei": "26.0.000000069-7",
      "sgi": "2500846",
      "categorias": ["polo_medio", "defensor"],
      "trechos": [
        "II - DESIGNAR, cumulativamente, o Defensor Público de 3ª Classe Eliaquim Antunes de Souza Santos para atuar na 9ª Defensoria Pública do Polo Médio Amazonas, a contar do dia 11 de janeiro de 2026;"
      ],
      "resumo": "Designa Eliaquim para 9ª DP Polo Médio Amazonas a partir de 11/01/2026"
    }}
  ]
}}

Regras:
- "sei" e "sgi": null se não mencionados no ato
- "trechos": inclua o inciso ou alínea COMPLETO, reconstituído de forma legível (sem mistura de colunas)
- "resumo": frase curta e objetiva (máximo 120 caracteres)
- Se nenhum ato relevante: {{"atos": []}}"""


# ── Funções auxiliares ─────────────────────────────────────────────────────────

def baixar_pdf(url: str, caminho: Path) -> bool:
    """Baixa um PDF para disco. Retorna True se bem-sucedido."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; DPE-AM-Script/1.0)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            caminho.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"    ⚠  Erro ao baixar: {e}")
        return False


def extrair_texto_pdf(caminho: Path) -> str:
    """Extrai texto completo do PDF, página por página."""
    try:
        doc = fitz.open(str(caminho))
        partes = []
        for num_pag, pagina in enumerate(doc, start=1):
            texto = pagina.get_text("text")
            if texto.strip():
                partes.append(f"[Página {num_pag}]\n{texto}")
        doc.close()
        return "\n\n".join(partes)
    except Exception as e:
        return f"[Erro na extração: {e}]"


def tem_palavra_chave(texto: str) -> bool:
    """Verifica se o texto contém ao menos uma palavra-chave relevante."""
    texto_lower = texto.lower()
    for kw in keywords:
        if kw.lower() in texto_lower:
            return True
    return False


def analisar_com_claude(client: anthropic.Anthropic, texto: str, edicao: int, data: str,
                        sistema_prompt: str, tentativa: int = 1) -> list:
    """Envia o texto ao Claude e retorna lista de atos relevantes.
    Usa chamada direta (sem streaming) para maior estabilidade em redes lentas.
    Tenta até 3 vezes em caso de erro de conexão.
    """
    MAX_TENTATIVAS = 3

    texto_enviar = texto[:120000]
    if len(texto) > 120000:
        texto_enviar += "\n\n[... texto truncado — arquivo muito longo ...]"

    mensagem_usuario = (
        f"Analise o Diário Oficial da DPE/AM — Edição {edicao} ({data}).\n\n"
        f"Texto extraído do PDF:\n"
        f"{'─' * 60}\n"
        f"{texto_enviar}\n"
        f"{'─' * 60}\n\n"
        f"Identifique todos os atos relevantes conforme as instruções."
    )

    try:
        # Chamada direta sem streaming — mais estável para processamento em lote
        resposta = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=sistema_prompt,
            messages=[{"role": "user", "content": mensagem_usuario}],
            timeout=120.0,  # 2 minutos de timeout
        )

        uso = resposta.usage
        tokens_in  = uso.input_tokens  if uso else 0
        tokens_out = uso.output_tokens if uso else 0
        print(f"    💰 Tokens: {tokens_in:,} entrada / {tokens_out:,} saída")

        texto_resposta = next(
            (b.text for b in resposta.content if b.type == "text"), ""
        ).strip()

        if not texto_resposta:
            print(f"    ⚠  Resposta vazia do Claude")
            return []

        # Remover bloco de código markdown se presente
        if texto_resposta.startswith("```"):
            linhas = texto_resposta.splitlines()
            texto_resposta = "\n".join(linhas[1:-1]).strip()

        dados = json.loads(texto_resposta)
        return dados.get("atos", [])

    except json.JSONDecodeError as e:
        print(f"    ⚠  JSON inválido na resposta: {e}")
        return []

    except anthropic.RateLimitError:
        print("    ⚠  Rate limit — aguardando 60 segundos...")
        time.sleep(60)
        return analisar_com_claude(client, texto, edicao, data, sistema_prompt, tentativa)

    except (anthropic.APIConnectionError, anthropic.APITimeoutError) as e:
        if tentativa < MAX_TENTATIVAS:
            espera = tentativa * 15  # 15s, 30s
            print(f"    ⚠  Erro de conexão (tentativa {tentativa}/{MAX_TENTATIVAS})"
                  f" — aguardando {espera}s: {type(e).__name__}")
            time.sleep(espera)
            return analisar_com_claude(client, texto, edicao, data, sistema_prompt, tentativa + 1)
        else:
            print(f"    ✗  Falha após {MAX_TENTATIVAS} tentativas — pulando edição")
            return []

    except anthropic.APIError as e:
        print(f"    ⚠  Erro na API: {e}")
        return []
    except anthropic.APIError as e:
        print(f"    ⚠  Erro na API: {e}")
        return []


def salvar_json(resultado: dict, caminho: Path):
    """Salva resultado ordenado por número de edição."""
    lista = sorted(resultado.values(), key=lambda e: e["edicao"])
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, indent=2)
    print(f"    💾 Salvo em {caminho.name}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Processa PDFs do Diário Oficial DPE/AM — Polo Médio Amazonas 2026"
    )
    parser.add_argument(
        "--api-key",
        help="Chave da API Anthropic (alternativa: variável ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--edicao", type=int,
        help="Processar apenas esta edição (útil para teste)"
    )
    parser.add_argument(
        "--forcar", action="store_true",
        help="Reprocessar edições já analisadas"
    )
    args = parser.parse_args()

    # ── API key ────────────────────────────────────────────────────────────────
    api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nErro: chave de API não encontrada.")
        print("Use --api-key sk-ant-... ou defina a variável ANTHROPIC_API_KEY\n")
        sys.exit(1)

    # ── Carregar defensores e construir filtros dinamicamente ─────────────────
    defensores = carregar_defensores()
    keywords   = construir_keywords(defensores)
    sistema_prompt = construir_sistema_prompt(defensores)
    nomes_defensores = [n for d in defensores for n in d.get("nome_busca", [])]
    print(f"\n✓ Defensores titulares carregados: {len(defensores)}")
    for d in defensores:
        print(f"   • {d['nome_completo']} → {', '.join(d['dps'])}")

    # ── Preparar pastas ────────────────────────────────────────────────────────
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Carregar JSON de entrada ───────────────────────────────────────────────
    if not JSON_ENTRADA.exists():
        print(f"Erro: arquivo não encontrado: {JSON_ENTRADA}")
        sys.exit(1)

    with open(JSON_ENTRADA, encoding="utf-8") as f:
        edicoes = json.load(f)

    if args.edicao:
        edicoes = [e for e in edicoes if e["edicao"] == args.edicao]
        if not edicoes:
            print(f"Edição {args.edicao} não encontrada no JSON de entrada.")
            sys.exit(1)

    # ── Carregar resultado existente (permite retomar processamento) ───────────
    resultado: dict = {}
    if JSON_SAIDA.exists():
        with open(JSON_SAIDA, encoding="utf-8") as f:
            dados_existentes = json.load(f)
        resultado = {e["edicao"]: e for e in dados_existentes}
        ja_processadas = sum(
            1 for e in resultado.values()
            if "portarias_estruturadas" in e or e.get("erro")
        )
        print(f"\n✓ Retomando — {ja_processadas} edição(ões) já processada(s)")

    client = anthropic.Anthropic(api_key=api_key)

    total = len(edicoes)
    total_tokens_in  = 0
    total_tokens_out = 0
    total_atos       = 0

    print(f"\n{'═' * 55}")
    print(f"  Processando {total} edição(ões) — modelo: {MODEL}")
    print(f"{'═' * 55}\n")

    for idx, edicao in enumerate(edicoes, 1):
        num  = edicao["edicao"]
        data = edicao["data_formatada"]
        url  = edicao["url"]

        print(f"[{idx:2d}/{total}] Edição {num} — {data}")

        # Pular se já processada (a menos que --forcar)
        if num in resultado and not args.forcar:
            atos_existentes = resultado[num].get("portarias_estruturadas", [])
            print(f"    ✓ Já processada ({len(atos_existentes)} ato(s)) — pulando")
            total_atos += len(atos_existentes)
            continue

        # ── Baixar PDF ─────────────────────────────────────────────────────────
        caminho_pdf = CACHE_DIR / f"edicao_{num}.pdf"
        if not caminho_pdf.exists():
            print(f"    ↓ Baixando PDF...")
            ok = baixar_pdf(url, caminho_pdf)
            if not ok:
                resultado[num] = {**edicao, "portarias_estruturadas": [], "erro": "falha_download"}
                salvar_json(resultado, JSON_SAIDA)
                continue
            time.sleep(1)  # Pausa entre downloads para não sobrecarregar o servidor

        # ── Extrair texto ──────────────────────────────────────────────────────
        print(f"    📄 Extraindo texto do PDF...")
        texto = extrair_texto_pdf(caminho_pdf)
        tamanho = len(texto)
        print(f"    📝 {tamanho:,} caracteres ({tamanho // 4:,} tokens estimados)")

        # ── Pré-filtro por palavras-chave ──────────────────────────────────────
        if not tem_palavra_chave(texto, keywords):
            print(f"    — Sem palavras-chave relevantes — pulando chamada à API")
            resultado[num] = {**edicao, "portarias_estruturadas": []}
            salvar_json(resultado, JSON_SAIDA)
            continue

        # ── Analisar com Claude ────────────────────────────────────────────────
        print(f"    🤖 Analisando com Claude Sonnet...")
        atos = analisar_com_claude(client, texto, num, data, sistema_prompt)
        n_atos = len(atos)
        total_atos += n_atos

        if n_atos > 0:
            print(f"    ✅ {n_atos} ato(s) relevante(s):")
            for ato in atos:
                cats   = ", ".join(ato.get("categorias", []))
                resumo = ato.get("resumo", "")
                numero = ato.get("numero", "")
                print(f"       • [{cats}] {numero}")
                print(f"         {resumo}")
        else:
            print(f"    — Sem atos relevantes encontrados pelo Claude")

        resultado[num] = {**edicao, "portarias_estruturadas": atos}
        salvar_json(resultado, JSON_SAIDA)

        # Pausa entre chamadas à API
        if idx < total:
            time.sleep(0.5)

    # ── Resumo final ───────────────────────────────────────────────────────────
    total_com_atos = sum(
        1 for e in resultado.values()
        if e.get("portarias_estruturadas")
    )
    print(f"\n{'═' * 55}")
    print(f"  ✓ Processamento concluído!")
    print(f"  Edições com atos relevantes : {total_com_atos}")
    print(f"  Total de atos encontrados   : {total_atos}")
    print(f"  Arquivo gerado              : {JSON_SAIDA.name}")
    print(f"{'═' * 55}\n")
    print("Próximo passo: abra o site e veja a aba Diário Oficial atualizada.")
    print("O site precisa ser ajustado para ler o novo arquivo JSON.")
    print("Avise quando o script terminar para fazermos isso.\n")


if __name__ == "__main__":
    main()
