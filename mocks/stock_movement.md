# StockMovement — Mocks

Movimentação efetiva do estoque, **derivada de uma `Request` aprovada**. O serviço sobrescreve `type_of_movement` e `quantity` com os valores da request — esses dois campos são read-only no serializer e devem ser omitidos no payload de criação.

## Campos enviados pelo cliente
- `user` — id do `User` que executou a movimentação (geralmente o operador do estoque)
- `supply` — id do `Supply`
- `supply_lots` — array de ids de `SupplyLot` com status **`approved`** (obrigatório >= 1)
- `request` — id da `Request` aprovada (OneToOne — só uma movimentação por request)
- `description` — texto livre (opcional)

## Campos derivados (não enviar)
- `type_of_movement` — copiado de `request.request_type`
- `quantity` — copiado de `request.quantity`

## Exemplos

```json
[
  {
    "user": 2,
    "supply": 1,
    "supply_lots": [1],
    "request": 1,
    "description": "Entrada de 50 unidades de Bravecto 1000mg conferida e armazenada"
  },
  {
    "user": 2,
    "supply": 4,
    "supply_lots": [2],
    "request": 2,
    "description": "10 caixas de Frontline Plus Gatos guardadas na geladeira"
  },
  {
    "user": 2,
    "supply": 2,
    "supply_lots": [2],
    "request": 4,
    "description": "Dispensação NexGard Spectra para a cadela Mel"
  },
  {
    "user": 2,
    "supply": 7,
    "supply_lots": [1],
    "request": 5,
    "description": "Rimadyl entregue pós-cirurgia da Luna"
  },
  {
    "user": 2,
    "supply": 12,
    "supply_lots": [1],
    "request": 6,
    "description": "Baixa de 5 lâminas danificadas - inventário ajustado"
  }
]
```

> **Pré-condições para criar uma StockMovement:**
> 1. A `Request` precisa estar com `is_approved=true`.
> 2. A `Request` ainda não pode ter outra `StockMovement` vinculada.
> 3. Todos os `supply_lots` informados precisam estar com `status="approved"`.
