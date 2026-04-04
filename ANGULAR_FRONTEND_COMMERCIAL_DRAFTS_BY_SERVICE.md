# Angular Frontend Commercial Drafts By Service

Guia para frontend Angular sobre el nuevo flujo del draft comercial editable.

## Cambio de criterio

El draft comercial ya no debe identificarse por cliente, direccion o estado temporal del frontend.

Ahora el draft pertenece al `laundry_service` en curso.

Regla:

- un `laundry_service_id` tiene un solo draft comercial activo
- varios usuarios pueden editar ese mismo draft en distintos momentos
- frontend no debe guardar identificadores temporales del draft para encontrarlo despues

## Endpoint recomendado

Usar este endpoint como principal:

- `PUT /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id`

Tambien existen:

- `GET /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id`
- `POST /v2/laundry-service-commercial-drafts`
- `PATCH /v2/laundry-service-commercial-drafts/:id`

Pero para el flujo normal se recomienda `PUT by-service` porque crea o actualiza automaticamente el mismo draft del servicio.

## Payload esperado

```json
{
  "payload": {
    "ui_model": {
      "id": 61,
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
        "recommended_price": "24.98",
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
  "is_confirmed": false,
  "confirmed_at": null,
  "charged_by_user_id": null
}
```

## Como debe trabajar Angular

### 1. El `laundry_service_id` es obligatorio

Frontend debe esperar tener el `laundry_service_id` real del servicio en curso para guardar o recuperar el draft comercial.

No usar como criterio:

- `client_id`
- `client_address_id`
- `status`
- `draft` local en memoria

### 2. Flujo recomendado

1. crear o abrir `laundry_service`
2. tomar `laundry_service_id`
3. cargar draft con:

```http
GET /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id
```

4. si usuario edita, guardar con:

```http
PUT /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id
```

### 3. Guardado automatico

Cada autosave o guardado manual debe mandar todo el `payload` completo actual de la pantalla.

No es necesario que el draft ya tenga:

- `payment_type_id`
- `order_payload`
- confirmacion final

## Campos que backend indexa ademas del payload

Aunque frontend manda el payload completo, backend extrae y guarda columnas utiles como:

- `client_id`
- `client_address_id`
- `transaction_id`
- `payment_type_id`
- `pricing_profile_id`
- `weight_lb`
- `distance_km`
- `delivery_fee_suggested`
- `delivery_fee_final`
- `quoted_service_amount`

## Cambio importante para frontend

Antes:

- el draft podia recuperarse por cliente o por heuristica

Ahora:

- el draft debe recuperarse y guardarse por `laundry_service_id`

Ese es el identificador estable que comparten distintos usuarios a lo largo del dia.
