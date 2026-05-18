# Restrições por App

Este documento descreve as restrições (de modelo, de serviço e de view) atualmente aplicadas em cada app da TeodoroAPI. Também lista, ao final, regras que costumam ser esperadas no domínio mas que **ainda não estão implementadas**.

---

## `account`

### Modelo ([apps/account/models.py](../apps/account/models.py))
- `user`: OneToOne com `User`; deletar o usuário deleta a Account (CASCADE).
- `account_type`: obrigatório; precisa estar entre os valores de `AccountType` (`admin`, `manager`, `auditor`, `operator`, `customer`).
- `cpf`: único; passa pelo `validate_cpf` que exige 11 dígitos, rejeita CPFs com todos os dígitos iguais e valida os dois dígitos verificadores.
- `phone_number`: passa pelo `validate_phone_number`, exigindo 10 ou 11 dígitos (com DDD).
- `address`: obrigatório (máx. 255 caracteres).
- `organization`: opcional (`null=True`, `blank=True`, `SET_NULL`).

### Serviço ([apps/account/services.py](../apps/account/services.py))
- `create()` e `update()` sincronizam o `User` com o `account_type`: quando `account_type == AccountType.ADMIN`, o `User` é promovido com `is_superuser=True` e `is_staff=True`; em qualquer outro tipo, ambas as flags são revogadas para `False`. Garante a invariante **`account_type == "admin"` ⇔ `User.is_superuser`** nos dois sentidos (promoção e rebaixamento). Coberto pelos testes em `AccountServicesTests`.

### Views ([apps/account/views.py](../apps/account/views.py))
- `POST /accounts` (cadastro): `AllowAny` — qualquer cliente pode criar conta.
- `GET /accounts` (listagem): `IsAuthenticated` + `IsNotCustomer`.
- `GET /accounts/<pk>`: `IsAuthenticated`.
- `PATCH /accounts/<pk>`: `IsAuthenticated`.
- `DELETE /accounts/<pk>`: `IsAuthenticated` + `IsNotCustomer`.

---

## `organization`

### Modelo ([apps/organization/models.py](../apps/organization/models.py))
- `cnpj`: único; passa pelo `validate_cnpj` (14 dígitos, rejeita CNPJs com todos os dígitos iguais e valida dígitos verificadores).
- `phone_number`: mesmo validador do `account` (10 ou 11 dígitos).
- `name` e `address`: obrigatórios.

### Views ([apps/organization/views.py](../apps/organization/views.py))
- `GET` (lista e detalhe): `AllowAny` — acesso público.
- `POST`, `PATCH`, `DELETE`: `IsAuthenticated` + `IsNotCustomer`.

---

## `inspection`

### Modelo ([apps/inspection/models.py](../apps/inspection/models.py))
- `responsible`: precisa ser um `User` cuja `Account` tenha `account_type == "auditor"`. Se o usuário não tiver Account ou não for auditor, a validação falha (`validate_responsible_is_auditor`).
- `is_complete`: default `False`.
- `completion_date`: opcional (`null=True`, `blank=True`).

### Serviço ([apps/inspection/services.py](../apps/inspection/services.py))
- `create()`: força `is_complete=False` e `completion_date=None`, ignorando o que o cliente enviar.
- `update()`: **bloqueia qualquer atualização se a inspeção já estiver com `is_complete=True`** — uma vez completa, é imutável.

### Views ([apps/inspection/views.py](../apps/inspection/views.py))
- `GET` (lista e detalhe): `IsAuthenticated`.
- `POST`, `PATCH`, `DELETE`: `IsAuthenticated` + `IsAuditor` (apenas contas do tipo `auditor`).

---

## `supply`

### Modelo ([apps/supply/models.py](../apps/supply/models.py))
- `supply_label`: FK com `PROTECT` — não permite remover um `SupplyLabel` que ainda está em uso.
- `status`: precisa estar em `SupplyStatus` (`available`, `unavailable`, `reserved`, `in_use`, `depleted`, `damaged`); default `available`.
- `unit_of_measure`: precisa estar em `UnitOfMeasure` (`unit`, `box`, `pack`, `bottle`, `liter`, `milliliter`, `gram`, `kilogram`).
- `quantity`: **não é um campo**, é uma `@property` calculada a partir da soma das `quantity` dos `stock_movements` cujos `supply_lots` estão com status `APPROVED`. Lotes com status `pending`, `rejected`, `quarantine` ou `expired` não entram na conta.

### Views ([apps/supply/views.py](../apps/supply/views.py))
- `GET` (lista e detalhe): `IsAuthenticated`.
- `POST`, `PATCH`, `DELETE`: `IsAuthenticated` + `IsNotCustomer`.

---

## `supply_label`

### Modelo ([apps/supply_label/models.py](../apps/supply_label/models.py))
- `name`: obrigatório, não pode ser vazio.
- `supply_label_type`: precisa estar em `SupplyLabelType` (`medication`, `equipment`, `sterilization`, `nutrition`, `blood_product`, `other`).
- `category`: precisa estar em `SupplyLabelCategory` (`disposable`, `reusable`, `implantable`, `diagnostic`, `therapeutic`, `other`).
- `details`: opcional (máx. 100 caracteres).
- ⚠️ Os validadores em [apps/supply_label/validators.py](../apps/supply_label/validators.py) levantam `ValueError` em vez de `ValidationError`, então um valor inválido pode estourar como 500 em vez de 400.

