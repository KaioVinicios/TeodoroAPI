# Request — Mocks

Solicitação de movimentação de estoque. Pode ser:
- **ENTRY** — entrada de insumo (reposição, compra, doação).
- **EXIT** — saída (consumo em atendimento, dispensação para tutor).
- **ADJUSTMENT** — acerto de inventário (perda, quebra, recontagem).

Precisa estar `is_approved=true` antes de virar um `StockMovement`. `quantity` deve ser `> 0` (validado no serializer).

## Campos
- `user` — id do `User` que abriu a request
- `request_type` — `ENTRY` | `EXIT` | `ADJUSTMENT`
- `supply` — id do `Supply`
- `description` — texto livre (máx. 100)
- `is_approved` — boolean (default `false`)
- `approval_date` — `YYYY-MM-DD` (opcional)
- `quantity` — float `> 0`

## Exemplos

```json
[
  {
    "user": 2,
    "request_type": "ENTRY",
    "supply": 1,
    "description": "Reposição mensal de Bravecto 1000mg - NF 4421",
    "is_approved": true,
    "approval_date": "2026-05-02",
    "quantity": 50
  },
  {
    "user": 2,
    "request_type": "ENTRY",
    "supply": 4,
    "description": "Compra de 10 caixas de Frontline Plus Gatos",
    "is_approved": true,
    "approval_date": "2026-05-05",
    "quantity": 10
  },
  {
    "user": 5,
    "request_type": "EXIT",
    "supply": 1,
    "description": "Dispensação Bravecto para tutor do cão Thor (15kg)",
    "is_approved": false,
    "approval_date": null,
    "quantity": 1
  },
  {
    "user": 5,
    "request_type": "EXIT",
    "supply": 2,
    "description": "NexGard Spectra para a cadela Mel (consulta de rotina)",
    "is_approved": true,
    "approval_date": "2026-05-10",
    "quantity": 1
  },
  {
    "user": 2,
    "request_type": "EXIT",
    "supply": 7,
    "description": "Rimadyl pós-cirúrgico paciente Luna - 7 dias de uso",
    "is_approved": true,
    "approval_date": "2026-05-12",
    "quantity": 7
  },
  {
    "user": 2,
    "request_type": "ADJUSTMENT",
    "supply": 12,
    "description": "Baixa de 5 lâminas de bisturi danificadas no recebimento",
    "is_approved": true,
    "approval_date": "2026-05-13",
    "quantity": 5
  },
  {
    "user": 5,
    "request_type": "EXIT",
    "supply": 10,
    "description": "Saco de Royal Canin Renal para paciente Bidu em tratamento renal",
    "is_approved": false,
    "approval_date": null,
    "quantity": 1
  }
]
```

> **Atenção:** o domínio espera que `EXIT` só seja aprovado quando `Supply.quantity > 0`, mas essa regra ainda não está implementada (ver [restrictions-per-app.md](../docs/restrictions-per-app.md)).
