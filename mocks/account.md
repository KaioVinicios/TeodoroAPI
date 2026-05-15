# Account — Mocks

Conta de um usuário do sistema. Representa veterinários, técnicos, administradores e tutores (customers). Quando `account_type == "admin"`, o `User` correspondente é automaticamente promovido a `is_superuser` / `is_staff` pelo `AccountServices`.

## Campos
- `username`, `password`, `email`, `first_name`, `last_name` (do `User`)
- `account_type` — `admin` | `manager` | `auditor` | `operator` | `customer`
- `cpf` (único, formato `XXX.XXX.XXX-XX`, dígitos verificadores válidos)
- `address`, `phone_number`
- `organization` — id de uma `Organization` (opcional)

## Exemplos

```json
[
  {
    "username": "dra.fernanda",
    "password": "ClinicaPet!2026",
    "email": "fernanda.lima@petvida.com.br",
    "first_name": "Fernanda",
    "last_name": "Lima",
    "account_type": "admin",
    "cpf": "529.982.247-25",
    "address": "Av. Rebouças, 1500 - São Paulo - SP",
    "phone_number": "(11) 91234-5678",
    "organization": 1
  },
  {
    "username": "carlos.estoque",
    "password": "Estoque@2026",
    "email": "carlos.santos@petvida.com.br",
    "first_name": "Carlos",
    "last_name": "Santos",
    "account_type": "operator",
    "cpf": "390.533.447-05",
    "address": "R. das Acácias, 200 - São Paulo - SP",
    "phone_number": "(11) 98765-4321",
    "organization": 1
  },
  {
    "username": "auditor.vet",
    "password": "Auditoria!2026",
    "email": "marcos.auditor@bichinhofeliz.com.br",
    "first_name": "Marcos",
    "last_name": "Pereira",
    "account_type": "auditor",
    "cpf": "248.438.034-80",
    "address": "R. Augusta, 2300 - São Paulo - SP",
    "phone_number": "(11) 99887-6543",
    "organization": 2
  },
  {
    "username": "gerente.bh",
    "password": "Gerencia@2026",
    "email": "ana.gerente@petcare24h.com.br",
    "first_name": "Ana",
    "last_name": "Oliveira",
    "account_type": "manager",
    "cpf": "859.715.080-09",
    "address": "Av. do Contorno, 8000 - Belo Horizonte - MG",
    "phone_number": "(31) 93456-7890",
    "organization": 3
  },
  {
    "username": "tutor.joao",
    "password": "MeuPet!2026",
    "email": "joao.silva@gmail.com",
    "first_name": "João",
    "last_name": "Silva",
    "account_type": "customer",
    "cpf": "111.444.777-35",
    "address": "R. dos Pinheiros, 50 - São Paulo - SP",
    "phone_number": "(11) 95555-1111",
    "organization": null
  }
]
```
