# Angular Frontend Commercial Drafts

Guia para persistir la captura comercial editable de lavanderia sin obligar al frontend a crear inmediatamente un `laundry_service` final o una `order`.

## Objetivo

Persistir casi todo el payload de UI como un documento editable.

Esto permite:

- guardar cotizaciones intermedias
- reabrirlas despues
- editarlas muchas veces
- agregar o quitar datos
- convertirlas luego a entidades finales

## Endpoint

Base URL:

- `GET /v2/laundry-service-commercial-drafts`
- `GET /v2/laundry-service-commercial-drafts/:id`
- `POST /v2/laundry-service-commercial-drafts`
- `PATCH /v2/laundry-service-commercial-drafts/:id`
- `DELETE /v2/laundry-service-commercial-drafts/:id`

## Create

`POST /v2/laundry-service-commercial-drafts`

Body:

```json
{
  "payload": {
    "ui_model": {
      "client_id": 60,
      "client_address_id": 44,
      "scheduled_pickup_at": "2026-03-13T12:42:29-06:00",
      "status": "PENDING",
      "service_label": "EXPRESS",
      "transaction_id": null,
      "payment_type_id": null,
      "weight_lb": 40,
      "delivery_zone_id": null,
      "pricing_profile_id": 7,
      "distance_km": 0,
      "delivery_price_per_km": 0.63,
      "delivery_fee_suggested": 0,
      "delivery_fee_final": 0,
      "delivery_fee_override_reason": null,
      "global_discount_amount": 0,
      "global_discount_reason": null,
      "notes": null,
      "items": [],
      "extras": [],
      "weight_pricing_preview": {
        "final_price": "24.98"
      },
      "commercial_capture_pending": []
    },
    "laundry_service_payload": {
      "client_id": 60,
      "client_address_id": 44,
      "scheduled_pickup_at": "2026-03-13T12:42:29-06:00",
      "status": "PENDING",
      "service_label": "EXPRESS",
      "transaction_id": null,
      "weight_lb": 40,
      "notes": null,
      "items": [],
      "extras": []
    },
    "order_payload": null,
    "validations": {
      "laundry_service": [],
      "order": []
    }
  },
  "laundry_service_id": null,
  "is_confirmed": false,
  "confirmed_at": null,
  "charged_by_user_id": null
}
```

## Que guarda backend

Backend guarda dos cosas:

- el payload completo en `payload`
- columnas utiles derivadas del `ui_model` para filtros y reportes rapidos

Ejemplos de columnas derivadas:

- `client_id`
- `client_address_id`
- `pricing_profile_id`
- `payment_type_id`
- `weight_lb`
- `distance_km`
- `delivery_fee_final`
- `quoted_service_amount`

## Recomendacion para Angular

Usar esta entidad como fuente principal de guardado automatico de la pantalla editable.

Flujo recomendado:

1. el usuario edita la pantalla
2. Angular construye `ui_model`
3. Angular construye payloads derivados si quiere
4. Angular guarda todo en `payload`
5. despues, en otra accion separada, convierte el draft a `laundry_service` o a `order`

## Nota

No es necesario que el draft ya tenga `payment_type_id`, `order_payload` o confirmacion final.

La tabla existe precisamente para guardar estados intermedios e incompletos.