### Views ([apps/supply_label/views.py](../apps/supply_label/views.py))
- ⚠️ Nenhuma `permission_classes` definida nas views. O acesso depende exclusivamente do default global do DRF.

---

## `supply_lot`

### Modelo ([apps/supply_lot/models.py](../apps/supply_lot/models.py))
- `status`: precisa estar em `SupplyLotStatus` (`pending`, `approved`, `rejected`, `quarantine`, `expired`); default `pending`.
- `inspection`: OneToOne com `PROTECT` — uma inspeção pode estar associada a no máximo um lote.
- `manufacturing_date < expiration_date`: validado em `clean()` via `validate_manufacturing_before_expiration`.

### Serviço ([apps/supply_lot/services.py](../apps/supply_lot/services.py))
- ⚠️ `create()` e `update()` usam `objects.create()` / `setattr` direto, **sem chamar `full_clean()`**. Isso significa que a checagem de datas só é acionada quando outro caller dispara `clean()`. Atenção a esse ponto.

### Views ([apps/supply_lot/views.py](../apps/supply_lot/views.py))
- ⚠️ Nenhuma `permission_classes` definida nas views.

---

## `request`

### Modelo ([apps/request/models.py](../apps/request/models.py))
- `user`: FK com `CASCADE` (deletar o usuário deleta as suas requests).
- `supply`: FK com `PROTECT`.
- `request_type`: precisa estar em `RequestType` (`ENTRY`, `EXIT`, `ADJUSTMENT`).
- `is_approved`: default `False`.
- `approval_date`: opcional.

### Views ([apps/request/views.py](../apps/request/views.py))
- Todos os métodos: `IsAuthenticated`. **Não há checagem de papel.** Customers podem listar, criar, ler, atualizar e deletar quaisquer requests (inclusive de outros usuários).

---

## `stock_movement`

### Modelo ([apps/stock_movement/models.py](../apps/stock_movement/models.py))
- `type_of_movement`: precisa estar em `StockMovementType` (`ENTRY`, `EXIT`, `ADJUSTMENT`).
- `user`, `supply`, `request`: todas `PROTECT`.
- `request`: OneToOne — uma request gera **no máximo um** stock movement.
- `clean()`: exige que a `Request` referenciada esteja com `is_approved=True`.

### Serviço ([apps/stock_movement/services.py](../apps/stock_movement/services.py) + [validators.py](../apps/stock_movement/validators.py))
- `create()` aplica, nesta ordem:
  1. `validate_request_is_approved`: a request precisa estar aprovada.
  2. `validate_request_not_already_consumed`: a request ainda não pode ter outro stock movement vinculado.
  3. `validate_supply_lots_approved`: pelo menos um lote precisa ser informado, **e todos os lotes precisam estar com status `APPROVED`**.
  4. `type_of_movement` e `quantity` são **derivados da request** — o que o cliente enviar nesses campos é ignorado.
- `update()`: somente o campo `description` pode ser alterado após a criação; todo o resto é imutável.

### Views ([apps/stock_movement/views.py](../apps/stock_movement/views.py))
- `GET` (lista e detalhe), `POST`, `PATCH`: `IsAuthenticated`. Sem checagem de papel.
- Não há endpoint de `DELETE`.

---

## Regras esperadas que ainda não estão implementadas

Estes pontos costumam ser esperados pelo domínio, mas hoje **não estão sendo aplicados em lugar algum**:

1. **`EXIT` só é permitido se a quantidade do supply for positiva.** Não há validação que impeça uma request ou um stock movement de tipo `EXIT` quando `Supply.quantity <= 0`.
2. **`Supply.quantity >= 0`.** Como `quantity` é uma soma derivada, nada impede que ela fique negativa.
3. **`Request.quantity >= 0` e `StockMovement.quantity >= 0`.** Ambos são `FloatField` sem `MinValueValidator`.
4. **Customer só pode criar/ver as próprias requests.** O docstring de `AccountType.CUSTOMER` declara isso, mas as views de `request` não filtram por dono e não exigem papel além de `IsAuthenticated`.
5. **CRUD exclusivo de Operator** em Inspections, Requests, StockMovements, Supplies, SupplyLabels e SupplyLots (conforme docstring de `AccountType.OPERATOR`) — atualmente apenas `IsNotCustomer` ou `IsAuditor` são usados; não existe permissão `IsOperator`.
6. **Auditor com acesso read-only a tudo.** Hoje o `IsAuditor` é usado para *permitir escrita* em Inspections, e não para restringir auditores a leitura nos demais recursos.
7. **`SupplyLot` create/update** não chamam `full_clean()` no serviço — a regra `manufacturing_date < expiration_date` pode não disparar pelo fluxo da API.
8. **Validadores de `supply_label`** levantam `ValueError` em vez de `ValidationError`.
