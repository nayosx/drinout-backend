# API V2 Frontend Contract

Guia practica para frontend sobre la forma real de las respuestas de la API `v2`.

Este documento esta pensado para evitar errores de integracion por asumir una estructura distinta a la que realmente devuelve el backend.

## Base URL

- Desarrollo local: `http://192.168.1.135:5050`
- Prefijo V2: `http://192.168.1.135:5050/v2`

## Autenticacion

Todos los endpoints de `v2` requieren JWT en header:

```http
Authorization: Bearer <token>
```

Si falta el token o es invalido, lo mas comun es recibir:

```json
{
  "msg": "Missing Authorization Header"
}
```

o:

```json
{
  "msg": "Token has expired"
}
```

Status habitual: `401`.

## Regla Mas Importante Para Frontend

La API v2 no usa una unica forma de respuesta.

Hay 4 patrones principales:

1. Listados simples: devuelven un `array`.
2. Listados paginados: devuelven un `object` con `items`, `total`, `page`, `per_page`, `pages`.
3. `POST` y `PATCH` de catalogos: devuelven `message` + objeto creado/actualizado.
4. `POST` y `PATCH` de entidades complejas como `orders` y `laundry_services`: devuelven directamente el objeto completo, sin wrapper `message`.

## Convenciones Reales Del Backend

- Los nombres vienen en `snake_case`, no en `camelCase`.
- Muchos montos vienen como string decimal, por ejemplo `"15.00"`.
- Los `DateTime` salen como string ISO.
- Algunos `404` y `500` pueden llegar como HTML si vienen de `get_or_404()` / `first_or_404()` o de un error no controlado.
- Los errores de validacion controlados suelen venir como:

```json
{
  "error": "mensaje"
}
```

- En varios endpoints con Marshmallow, el contenido de `error` puede ser un string con un diccionario serializado, por ejemplo:

```json
{
  "error": "{'category_id': ['Missing data for required field.']}"
}
```

Frontend no debe asumir que `error` siempre es un texto simple de una sola frase.

## Resumen De Formas De Respuesta

### 1. Listados simples

Ejemplo real:

```json
[
  {
    "id": 1,
    "code": "HOUSEHOLD_BULKY",
    "name": "Hogar y volumen",
    "description": "Servicios especiales para piezas grandes del hogar",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41"
  }
]
```

### 2. Listados paginados

Ejemplo real de forma:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "per_page": 10,
  "pages": 0
}
```

### 3. Create / update con wrapper

Ejemplo:

```json
{
  "message": "Service category created",
  "service_category": {
    "id": 6,
    "code": "NEW_CAT",
    "name": "Nueva categoria",
    "description": null,
    "sort_order": 6,
    "is_active": true,
    "created_at": "2026-03-28T15:40:00",
    "updated_at": "2026-03-28T15:40:00"
  }
}
```

### 4. Create / update sin wrapper

Ejemplo de `POST /v2/orders` y `PATCH /v2/orders/:id`:

```json
{
  "id": 1,
  "client_id": 3,
  "client_address_id": 2,
  "pricing_profile_id": 1,
  "payment_type_id": 4,
  "delivery_zone_id": null,
  "delivery_zone_price_id": null,
  "status": "CONFIRMED",
  "service_subtotal": "9.99",
  "extras_subtotal": "1.00",
  "delivery_fee_suggested": "0.00",
  "delivery_fee_final": "0.00",
  "delivery_fee_override_by_user_id": null,
  "delivery_fee_override_reason": null,
  "global_discount_amount": "0.00",
  "global_discount_reason": null,
  "subtotal_before_payment_surcharge": "10.99",
  "payment_type_name_snapshot": "Tarjeta",
  "payment_surcharge_type_snapshot": "PERCENT",
  "payment_surcharge_value_snapshot": "5.6500",
  "payment_surcharge_amount": "0.62",
  "total_amount": "11.61",
  "notes": "Orden creada desde frontend",
  "charged_by_user_id": 6,
  "created_by_user_id": 6,
  "updated_by_user_id": 6,
  "created_at": "2026-03-28T15:45:00",
  "updated_at": "2026-03-28T15:45:00",
  "items": [],
  "extra_items": []
}
```

## Endpoints V2

### 1. `/v2/service-categories`

#### GET `/v2/service-categories`

Devuelve `array`.

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "code": "HOUSEHOLD_BULKY",
    "name": "Hogar y volumen",
    "description": "Servicios especiales para piezas grandes del hogar",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41"
  },
  {
    "id": 2,
    "code": "FORMAL_WEAR",
    "name": "Ropa formal",
    "description": "Servicios para traje, vestidos y prendas delicadas formales",
    "sort_order": 2,
    "is_active": true,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41"
  }
]
```

