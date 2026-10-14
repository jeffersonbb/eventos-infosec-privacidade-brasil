"""Gera README.md e eventos.ics a partir de eventos.json.

- Remove de eventos.json os eventos que já terminaram (horário de Brasília).
- Ordena os eventos por data.
- Reescreve a tabela do README entre os marcadores.
- Gera o calendário eventos.ics para assinatura.

Uso: python scripts/gerar.py  (só biblioteca padrão)
"""

import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_JSON = RAIZ / "eventos.json"
ARQ_README = RAIZ / "README.md"
ARQ_ICS = RAIZ / "eventos.ics"

BRT = timezone(timedelta(hours=-3))  # Brasil sem horário de verão desde 2019
UID_DOMINIO = "eventos-infosec-privacidade-brasil"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

OBRIGATORIOS = ["id", "nome", "inicio", "fim", "cidade", "uf", "formato",
                "entrada", "tema", "site", "fonte", "verificado_em"]
FORMATOS = {"Presencial", "Online", "Híbrido"}
TEMAS = {"Cibersegurança", "Privacidade", "Cibersegurança e Privacidade"}

TABELA_INICIO = "<!-- TABELA:INICIO -->"
TABELA_FIM = "<!-- TABELA:FIM -->"


def hoje_brt() -> date:
    return datetime.now(BRT).date()


def validar(dados: dict) -> list[str]:
    erros = []
    ids = set()
    for i, ev in enumerate(dados.get("eventos", [])):
        rot = ev.get("id") or f"eventos[{i}]"
        for campo in OBRIGATORIOS:
            if not ev.get(campo):
                erros.append(f"{rot}: campo obrigatório ausente: {campo}")
        if ev.get("id") in ids:
            erros.append(f"{rot}: id duplicado")
        ids.add(ev.get("id"))
        try:
            ini = date.fromisoformat(ev["inicio"])
            fim = date.fromisoformat(ev["fim"])
            if fim < ini:
                erros.append(f"{rot}: fim antes do início")
        except (KeyError, TypeError, ValueError):
            erros.append(f"{rot}: datas devem estar no formato AAAA-MM-DD")
        if ev.get("formato") and ev["formato"] not in FORMATOS:
            erros.append(f"{rot}: formato deve ser um de {sorted(FORMATOS)}")
        if ev.get("tema") and ev["tema"] not in TEMAS:
            erros.append(f"{rot}: tema deve ser um de {sorted(TEMAS)}")
        cfp = ev.get("cfp")
        if cfp:
            if not cfp.get("url"):
                erros.append(f"{rot}: cfp precisa de url")
            if cfp.get("prazo"):
                try:
                    date.fromisoformat(cfp["prazo"])
                except ValueError:
                    erros.append(f"{rot}: cfp.prazo deve estar no formato AAAA-MM-DD")
    for i, ev in enumerate(dados.get("a_confirmar", [])):
        for campo in ["nome", "previsao", "cidade", "uf", "site"]:
            if not ev.get(campo):
                erros.append(f"a_confirmar[{i}]: campo obrigatório ausente: {campo}")
    return erros


def fmt_data(ini: date, fim: date) -> str:
    if ini == fim:
        return ini.strftime("%d/%m/%Y")
    if ini.year == fim.year and ini.month == fim.month:
        return f"{ini.day:02d} a {fim.strftime('%d/%m/%Y')}"
    return f"{ini.strftime('%d/%m')} a {fim.strftime('%d/%m/%Y')}"


def cel(texto: str) -> str:
    return str(texto).replace("|", "\\|").replace("\n", " ")


def gerar_tabela(eventos: list[dict], a_confirmar: list[dict], hoje: date,
                 revisado_em: date) -> str:
    linhas = [f"_Última revisão das fontes: {revisado_em.strftime('%d/%m/%Y')} · "
              f"{len(eventos)} eventos com data confirmada._"]
    if not eventos:
        linhas += ["", "Nenhum evento com data confirmada no momento."]
    mes_atual = None
    for ev in eventos:
        ini = date.fromisoformat(ev["inicio"])
        fim = date.fromisoformat(ev["fim"])
        mes = (ini.year, ini.month)
        if mes != mes_atual:
            mes_atual = mes
            linhas += ["", f"### {MESES[ini.month - 1].capitalize()} de {ini.year}", "",
                       "| Evento | Data | Local | Formato | Entrada | Tema | Chamada de palestras |",
                       "|---|---|---|---|---|---|---|"]
        nome = f"[{cel(ev['nome'])}]({ev['site']})"
        local = f"{cel(ev['cidade'])}/{ev['uf']}"
        if ev.get("local"):
            local = f"{cel(ev['local'])}, {local}"
        cfp = "–"
        if ev.get("cfp"):
            prazo = ev["cfp"].get("prazo")
            if prazo and date.fromisoformat(prazo) < hoje:
                cfp = "Encerrada"
            else:
                rot = f"até {date.fromisoformat(prazo).strftime('%d/%m/%Y')}" if prazo else "aberta"
                cfp = f"[{rot}]({ev['cfp']['url']})"
        linhas.append(f"| {nome} | {fmt_data(ini, fim)} | {local} | {ev['formato']} | "
                      f"{cel(ev['entrada'])} | {ev['tema']} | {cfp} |")
    if a_confirmar:
        linhas += ["", "### Próximas edições com data a confirmar", "",
                   "Eventos recorrentes cuja próxima data ainda não foi anunciada oficialmente. "
                   "Eles não entram no calendário até a confirmação.", "",
                   "| Evento | Previsão | Local | Tema |", "|---|---|---|---|"]
        for ev in sorted(a_confirmar, key=lambda e: e["nome"].lower()):
            linhas.append(f"| [{cel(ev['nome'])}]({ev['site']}) | {cel(ev['previsao'])} | "
                          f"{cel(ev['cidade'])}/{ev['uf']} | {ev.get('tema', '–')} |")
    return "\n".join(linhas).strip() + "\n"


