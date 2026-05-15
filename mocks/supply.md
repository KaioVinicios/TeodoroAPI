# Supply — Mocks

Item de estoque associado a um `SupplyLabel`. A **`quantity` não é enviada** — é calculada a partir dos `StockMovement` cujos `SupplyLot` estão `APPROVED`.

## Campos
- `supply_label` — id do `SupplyLabel`
- `status` — `available` | `unavailable` | `reserved` | `in_use` | `depleted` | `damaged`
- `description` — texto livre
- `unit_of_measure` — `unit` | `box` | `pack` | `bottle` | `liter` | `milliliter` | `gram` | `kilogram`

## Exemplos

```json
[
  {
    "supply_label": 1,
    "status": "available",
    "description": "Bravecto 1000mg - lote de prateleira do estoque central",
    "unit_of_measure": "unit"
  },
  {
    "supply_label": 2,
    "status": "available",
    "description": "NexGard Spectra 3-7,5kg - comprimidos mastigáveis individuais",
    "unit_of_measure": "unit"
  },
  {
    "supply_label": 3,
    "status": "reserved",
    "description": "Simparic 80mg reservado para campanha antiparasitária trimestral",
    "unit_of_measure": "unit"
  },
  {
    "supply_label": 4,
    "status": "available",
    "description": "Frontline Plus Gatos - caixa contendo 3 pipetas",
    "unit_of_measure": "box"
  },
  {
    "supply_label": 5,
    "status": "depleted",
    "description": "Drontal Plus 10kg - estoque esgotado, aguardando reposição",
    "unit_of_measure": "unit"
  },
  {
    "supply_label": 6,
    "status": "in_use",
    "description": "Apoquel 16mg em uso por pacientes em tratamento contínuo",
    "unit_of_measure": "unit"
  },
  {
    "supply_label": 7,
    "status": "available",
    "description": "Rimadyl 75mg - frasco com 14 comprimidos",
    "unit_of_measure": "bottle"
  },
  {
    "supply_label": 8,
    "status": "available",
    "description": "Vacina V10 - frascos refrigerados na geladeira do consultório",
    "unit_of_measure": "bottle"
  },
  {
    "supply_label": 9,
    "status": "available",
    "description": "Bolsa de hemácias DEA 1.1+ disponível no banco de sangue",
    "unit_of_measure": "milliliter"
  },
  {
    "supply_label": 10,
    "status": "available",
    "description": "Royal Canin Renal Canine - saco de 10kg lacrado",
    "unit_of_measure": "kilogram"
  },
  {
    "supply_label": 11,
    "status": "available",
    "description": "Seringa descartável 5ml - pacote com 100 unidades",
    "unit_of_measure": "pack"
  },
  {
    "supply_label": 12,
    "status": "damaged",
    "description": "Lâminas de bisturi nº 15 - embalagem violada, descartar",
    "unit_of_measure": "unit"
  }
]
```