Ejemplo no exitoso:

```json
{
  "msg": "Missing Authorization Header"
}
```

#### GET `/v2/service-categories/:id`

Devuelve un objeto.

Ejemplo exitoso:

```json
{
  "id": 1,
  "code": "HOUSEHOLD_BULKY",
  "name": "Hogar y volumen",
  "description": "Servicios especiales para piezas grandes del hogar",
  "sort_order": 1,
  "is_active": true,
  "created_at": "2026-03-28T15:22:41",
  "updated_at": "2026-03-28T15:22:41"
}
```

Ejemplo no exitoso:

- `404` puede venir como HTML si el id no existe.

#### POST `/v2/service-categories`

Body ejemplo:

```json
{
  "code": "DRY_ONLY",
  "name": "Solo seco",
  "description": "Servicios de lavado en seco",
  "sort_order": 6,
  "is_active": true
}
```

Respuesta exitosa:

```json
{
  "message": "Service category created",
  "service_category": {
    "id": 6,
    "code": "DRY_ONLY",
    "name": "Solo seco",
    "description": "Servicios de lavado en seco",
    "sort_order": 6,
    "is_active": true,
    "created_at": "2026-03-28T15:40:00",
    "updated_at": "2026-03-28T15:40:00"
  }
}
```

Respuesta no exitosa:

```json
{
  "error": "No input data provided"
}
```

o:

```json
{
  "error": "{'name': ['Missing data for required field.']}"
}
```

#### PATCH `/v2/service-categories/:id`

Respuesta exitosa:

```json
{
  "message": "Service category updated",
  "service_category": {
    "id": 1,
    "code": "HOUSEHOLD_BULKY",
    "name": "Hogar y volumen",
    "description": "Actualizada",
    "sort_order": 1,
    "is_active": true,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:50:00"
  }
}
```

### 2. `/v2/services`

#### GET `/v2/services`

Devuelve `array`, no paginacion.

Filtros:

- `category_id`
- `pricing_mode`
- `is_active`

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "category_id": 1,
    "code": "ALFOMBRAS",
    "name": "Alfombras",
    "pricing_mode": "FIXED",
    "unit_label": "pieza",
    "description": null,
    "is_active": true,
    "allow_manual_price_override": true,
    "allow_item_discount": true,
    "sort_order": 1,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41",
    "category": {
      "id": 1,
      "code": "HOUSEHOLD_BULKY",
      "name": "Hogar y volumen",
      "description": "Servicios especiales para piezas grandes del hogar",
      "sort_order": 1,
      "is_active": true,
      "created_at": "2026-03-28T15:22:41",
      "updated_at": "2026-03-28T15:22:41"
    },
    "price_options": [
      {
        "id": 1,
        "service_id": 1,
        "label": "Precio 1",
        "suggested_price": "2.00",
        "sort_order": 1,
        "is_active": true,
        "notes": null,
        "created_at": "2026-03-28T15:22:41",
        "updated_at": "2026-03-28T15:22:41"
      }
    ]
  }
]
```

#### POST `/v2/services`

Respuesta exitosa:

```json
{
  "message": "Service created",
  "service": {
    "id": 29,
    "category_id": 1,
    "code": "NUEVO_SERVICIO",
    "name": "Nuevo servicio",
    "pricing_mode": "FIXED",
    "unit_label": "pieza",
    "description": null,
    "is_active": true,
    "allow_manual_price_override": true,
    "allow_item_discount": true,
    "sort_order": 99,
    "created_at": "2026-03-28T15:55:00",
    "updated_at": "2026-03-28T15:55:00",
    "category": null,
    "price_options": []
  }
}
```

No exitoso:

```json
{
  "error": "Category not found"
}
```

### 3. `/v2/service-price-options`

#### GET `/v2/service-price-options`

Devuelve `array`.

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "service_id": 1,
    "label": "Precio 1",
    "suggested_price": "2.00",
    "sort_order": 1,
    "is_active": true,
    "notes": null,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41"
  }
]
```

