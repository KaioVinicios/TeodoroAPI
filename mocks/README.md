# Mocks

Dados de exemplo, em JSON, para cada modelo da TeodoroAPI. O domínio é **gestão de insumos para clínicas/hospitais veterinários** — medicações veterinárias (Bravecto, NexGard, Simparic, Frontline, Apoquel, Rimadyl…), nutrição terapêutica, hemoderivados e equipamentos médicos.

## Ordem sugerida de seed

Os modelos têm dependências entre si. Crie nesta ordem para garantir que as FKs resolvam:

1. [organization.md](organization.md) — clínicas/distribuidoras
2. [account.md](account.md) — usuários (admin, manager, auditor, operator, customer); FK opcional → Organization
3. [supply_label.md](supply_label.md) — rótulos dos insumos (nome, tipo, categoria)
4. [supply.md](supply.md) — itens de estoque; FK → SupplyLabel
5. [inspection.md](inspection.md) — inspeções; FK → User (auditor)
6. [supply_lot.md](supply_lot.md) — lotes físicos; OneToOne → Inspection
7. [request.md](request.md) — solicitações de movimentação; FK → User, Supply
8. [stock_movement.md](stock_movement.md) — movimentações efetivas; FK → Request, Supply, SupplyLots

## Restrições importantes

Veja [docs/restrictions-per-app.md](../docs/restrictions-per-app.md) para a lista completa. Em resumo:

- `account_type == "admin"` promove o `User` para `is_superuser`/`is_staff` automaticamente.
- `Inspection` só pode ser criada por usuários `auditor`.
- `SupplyLot.manufacturing_date` precisa ser **antes** de `expiration_date`.
- `StockMovement` exige `Request.is_approved=true` e todos os `supply_lots` com status `approved`.
- `Supply.quantity` é **calculado** a partir dos `StockMovement` cujos lotes estão `approved`.
