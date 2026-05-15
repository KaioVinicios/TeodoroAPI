# Inspection — Mocks

Inspeção registrada antes da aprovação de um `SupplyLot`. Só pode ser criada por um `User` cuja `Account` seja `auditor`.

## Campos
- `responsible` — id de um `User` com `Account.account_type == "auditor"`
- `is_complete` — boolean (default `false`; o serviço força `false` no create)
- `completion_date` — data ISO `YYYY-MM-DD` (opcional)

## Exemplos

```json
[
  {
    "responsible": 3,
    "is_complete": false,
    "completion_date": null
  },
  {
    "responsible": 3,
    "is_complete": true,
    "completion_date": "2026-04-12"
  },
  {
    "responsible": 3,
    "is_complete": true,
    "completion_date": "2026-05-02"
  },
  {
    "responsible": 3,
    "is_complete": false,
    "completion_date": null
  }
]
```

> **Lembrete:** `responsible` precisa apontar para um usuário cujo `Account` tenha `account_type="auditor"`. Veja [account.md](account.md) — no exemplo, é o usuário `auditor.vet` (id 3).
