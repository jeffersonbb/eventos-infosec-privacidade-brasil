# Como contribuir

O jeito mais simples é abrir uma issue ([sugerir evento](../../issues/new?template=sugerir-evento.yml) ou [corrigir evento](../../issues/new?template=corrigir-evento.yml)). Toda semana as issues abertas são revisadas e incorporadas quando têm fonte.

## Critérios

- Tema: cibersegurança, segurança da informação, hacking, privacidade ou proteção de dados.
- Realizado no Brasil, ou online com foco no público brasileiro.
- Aberto ao público (gratuito ou pago). Eventos só para convidados não entram. Eventos organizados por uma única empresa entram, desde que abertos ao público.
- Data confirmada em fonte verificável, de preferência o site oficial ou a página de inscrição.

## Editando o `eventos.json`

Cada evento em `eventos`:

| Campo | Obrigatório | Exemplo |
|---|---|---|
| `id` | sim | `bsides-rio-2027` (minúsculas, único, com o ano) |
| `nome` | sim | `BSides Rio de Janeiro 2027` |
| `inicio`, `fim` | sim | `2027-03-20` (AAAA-MM-DD; mesmo dia se for de um dia só) |
| `cidade`, `uf` | sim | `Rio de Janeiro`, `RJ` (online: `Online`, `BR`) |
| `local` | não | `Riocentro` |
| `formato` | sim | `Presencial`, `Online` ou `Híbrido` |
| `entrada` | sim | `Gratuito`, `Pago`, `Gratuito com inscrição`… |
| `tema` | sim | `Cibersegurança`, `Privacidade` ou `Cibersegurança e Privacidade` |
| `resumo` | não | uma frase |
| `site` | sim | site oficial do evento |
| `fonte` | sim | página onde a data foi confirmada |
| `verificado_em` | sim | data em que a fonte foi conferida |
| `cfp` | não | `{"url": "...", "prazo": "2027-01-31"}` |

Eventos recorrentes ainda sem data entram em `a_confirmar`, com `nome`, `previsao`, `cidade`, `uf`, `tema` e `site`.

Para conferir antes de enviar:

```
python scripts/gerar.py
```

O script valida os campos, remove eventos que já passaram e atualiza o README e o `eventos.ics`.
