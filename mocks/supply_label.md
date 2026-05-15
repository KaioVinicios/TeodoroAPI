# SupplyLabel — Mocks

`SupplyLabel` é o **rótulo/identidade** de um insumo (nome comercial, tipo, categoria). Um `Supply` aponta para um `SupplyLabel` via FK, então cada medicação/insumo do estoque é descrito aqui uma vez.

## Campos
- `name` — nome comercial (ex.: "Bravecto 1000mg")
- `supply_label_type` — `medication` | `equipment` | `sterilization` | `nutrition` | `blood_product` | `other`
- `category` — `disposable` | `reusable` | `implantable` | `diagnostic` | `therapeutic` | `other`
- `details` — texto livre opcional (máx. 100)

## Exemplos

```json
[
  {
    "name": "Bravecto 1000mg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Antiparasitário oral para cães de 20-40kg, ação 12 semanas"
  },
  {
    "name": "NexGard Spectra 3-7,5kg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Antipulgas, carrapatos e vermífugo para cães pequenos"
  },
  {
    "name": "Simparic 80mg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Sarolaner mastigável para cães de 20-40kg"
  },
  {
    "name": "Frontline Plus Gatos",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Pipeta antipulgas e carrapatos tópica para gatos"
  },
  {
    "name": "Drontal Plus 10kg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Vermífugo de amplo espectro para cães"
  },
  {
    "name": "Apoquel 16mg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Oclacitinib para controle de prurido alérgico"
  },
  {
    "name": "Rimadyl 75mg",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Carprofeno anti-inflamatório para cães"
  },
  {
    "name": "Vacina V10 Vanguard Plus",
    "supply_label_type": "medication",
    "category": "therapeutic",
    "details": "Vacina decuplaa cães - cinomose, parvo, lepto, etc."
  },
  {
    "name": "Hemácias Caninas Tipo DEA 1.1+",
    "supply_label_type": "blood_product",
    "category": "therapeutic",
    "details": "Bolsa 250ml para transfusão sanguínea em cães"
  },
  {
    "name": "Royal Canin Renal Canine 10kg",
    "supply_label_type": "nutrition",
    "category": "therapeutic",
    "details": "Ração terapêutica para cães com insuficiência renal"
  },
  {
    "name": "Seringa Descartável 5ml",
    "supply_label_type": "equipment",
    "category": "disposable",
    "details": "Seringa estéril com agulha 25x7"
  },
  {
    "name": "Bisturi Lâmina nº 15",
    "supply_label_type": "equipment",
    "category": "disposable",
    "details": "Lâmina cirúrgica estéril"
  },
  {
    "name": "Autoclave Pacote Cirúrgico",
    "supply_label_type": "sterilization",
    "category": "reusable",
    "details": "Pacote padrão para esterilização em autoclave"
  },
  {
    "name": "Microchip ISO 11784",
    "supply_label_type": "equipment",
    "category": "implantable",
    "details": "Chip de identificação subcutâneo 134.2 kHz"
  },
  {
    "name": "Tira Reagente Glicemia",
    "supply_label_type": "equipment",
    "category": "diagnostic",
    "details": "Tira para glicosímetro veterinário"
  }
]
```
