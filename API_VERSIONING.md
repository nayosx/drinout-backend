# API Versioning Guide

Esta guia documenta como conviven las versiones actuales de la API de lavanderia y como se esperan los objetos en los metodos principales.

## Resumen

- `v1` sigue activa para compatibilidad con el frontend actual.
- `v1` usa rutas historicas sin prefijo de version.
- `v2` agrega nuevas rutas con prefijo `/v2`.
- Ambas versiones usan autenticacion JWT con `Authorization: Bearer <token>`.

## Autenticacion

Primero obten el token en:

- `POST /auth/login`

Ejemplo:

```json
{
  "username": "tu_usuario",
  "password": "tu_password"
}
```

Luego usa el token en cada request protegido:

```http
Authorization: Bearer eyJ...
```

## Como funcionan las versiones

### v1

`v1` es la API heredada. Mantiene el comportamiento previo y no exige los nuevos objetos de prendas y extras.

Ejemplos de rutas activas en `v1`:

- `GET /laundry_services`
- `GET /laundry_services/<id>`
- `POST /laundry_services`
- `PUT /laundry_services/<id>`
- `DELETE /laundry_services/<id>`
- `GET /garment_types`
- `POST /garment_types`

### v2

`v2` es la nueva API pensada para el frontend nuevo. En esta version se separa:

- el servicio principal
- las prendas recibidas
- los extras aplicados
- el catalogo de tipos de prenda
- el catalogo de extras

Rutas activas en `v2`:

- `GET /v2/laundry_services`
- `GET /v2/laundry_services/<id>`
- `POST /v2/laundry_services`
- `PUT /v2/laundry_services/<id>`
- `DELETE /v2/laundry_services/<id>`
- `GET /v2/garment_types`
- `GET /v2/garment_types/<id>`
- `POST /v2/garment_types`
- `PUT /v2/garment_types/<id>`
- `DELETE /v2/garment_types/<id>`
- `GET /v2/service_extra_types`
- `GET /v2/service_extra_types/<id>`
- `POST /v2/service_extra_types`
- `PUT /v2/service_extra_types/<id>`
- `DELETE /v2/service_extra_types/<id>`

## Objetos esperados en v1

### `POST /laundry_services`

Objeto esperado:

```json
{
  "client_id": 5,
  "client_address_id": 4,
  "scheduled_pickup_at": "2026-03-21T10:30:00",
  "status": "PENDING",
  "service_label": "NORMAL",
  "transaction_id": null
}
```

Campos:

- `client_id`: entero
- `client_address_id`: entero
- `scheduled_pickup_at`: fecha ISO
- `status`: `PENDING`, `STARTED`, `IN_PROGRESS`, `READY_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`
- `service_label`: `NORMAL` o `EXPRESS`
- `transaction_id`: entero o `null`

### `PUT /laundry_services/<id>`

Acepta actualizacion parcial:

```json
{
  "status": "IN_PROGRESS",
  "service_label": "EXPRESS"
}
```

### `POST /garment_types`

Objeto esperado:

```json
{
  "name": "Camisas",
  "icon": "shirt",
  "is_frequent": true
}
```

## Objetos esperados en v2

## 1. Catalogo de tipos de prenda

### `GET /v2/garment_types`

Devuelve una lista como esta:

```json
[
  {
    "id": 1,
    "name": "Camisas",
    "icon": "shirt",
    "is_frequent": true,
    "category": "CLOTHING",
    "active": true,
    "default_unit_type": "UNIT",
    "default_unit_price": null,
    "display_order": 1,
    "created_at": "2026-03-20T18:00:00-06:00",
    "updated_at": "2026-03-20T18:00:00-06:00"
  }
]
```

### `POST /v2/garment_types`

Objeto esperado:

```json
{
  "name": "Zapatos",
  "icon": "shoe",
  "is_frequent": true,
  "category": "FOOTWEAR",
  "active": true,
  "default_unit_type": "UNIT",
  "default_unit_price": 4.5,
  "display_order": 104
}
```

Valores validos:

- `category`: `CLOTHING`, `BEDDING`, `FOOTWEAR`, `PLUSH`, `RUG`, `HOUSEHOLD`
- `default_unit_type`: `UNIT`, `PAIR`

### `PUT /v2/garment_types/<id>`

Actualizacion parcial:

```json
{
  "default_unit_price": 5.0,
  "active": false
}
```

## 2. Catalogo de extras

### `GET /v2/service_extra_types`

Devuelve una lista como esta:

```json
[
  {
    "id": 1,
    "code": "IRONING",
    "name": "Planchado",
    "unit_label": "prenda",
    "default_unit_price": null,
    "active": true,
    "display_order": 1,
    "created_at": "2026-03-20T18:00:00-06:00",
    "updated_at": "2026-03-20T18:00:00-06:00"
  }
]
```

### `POST /v2/service_extra_types`

Objeto esperado:

```json
{
  "code": "SOFTENER",
  "name": "Suavizante",
  "unit_label": "unidad",
  "default_unit_price": 0.5,
  "active": true,
  "display_order": 10
}
```

### `PUT /v2/service_extra_types/<id>`

Actualizacion parcial:

```json
{
  "default_unit_price": 1.25,
  "active": true
}
```

## 3. Servicios de lavanderia en v2

En `v2`, el servicio principal puede incluir:

- datos generales del servicio
- peso en libras
- notas generales
- `items`: prendas o articulos recibidos
- `extras`: extras aplicados al servicio

### `POST /v2/laundry_services`

Objeto esperado:

```json
{
  "client_id": 5,
  "client_address_id": 4,
  "scheduled_pickup_at": "2026-03-21T10:30:00",
  "status": "PENDING",
  "service_label": "NORMAL",
  "transaction_id": null,
  "weight_lb": 18.5,
  "notes": "Cliente solicita cuidado especial con prendas blancas.",
  "items": [
    {
      "garment_type_id": 2,
      "quantity": 12,
      "unit_type": "UNIT",
      "unit_price": 0.25,
      "notes": "Pantalones variados"
    },
    {
      "garment_type_id": 1,
      "quantity": 20,
      "unit_type": "UNIT",
      "unit_price": 0.2,
      "notes": "Camisas de vestir"
    },
    {
      "garment_type_id": 9,
      "quantity": 2,
      "unit_type": "PAIR",
      "unit_price": 0.15,
      "notes": "Calcetines por pares"
    },
    {
      "garment_type_id": 18,
      "quantity": 3,
      "unit_type": "UNIT",
      "unit_price": 5.0,
      "notes": "Edredones grandes"
    }
  ],
  "extras": [
    {
      "service_extra_type_id": 1,
      "quantity": 8,
      "unit_price": 0.35,
      "notes": "Planchado de 8 prendas"
    },
    {
      "service_extra_type_id": 2,
      "quantity": 2,
      "unit_price": 0.5,
      "notes": "Perlitas de olor"
    },
    {
      "service_extra_type_id": 4,
      "quantity": 1,
      "unit_price": 0.25,
      "notes": "Aplicacion de vinagre"
    }
  ]
}
```

Campos principales:

- `client_id`: entero
- `client_address_id`: entero y debe pertenecer al cliente
- `scheduled_pickup_at`: fecha ISO
- `status`: `PENDING`, `STARTED`, `IN_PROGRESS`, `READY_FOR_DELIVERY`, `DELIVERED`, `CANCELLED`
- `service_label`: `NORMAL` o `EXPRESS`
- `transaction_id`: entero o `null`
- `weight_lb`: numero o `null`
- `notes`: texto o `null`
- `items`: lista opcional
- `extras`: lista opcional

### Objeto de cada item en `items`

```json
{
  "garment_type_id": 2,
  "quantity": 12,
  "unit_type": "UNIT",
  "unit_price": 0.25,
  "notes": "Pantalones variados"
}
```

Valores validos:

- `unit_type`: `UNIT`, `PAIR`

### Objeto de cada extra en `extras`

```json
{
  "service_extra_type_id": 1,
  "quantity": 8,
  "unit_price": 0.35,
  "notes": "Planchado de 8 prendas"
}
```

### `PUT /v2/laundry_services/<id>`

Acepta actualizacion parcial. Si envias `items` o `extras`, la lista enviada reemplaza la lista actual de ese servicio.

Ejemplo:

```json
{
  "status": "IN_PROGRESS",
  "weight_lb": 20.25,
  "notes": "Se inicio el proceso de lavado.",
  "items": [
    {
      "garment_type_id": 2,
      "quantity": 14,
      "unit_type": "UNIT",
      "unit_price": 0.25,
      "notes": "Se agregaron 2 pantalones"
    }
  ],
  "extras": [
    {
      "service_extra_type_id": 3,
      "quantity": 1,
      "unit_price": 1.0,
      "notes": "Remojo aplicado"
    }
  ]
}
```

### `GET /v2/laundry_services`

Devuelve una lista paginada:

```json
{
  "items": [
    {
      "id": 63,
      "client_id": 5,
      "client_address_id": 4,
      "scheduled_pickup_at": "2026-03-21T10:30:00-06:00",
      "pending_order": 1,
      "status": "PENDING",
      "service_label": "NORMAL",
      "transaction_id": null,
      "weight_lb": 18.5,
      "notes": "Cliente solicita cuidado especial con prendas blancas.",
      "created_by_user_id": 1,
      "created_at": "2026-03-21T10:35:00-06:00",
      "updated_at": "2026-03-21T10:35:00-06:00",
      "client": {
        "id": 5,
        "name": "Andrea Urbina"
      },
      "client_address": {
        "id": 4,
        "client_id": 5,
        "address_text": "Sierra 2"
      },
      "transaction": null,
      "created_by_user": {
        "id": 1,
        "name": "John"
      },
      "logs": [],
      "items": [],
      "extras": [],
      "items_total": 0.0,
      "extras_total": 0.0,
      "grand_total": 0.0
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

Filtros soportados:

- `client_id`
- `status`
- `page`
- `per_page`

Ejemplo:

```http
GET /v2/laundry_services?client_id=5&status=PENDING&page=1&per_page=10
```

### `GET /v2/laundry_services/<id>`

Devuelve el servicio completo con:

- datos base
- cliente
- direccion
- transaccion
- usuario creador
- logs
- items
- extras
- totales calculados

### `DELETE /v2/laundry_services/<id>`

Elimina el servicio y por cascada elimina:

- `laundry_service_items`
- `laundry_service_extras`

## Recomendacion para frontend

- Si el frontend actual depende de la estructura vieja, sigue usando `v1`.
- Si el frontend nuevo va a capturar prendas, extras y peso del servicio, usa `v2`.
- Para migracion gradual, puedes mantener consultas simples en `v1` y comenzar formularios nuevos en `v2`.

## Notas importantes

- `v1` y `v2` comparten autenticacion JWT.
- `v2` no reemplaza automaticamente `v1`; ambas conviven.
- La tabla legacy `laundry_items` no es parte del nuevo flujo `v2`.
- En `PUT /v2/laundry_services/<id>`, enviar `items` o `extras` implica reemplazar el contenido actual de esas listas.