#### POST `/v2/service-price-options`

Respuesta exitosa:

```json
{
  "message": "Service price option created",
  "service_price_option": {
    "id": 65,
    "service_id": 1,
    "label": "Precio especial",
    "suggested_price": "12.50",
    "sort_order": 6,
    "is_active": true,
    "notes": null,
    "created_at": "2026-03-28T16:00:00",
    "updated_at": "2026-03-28T16:00:00"
  }
}
```

No exitoso:

```json
{
  "error": "Service not found"
}
```

### 4. `/v2/extras`

#### GET `/v2/extras`

Devuelve `array`.

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "code": "REMOJO",
    "name": "Remojo",
    "unit_label": "unidad",
    "suggested_unit_price": "1.00",
    "is_active": true,
    "sort_order": 1,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41"
  }
]
```

#### POST `/v2/extras`

Respuesta exitosa:

```json
{
  "message": "Extra created",
  "extra": {
    "id": 6,
    "code": "AMBIENTADOR",
    "name": "Ambientador",
    "unit_label": "unidad",
    "suggested_unit_price": "1.50",
    "is_active": true,
    "sort_order": 6,
    "created_at": "2026-03-28T16:05:00",
    "updated_at": "2026-03-28T16:05:00"
  }
}
```

### 5. `/v2/delivery-zones`

#### GET `/v2/delivery-zones`

Devuelve `array`.

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "code": "CENTRO",
    "name": "Centro",
    "description": "Zona centro",
    "is_active": true,
    "created_at": "2026-03-28T16:10:00",
    "updated_at": "2026-03-28T16:10:00",
    "prices": [
      {
        "id": 1,
        "delivery_zone_id": 1,
        "fee_amount": "2.50",
        "is_active": true,
        "effective_from": "2026-03-28T16:10:00",
        "effective_to": null,
        "created_at": "2026-03-28T16:10:00",
        "updated_at": "2026-03-28T16:10:00"
      }
    ]
  }
]
```

#### POST `/v2/delivery-zones`

Body ejemplo:

```json
{
  "code": "CENTRO",
  "name": "Centro",
  "description": "Zona centro",
  "is_active": true,
  "current_fee": "2.50"
}
```

Respuesta exitosa:

```json
{
  "message": "Delivery zone created",
  "delivery_zone": {
    "id": 1,
    "code": "CENTRO",
    "name": "Centro",
    "description": "Zona centro",
    "is_active": true,
    "created_at": "2026-03-28T16:10:00",
    "updated_at": "2026-03-28T16:10:00",
    "prices": [
      {
        "id": 1,
        "delivery_zone_id": 1,
        "fee_amount": "2.50",
        "is_active": true,
        "effective_from": "2026-03-28T16:10:00",
        "effective_to": null,
        "created_at": "2026-03-28T16:10:00",
        "updated_at": "2026-03-28T16:10:00"
      }
    ]
  }
}
```

#### POST `/v2/delivery-zones/:id/prices`

Respuesta exitosa:

```json
{
  "message": "Delivery zone price created",
  "delivery_zone_price": {
    "id": 2,
    "delivery_zone_id": 1,
    "fee_amount": "3.00",
    "is_active": true,
    "effective_from": "2026-03-29T00:00:00",
    "effective_to": null,
    "created_at": "2026-03-28T16:12:00",
    "updated_at": "2026-03-28T16:12:00"
  }
}
```