def atualizar_readme(tabela: str) -> None:
    texto = ARQ_README.read_text(encoding="utf-8")
    padrao = re.compile(re.escape(TABELA_INICIO) + r".*?" + re.escape(TABELA_FIM), re.S)
    if not padrao.search(texto):
        sys.exit("README.md sem os marcadores da tabela")
    novo = padrao.sub(lambda _: f"{TABELA_INICIO}\n{tabela}{TABELA_FIM}", texto)
    ARQ_README.write_text(novo, encoding="utf-8", newline="\n")


def ics_escape(texto: str) -> str:
    return (str(texto).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def ics_dobrar(linha: str) -> list[str]:
    """Quebra linhas em até 75 octetos (RFC 5545)."""
    partes, atual = [], ""
    for ch in linha:
        limite = 75 if not partes else 74
        if len((atual + ch).encode("utf-8")) > limite:
            partes.append(atual)
            atual = ch
        else:
            atual += ch
    partes.append(atual)
    return [partes[0]] + [" " + p for p in partes[1:]]


def gerar_ics(eventos: list[dict]) -> str:
    linhas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//{UID_DOMINIO}//PT-BR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Eventos de Cibersegurança e Privacidade (Brasil)",
        "X-WR-TIMEZONE:America/Sao_Paulo",
        "X-WR-CALDESC:Eventos de cibersegurança\\, privacidade e LGPD no Brasil. "
        f"Mantido em github.com/jeffersonbb/{UID_DOMINIO}",
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    for ev in eventos:
        ini = date.fromisoformat(ev["inicio"])
        fim = date.fromisoformat(ev["fim"]) + timedelta(days=1)  # DTEND exclusivo
        carimbo = date.fromisoformat(ev["verificado_em"]).strftime("%Y%m%dT000000Z")
        local = f"{ev['cidade']}/{ev['uf']}"
        if ev.get("local"):
            local = f"{ev['local']}, {local}"
        if ev["formato"] == "Online":
            local = "Online"
        desc = [f"{ev['tema']} · {ev['formato']} · {ev['entrada']}"]
        if ev.get("resumo"):
            desc.append(ev["resumo"])
        if ev.get("cfp"):
            prazo = ev["cfp"].get("prazo")
            desc.append("Chamada de palestras: " + ev["cfp"]["url"]
                        + (f" (prazo {date.fromisoformat(prazo).strftime('%d/%m/%Y')})" if prazo else ""))
        desc.append(f"Site: {ev['site']}")
        desc.append(f"Fonte da data: {ev['fonte']}")
        bloco = [
            "BEGIN:VEVENT",
            f"UID:{ev['id']}@{UID_DOMINIO}",
            f"DTSTAMP:{carimbo}",
            f"LAST-MODIFIED:{carimbo}",
            f"DTSTART;VALUE=DATE:{ini.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{fim.strftime('%Y%m%d')}",
            f"SUMMARY:{ics_escape(ev['nome'])}",
            f"LOCATION:{ics_escape(local)}",
            f"DESCRIPTION:{ics_escape(chr(10).join(desc))}",
            f"URL:{ev['site']}",
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
        for linha in bloco:
            linhas.extend(ics_dobrar(linha))
    linhas.append("END:VCALENDAR")
    return "\r\n".join(linhas) + "\r\n"


def main() -> None:
    dados = json.loads(ARQ_JSON.read_text(encoding="utf-8"))
    erros = validar(dados)
    if erros:
        print("Erros em eventos.json:", *erros, sep="\n- ")
        sys.exit(1)

    hoje = hoje_brt()
    eventos = [e for e in dados.get("eventos", []) if date.fromisoformat(e["fim"]) >= hoje]
    removidos = len(dados.get("eventos", [])) - len(eventos)
    eventos.sort(key=lambda e: (e["inicio"], e["nome"].lower()))
    dados["eventos"] = eventos

    ARQ_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    revisado_em = date.fromisoformat(dados.get("revisado_em") or hoje.isoformat())
    atualizar_readme(gerar_tabela(eventos, dados.get("a_confirmar", []), hoje, revisado_em))
    ARQ_ICS.write_bytes(gerar_ics(eventos).encode("utf-8"))
    print(f"{len(eventos)} eventos publicados, {removidos} removidos por já terem passado.")


if __name__ == "__main__":
    main()
