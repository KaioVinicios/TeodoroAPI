# SupplyLot — Mocks

Lote físico de um insumo, vinculado a uma `Inspection`. Só lotes `approved` contam para a `quantity` calculada do `Supply`.

## Campos
- `status` — `pending` | `approved` | `rejected` | `quarantine` | `expired`
- `inspection` — id da `Inspection` (OneToOne — uma inspeção, um lote)
- `manufacturing_date` — `YYYY-MM-DD` (precisa ser **antes** de `expiration_date`)
- `expiration_date` — `YYYY-MM-DD`
- `description` — texto livre

## Exemplos

```json
[
  {
    "status": "approved",
    "inspection": 1,
    "manufacturing_date": "2026-01-15",
    "expiration_date": "2028-01-15",
    "description": "Lote BRV-2601-A de Bravecto 1000mg, recebido pelo fornecedor MSD"
  },
  {
    "status": "approved",
    "inspection": 2,
    "manufacturing_date": "2026-02-10",
    "expiration_date": "2027-08-10",
    "description": "Lote NXG-7754 de NexGard Spectra, fornecedor Boehringer Ingelheim"
  },
  {
    "status": "pending",
    "inspection": 3,
    "manufacturing_date": "2026-03-20",
    "expiration_date": "2028-03-20",
    "description": "Lote SIM-9912 de Simparic aguardando aprovação do auditor"
  },
  {
    "status": "quarantine",
    "inspection": 4,
    "manufacturing_date": "2025-11-05",
    "expiration_date": "2027-11-05",
    "description": "Lote Frontline com indício de violação na caixa, em quarentena"
  },
  {
    "status": "rejected",
    "inspection": 5,
    "manufacturing_date": "2025-08-01",
    "expiration_date": "2026-08-01",
    "description": "Lote Apoquel reprovado: cadeia de frio quebrada no transporte"
  },
  {
    "status": "expired",
    "inspection": 6,
    "manufacturing_date": "2023-06-15",
    "expiration_date": "2025-06-15",
    "description": "Lote Drontal Plus vencido, aguardando descarte conforme RDC ANVISA"
  }
]
```