### 6. `/v2/weight-pricing`

#### GET `/v2/weight-pricing/profiles`

Devuelve `array`.

Ejemplo exitoso:

```json
[
  {
    "id": 1,
    "name": "Perfil Principal MAX_REVENUE",
    "is_active": true,
    "strategy": "MAX_REVENUE",
    "extra_lb_price": "0.90",
    "auto_upgrade_enabled": false,
    "auto_upgrade_margin": "0.00",
    "force_upgrade_from_lb": null,
    "compare_all_tiers": true,
    "round_mode": "exact",
    "allow_manual_override": true,
    "notes": null,
    "created_at": "2026-03-28T15:22:41",
    "updated_at": "2026-03-28T15:22:41",
    "tiers": [
      {
        "id": 1,
        "profile_id": 1,
        "max_weight_lb": "15.00",
        "price": "9.99",
        "sort_order": 1,
        "is_active": true,
        "created_at": "2026-03-28T15:22:41",
        "updated_at": "2026-03-28T15:22:41"
      }
    ]
  },
  {
    "id": 2,
    "name": "Perfil BEST_TIER_FIT",
    "is_active": true,
    "strategy": "BEST_TIER_FIT",
    "extra_lb_price": "0.90",
    "auto_upgrade_enabled": false,
    "auto_upgrade_margin": "0.00",
    "force_upgrade_from_lb": null,
    "compare_all_tiers": false,
    "round_mode": "exact",
    "allow_manual_override": true,
    "notes": "Perfil para elegir el tier minimo que cubre el peso sin usar extras",
    "created_at": "2026-03-28T16:30:00",
    "updated_at": "2026-03-28T16:30:00",
    "tiers": [
      {
        "id": 3,
        "profile_id": 2,
        "max_weight_lb": "15.00",
        "price": "9.99",
        "sort_order": 1,
        "is_active": true,
        "created_at": "2026-03-28T16:30:00",
        "updated_at": "2026-03-28T16:30:00"
      },
      {
        "id": 4,
        "profile_id": 2,
        "max_weight_lb": "25.00",
        "price": "14.99",
        "sort_order": 2,
        "is_active": true,
        "created_at": "2026-03-28T16:30:00",
        "updated_at": "2026-03-28T16:30:00"
      }
    ]
  }
]
```

Perfiles actuales sembrados en base:

- `Perfil Principal MAX_REVENUE`
- `Perfil BEST_TIER_FIT`
- `Perfil BASE_PLUS_EXTRA`
- `Perfil CUSTOMER_BEST_PRICE`
- `Perfil PROMOTIONAL_UPGRADE`
- `Perfil FORCE_UPGRADE_FROM_WEIGHT`

#### GET `/v2/weight-pricing/tiers`

Devuelve `array`.

#### POST `/v2/weight-pricing/profiles`

Respuesta exitosa:

```json
{
  "message": "Weight pricing profile created",
  "weight_pricing_profile": {
    "id": 2,
    "name": "Perfil Secundario",
    "is_active": true,
    "strategy": "MAX_REVENUE",
    "extra_lb_price": "0.90",
    "auto_upgrade_enabled": false,
    "auto_upgrade_margin": "0.00",
    "force_upgrade_from_lb": null,
    "compare_all_tiers": true,
    "round_mode": "exact",
    "allow_manual_override": true,
    "notes": null,
    "created_at": "2026-03-28T16:15:00",
    "updated_at": "2026-03-28T16:15:00",
    "tiers": []
  }
}
```

#### POST `/v2/weight-pricing/tiers`

No exitoso:

```json
{
  "error": "Weight pricing profile not found"
}
```

#### POST `/v2/weight-pricing/quote`

Body ejemplo:

```json
{
  "weight_lb": "22.00",
  "profile_id": 1
}
```

Respuesta exitosa aproximada:

```json
{
  "profile_id": 1,
  "profile_name": "Perfil Principal MAX_REVENUE",
  "weight_lb": "22.00",
  "strategy_selected": "MAX_REVENUE",
  "recommended_price": "16.29",
  "selected_price": "16.29",
  "selected_tier_id": 2,
  "selected_tier_max_weight_lb": "25.00",
  "selected_base_price": "14.99",
  "selected_option_type": "BASE_PLUS_EXTRA",
  "allow_manual_override": true,
  "decision_reason": "Perfil 'Perfil Principal MAX_REVENUE' con estrategia MAX_REVENUE para peso 22.00 lb. Se evaluaron alternativas y se eligio la de mayor total valido.",
  "lowest_valid_price": "14.99",
  "highest_valid_price": "16.29",
  "difference_selected_vs_lowest": "1.30",
  "difference_selected_vs_highest": "0.00",
  "evaluated_options_count": 4,
  "options_evaluated": [
    {
      "option_type": "BEST_TIER_FIT",
      "tier_id": 2,
      "tier_max_weight_lb": "25.00",
      "tier_price": "14.99",
      "extra_lb": "0.00",
      "extra_charge": "0.00",
      "total_price": "14.99",
      "reason": "Tier 25.00 lb cubre el peso 22.00 lb con precio fijo 14.99.",
      "selected": false
    },
    {
      "option_type": "BASE_PLUS_EXTRA",
      "tier_id": 1,
      "tier_max_weight_lb": "15.00",
      "tier_price": "9.99",
      "extra_lb": "7.00",
      "extra_charge": "6.30",
      "total_price": "16.29",
      "reason": "Base 15.00 lb con 7.00 lb extra a 0.90 da total 16.29.",
      "selected": true
    }
  ]
}
```

Frontend debe usar `decision_reason` para mostrar al operador por que se eligio una alternativa.

No exitoso:

```json
{
  "error": "weight_lb is required"
}
```

### 7. `/payment_types`

Estos endpoints no llevan prefijo `/v2`.

#### GET `/payment_types`

Devuelve `array`.

Query param opcional:

- `is_active=true|false`

Ejemplo exitoso:

```json
[
  {
    "id": 3,
    "code": "TARJETA_DE_CREDITO",
    "name": "Tarjeta",
    "description": "Pago con tarjeta",
    "surcharge_type": "PERCENT",
    "surcharge_value": "5.6500",
    "is_active": true,
    "sort_order": 1,
    "created_at": "2026-03-28T10:30:00",
    "updated_at": "2026-03-28T10:30:00"
  },
  {
    "id": 2,
    "code": "TRANSFERENCIA",
    "name": "Transferencias",
    "description": "Pago por transferencia bancaria",
    "surcharge_type": "PERCENT",
    "surcharge_value": "0.0000",
    "is_active": true,
    "sort_order": 2,
    "created_at": "2026-03-28T10:30:00",
    "updated_at": "2026-03-28T10:30:00"
  },
  {
    "id": 1,
    "code": "EFECTIVO",
    "name": "Efectivo",
    "description": "Pago en efectivo",
    "surcharge_type": "PERCENT",
    "surcharge_value": "0.0000",
    "is_active": true,
    "sort_order": 3,
    "created_at": "2026-03-28T10:30:00",
    "updated_at": "2026-03-28T10:30:00"
  }
]
```

#### POST `/payment_types`

Body ejemplo:

```json
{
  "code": "TARJETA_DE_CREDITO",
  "name": "Tarjeta",
  "description": "Pago con tarjeta",
  "surcharge_type": "PERCENT",
  "surcharge_value": "5.6500",
  "is_active": true,
  "sort_order": 1
}
```

Respuesta exitosa:

```json
{
  "message": "Payment type created",
  "payment_type": {
    "id": 3,
    "code": "TARJETA_DE_CREDITO",
    "name": "Tarjeta",
    "description": "Pago con tarjeta",
    "surcharge_type": "PERCENT",
    "surcharge_value": "5.6500",
    "is_active": true,
    "sort_order": 1,
    "created_at": "2026-03-28T10:30:00",
    "updated_at": "2026-03-28T10:30:00"
  }
}
```

