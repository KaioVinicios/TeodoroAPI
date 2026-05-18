# Organization — Mocks

Organizações são clínicas/hospitais veterinários e fornecedores parceiros. Usadas para vincular contas (`Account.organization`).

## Campos
- `name` (string)
- `cnpj` (string, único, formato `XX.XXX.XXX/XXXX-XX`)
- `address` (string)
- `phone_number` (string, formato `(XX) XXXXX-XXXX`)

## Exemplos

```json
[
  {
    "name": "Clínica Veterinária Pet Vida",
    "cnpj": "11.222.333/0001-81",
    "address": "Av. Rebouças, 1500 - Pinheiros, São Paulo - SP",
    "phone_number": "(11) 91234-5678"
  },
  {
    "name": "Hospital Veterinário Bichinho Feliz",
    "cnpj": "39.346.861/0001-61",
    "address": "R. Augusta, 2300 - Cerqueira César, São Paulo - SP",
    "phone_number": "(11) 99887-6543"
  },
  {
    "name": "PetCare 24h Belo Horizonte",
    "cnpj": "45.723.174/0001-10",
    "address": "Av. do Contorno, 8000 - Lourdes, Belo Horizonte - MG",
    "phone_number": "(31) 93456-7890"
  },
  {
    "name": "AnimalLife Distribuidora",
    "cnpj": "27.865.757/0001-02",
    "address": "Rod. Anhanguera, km 42 - Cajamar - SP",
    "phone_number": "(11) 97777-1234"
  }
]
```
