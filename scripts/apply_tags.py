#!/usr/bin/env python3
"""Apply taxonomy (tags + category) to each entry in transcripts/index.json.

Tags categorize posts thematically. Category separates the spinal column
('core') from outliers ('lateral') so the index can show outliers at the end.

Run after adding a new entry — TAG_MAP below is the source of truth.
"""
import json
import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(PROJECT_DIR, "transcripts", "index.json")

# slug -> {"tags": [...], "category": "core"|"lateral"}
# Available tags: claude-code, agentic-engineering, carreira, soft-skills,
# produto, tutoriais, ia-2026, financas
TAG_MAP = {
    "por-que-metade-dos-product-managers-esta-em-apuros": {
        "tags": ["produto", "carreira", "soft-skills", "agentic-engineering"],
        "category": "core",
    },
    "ryan-lopopolo-engenharia-de-harness-quando-humanos-conduzem-e-agentes-executam": {
        "tags": ["agentic-engineering", "claude-code"],
        "category": "core",
    },
    "chefe-do-claude-code-o-que-acontece-depois-que-a-programacao-for-resolvida": {
        "tags": ["claude-code", "agentic-engineering", "carreira"],
        "category": "core",
    },
    "guia-completo-claude-iniciante-sistema-operacional-ia": {
        "tags": ["claude-code", "tutoriais"],
        "category": "core",
    },
    "claude-code-leak-what-weve-learned-so-far": {
        "tags": ["claude-code"],
        "category": "core",
    },
    "como-construi-sistema-suporte-cliente-ia-nivel-producao": {
        "tags": ["claude-code", "tutoriais", "agentic-engineering"],
        "category": "core",
    },
    "de-ides-para-agentes-de-ia-steve-yegge": {
        "tags": ["agentic-engineering"],
        "category": "core",
    },
    "do-prompt-a-producao-o-que-e-engenharia-agentica": {
        "tags": ["agentic-engineering"],
        "category": "core",
    },
    "engenharia-agentica-contexto-guardrails-e-criatividade": {
        "tags": ["agentic-engineering"],
        "category": "core",
    },
    "engenheiro-senior-fluxo-desenvolvimento-especificacoes-ia": {
        "tags": ["agentic-engineering", "tutoriais"],
        "category": "core",
    },
    "estado-da-ia-2026-ponto-de-inflexao-simon-willison": {
        "tags": ["ia-2026", "agentic-engineering"],
        "category": "core",
    },
    "fluxos-de-trabalho-agenticos-don-syme": {
        "tags": ["agentic-engineering"],
        "category": "core",
    },
    "politica-corporativa-tech-tudo-que-ninguem-te-conta": {
        "tags": ["carreira", "soft-skills"],
        "category": "core",
    },
    "praticas-de-engenharia-para-agentes-de-codigo-simon-willison": {
        "tags": ["agentic-engineering"],
        "category": "core",
    },
    "roteiro-engenheiro-ia-para-desenvolvedores-de-software": {
        "tags": ["carreira", "agentic-engineering"],
        "category": "core",
    },
    "um-agente-nao-e-suficiente-programacao-agentica-alem-do-claude-code": {
        "tags": ["agentic-engineering", "claude-code"],
        "category": "core",
    },
    "obsidian-claude-code-pensamento": {
        "tags": ["claude-code", "soft-skills"],
        "category": "core",
    },
    "conselhos-de-carreira-em-ia-andrew-ng-lawrence-moroney-stanford": {
        "tags": ["carreira", "agentic-engineering"],
        "category": "core",
    },
    "entendendo-rony-coder": {
        "tags": ["soft-skills", "carreira"],
        "category": "core",
    },
    "ia-agentica-progressao-uso-modelos-linguagem-stanford": {
        "tags": ["agentic-engineering", "ia-2026"],
        "category": "core",
    },
    "por-que-paramos-de-construir-agentes-e-comecamos-a-construir-skills": {
        "tags": ["claude-code", "agentic-engineering"],
        "category": "core",
    },
    "fabio-akita-flow-588": {
        "tags": ["claude-code", "carreira", "agentic-engineering"],
        "category": "core",
    },
    "curso-completo-claude-code-4-horas": {
        "tags": ["claude-code", "tutoriais"],
        "category": "core",
    },
    "boris-cherny-dicas-praticas-para-usar-claude-code": {
        "tags": ["claude-code", "tutoriais"],
        "category": "core",
    },
    # outliers — espinha lateral
    "trading-com-order-flow-mercado-global-ao-chines": {
        "tags": ["financas"],
        "category": "lateral",
    },
    "financas-comportamentais-robert-shiller-yale": {
        "tags": ["financas", "soft-skills"],
        "category": "lateral",
    },
}


def main() -> None:
    with open(INDEX_PATH) as f:
        index = json.load(f)

    missing = []
    for entry in index:
        slug = entry.get("slug")
        meta = TAG_MAP.get(slug)
        if not meta:
            missing.append(slug)
            continue
        entry["tags"] = meta["tags"]
        entry["category"] = meta["category"]

    if missing:
        print(f"WARN: no tag mapping for: {missing}", file=sys.stderr)

    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"applied tags+category to {len(index) - len(missing)} entries")


if __name__ == "__main__":
    main()