### 8. `/v2/orders`

#### GET `/v2/orders`

Devuelve objeto paginado, no array.

Frontend debe leer `response.items`.

Ejemplo exitoso:

```json
{
  "items": [
    {
      "id": 1,
      "client_id": 3,
      "client_address_id": 2,
      "pricing_profile_id": 1,
      "payment_type_id": 3,
      "delivery_zone_id": null,
      "delivery_zone_price_id": null,
      "status": "CONFIRMED",
      "service_subtotal": "9.99",
      "extras_subtotal": "1.00",
      "delivery_fee_suggested": "0.00",
      "delivery_fee_final": "0.00",
      "delivery_fee_override_by_user_id": null,
      "delivery_fee_override_reason": null,
      "global_discount_amount": "0.00",
      "global_discount_reason": null,
      "subtotal_before_payment_surcharge": "10.99",
      "payment_type_name_snapshot": "Tarjeta",
      "payment_surcharge_type_snapshot": "PERCENT",
      "payment_surcharge_value_snapshot": "5.6500",
      "payment_surcharge_amount": "0.62",
      "total_amount": "11.61",
      "notes": "Orden de ejemplo",
      "charged_by_user_id": 6,
      "created_by_user_id": 6,
      "updated_by_user_id": 6,
      "created_at": "2026-03-28T16:20:00",
      "updated_at": "2026-03-28T16:20:00",
      "items": [],
      "extra_items": []
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

#### GET `/v2/orders/:id`

Devuelve un objeto.

#### POST `/v2/orders`

Body ejemplo:

```json
{
  "client_id": 3,
  "client_address_id": 2,
  "pricing_profile_id": 1,
  "payment_type_id": 3,
  "status": "CONFIRMED",
  "global_discount_amount": "0.00",
  "notes": "Orden creada desde Angular",
  "items": [
    {
      "service_id": 10,
      "suggested_price_option_id": 21,
      "quantity": "1.00",
      "discount_amount": "0.00"
    }
  ],
  "extras": [
    {
      "extra_id": 1,
      "quantity": "1.00",
      "discount_amount": "0.00"
    }
  ]
}
```

Respuesta exitosa:

```json
{
  "id": 1,
  "client_id": 3,
  "client_address_id": 2,
  "pricing_profile_id": 1,
  "payment_type_id": 3,
  "delivery_zone_id": null,
  "delivery_zone_price_id": null,
  "status": "CONFIRMED",
  "service_subtotal": "9.99",
  "extras_subtotal": "1.00",
  "delivery_fee_suggested": "0.00",
  "delivery_fee_final": "0.00",
  "delivery_fee_override_by_user_id": null,
  "delivery_fee_override_reason": null,
  "global_discount_amount": "0.00",
  "global_discount_reason": null,
  "subtotal_before_payment_surcharge": "10.99",
  "payment_type_name_snapshot": "Tarjeta",
  "payment_surcharge_type_snapshot": "PERCENT",
  "payment_surcharge_value_snapshot": "5.6500",
  "payment_surcharge_amount": "0.62",
  "total_amount": "11.61",
  "notes": "Orden creada desde Angular",
  "charged_by_user_id": 6,
  "created_by_user_id": 6,
  "updated_by_user_id": 6,
  "created_at": "2026-03-28T16:20:00",
  "updated_at": "2026-03-28T16:20:00",
  "items": [
    {
      "id": 1,
      "order_id": 1,
      "service_id": 10,
      "suggested_price_option_id": 21,
      "service_name_snapshot": "Lavado por peso",
      "category_name_snapshot": "Lavado por peso",
      "pricing_mode": "WEIGHT",
      "quantity": "1.00",
      "weight_lb": "10.00",
      "unit_label_snapshot": "servicio",
      "suggested_price_label_snapshot": "Precio 1",
      "suggested_unit_price": "9.99",
      "recommended_unit_price": "9.99",
      "final_unit_price": "9.99",
      "manual_price_override_by_user_id": null,
      "manual_price_override_reason": null,
      "discount_amount": "0.00",
      "subtotal_before_discount": "9.99",
      "subtotal_after_discount": "9.99",
      "notes": null,
      "weight_pricing_snapshot": {
        "id": 1,
        "order_id": 1,
        "order_item_id": 1,
        "pricing_profile_id": 1,
        "pricing_profile_name_snapshot": "Perfil Principal MAX_REVENUE",
        "strategy_applied": "MAX_REVENUE",
        "weight_lb": "10.00",
        "selected_tier_id": 1,
        "selected_tier_max_weight_lb": "15.00",
        "selected_base_price": "9.99",
        "recommended_price": "9.99",
        "final_price": "9.99",
        "override_applied": false,
        "override_by_user_id": null,
        "override_reason": null,
        "allow_manual_override": true,
        "decision_reason": "Perfil 'Perfil Principal MAX_REVENUE' con estrategia MAX_REVENUE para peso 10.00 lb.",
        "options_evaluated_json": "[...]",
        "lowest_valid_price": "9.99",
        "highest_valid_price": "9.99",
        "difference_selected_vs_lowest": "0.00",
        "difference_selected_vs_highest": "0.00",
        "created_at": "2026-03-28T16:20:00"
      }
    }
  ],
  "extra_items": [
    {
      "id": 1,
      "order_id": 1,
      "extra_id": 1,
      "extra_name_snapshot": "Remojo",
      "unit_label_snapshot": "unidad",
      "quantity": "1.00",
      "suggested_unit_price": "1.00",
      "final_unit_price": "1.00",
      "discount_amount": "0.00",
      "subtotal_before_discount": "1.00",
      "subtotal_after_discount": "1.00",
      "notes": null
    }
  ]
}
```

No exitoso:

```json
{
  "error": "Client not found"
}
```

o:

```json
{
  "error": "Address does not belong to client"
}
```

o:

```json
{
  "error": "Service 999 not found"
}
```

o:

```json
{
  "error": "weight_lb is required for service 10"
}
```

o:

```json
{
  "error": "Payment type not found"
}
```

o:

```json
{
  "error": "Payment type is inactive"
}
```

o:

```json
{
  "error": "global_discount_amount cannot exceed order total"
}
```

#### PATCH `/v2/orders/:id`

Respuesta exitosa:

Devuelve el objeto completo actualizado, no `message`.

Frontend debe tratar `payment_type_id` como obligatorio al crear pedido y debe mostrar:

- subtotal antes de recargo
- metodo de pago aplicado
- tipo de recargo
- valor del recargo
- monto final del recargo
- total final

### 9. `/v2/laundry_services`

#### GET `/v2/laundry_services`

Devuelve objeto paginado, igual que `orders`.

Ejemplo exitoso:

```json
{
  "items": [
    {
      "id": 12,
      "client_id": 3,
      "client_address_id": 2,
      "scheduled_pickup_at": "2026-03-28T17:00:00",
      "pending_order": 1,
      "status": "PENDING",
      "service_label": "NORMAL",
      "transaction_id": null,
      "weight_lb": null,
      "notes": "Recoger antes de las 5",
      "created_by_user_id": 6,
      "created_at": "2026-03-28T16:25:00",
      "updated_at": "2026-03-28T16:25:00",
      "client": {
        "id": 3,
        "name": "Cliente Demo"
      },
      "client_address": {
        "id": 2,
        "client_id": 3,
        "address_text": "San Salvador"
      },
      "transaction": null,
      "created_by_user": null,
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

#### POST `/v2/laundry_services`

Respuesta exitosa:

Devuelve el objeto completo creado, sin `message`.

No exitoso:

```json
{
  "error": "Client not found"
}
```

o:

```json
{
  "error": "Address does not belong to client"
}
```

o:

```json
{
  "error": "GarmentType 999 not found"
}
```

o:

```json
{
  "error": "ServiceExtraType 999 not found"
}
```

#### PUT `/v2/laundry_services/:id`

Devuelve el objeto completo actualizado.

#### DELETE `/v2/laundry_services/:id`

Devuelve:

```json
{
  "message": "LaundryService 12 deleted"
}
```

### 10. `/v2/garment_types`

#### GET `/v2/garment_types`

Devuelve `array`.

#### POST `/v2/garment_types`

Devuelve:

```json
{
  "message": "Garment type created",
  "garment_type": {
    "id": 1
  }
}
```

#### PUT `/v2/garment_types/:id`

Devuelve:

```json
{
  "message": "Garment type updated",
  "garment_type": {
    "id": 1
  }
}
```

#### DELETE `/v2/garment_types/:id`

Devuelve:

```json
{
  "message": "Garment type 1 deleted"
}
```

### 11. `/v2/service_extra_types`

#### GET `/v2/service_extra_types`

Devuelve `array`.

#### POST `/v2/service_extra_types`

Devuelve:

```json
{
  "message": "Service extra type created",
  "service_extra_type": {
    "id": 1
  }
}
```

#### PUT `/v2/service_extra_types/:id`

Devuelve:

```json
{
  "message": "Service extra type updated",
  "service_extra_type": {
    "id": 1
  }
}
```

#### DELETE `/v2/service_extra_types/:id`

Devuelve:

```json
{
  "message": "Service extra type 1 deleted"
}
```

## Recomendaciones Para El Frontend

### Al leer listados

- Si el endpoint es `/v2/orders` o `/v2/laundry_services`, leer `response.items`.
- Si el endpoint es `/v2/service-categories`, `/v2/services`, `/v2/service-price-options`, `/v2/extras`, `/v2/delivery-zones`, `/v2/weight-pricing/profiles`, `/v2/weight-pricing/tiers`, `/v2/garment_types`, `/v2/service_extra_types`, `/payment_types`, leer el response completo como `array`.

### Al leer creaciones / actualizaciones

- Catalogos pequenos usan wrapper:
  - `response.service_category`
  - `response.service`
  - `response.service_price_option`
  - `response.extra`
  - `response.delivery_zone`
  - `response.delivery_zone_price`
  - `response.weight_pricing_profile`
  - `response.weight_pricing_tier`
  - `response.payment_type`
  - `response.garment_type`
  - `response.service_extra_type`
- `orders` y `laundry_services` devuelven directamente la entidad completa.

### Al manejar errores

- Si existe `error`, mostrar `response.error`.
- Si existe `msg`, mostrar `response.msg`.
- Si el backend responde HTML en `404/500`, frontend debe usar un fallback generico.

Ejemplo de fallback:

```ts
const message =
  error?.error?.error ||
  error?.error?.msg ||
  error?.message ||
  'Error inesperado';
```

### Al modelar en Angular

No tipar todos los GET como `Observable<T[]>`.

Usar algo parecido a esto:

```ts
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}
```

Y para catalogos:

```ts
this.http.get<ServiceCategory[]>(url)
```

Para `orders`:

```ts
this.http.get<PaginatedResponse<Order>>(url)
```

## Archivo Fuente Del Comportamiento

La fuente real de este contrato esta en:

- [app/modules/laundry/v2/orders/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/orders/routes.py)
- [app/modules/laundry/v2/services/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/services/routes.py)
- [app/modules/laundry/v2/service_categories/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/service_categories/routes.py)
- [app/modules/laundry/v2/services_catalog/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/services_catalog/routes.py)
- [app/modules/laundry/v2/service_price_options/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/service_price_options/routes.py)
- [app/modules/laundry/v2/extras/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/extras/routes.py)
- [app/modules/laundry/v2/delivery_zones/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/delivery_zones/routes.py)
- [app/modules/laundry/v2/weight_pricing/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/weight_pricing/routes.py)
- [app/modules/billing/payment_types/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/billing/payment_types/routes.py)
- [app/modules/laundry/v2/garment_types/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/garment_types/routes.py)
- [app/modules/laundry/v2/service_extra_types/routes.py](/home/ness/Dev/Python/drinout-backend/app/modules/laundry/v2/service_extra_types/routes.py)
