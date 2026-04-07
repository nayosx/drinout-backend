# Angular Frontend Weight Pricing Alignment Prompt

Necesito alinear el frontend Angular con el backend en el flujo de draft comercial de lavanderia.

## Contexto importante

- El backend ya devuelve correctamente el precio recalculado del lavado por peso en el draft comercial.
- La respuesta actual de `GET /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id` trae el valor correcto en:
  - `quoted_service_amount`
  - `payload.ui_model.quoted_service_amount`
  - `payload.ui_model.weight_pricing_preview.final_price`
  - `payload.ui_model.weight_pricing_preview.recommended_price`
- En un caso real, el draft trae:
  - `weight_lb = 5`
  - un item comercial en `payload.ui_model.commercial_capture_pending`
  - y el backend responde correctamente `4.50`
- Pero en la UI todavia se muestra `9.99`, asi que el frontend probablemente esta usando un valor viejo, un calculo local, o un campo incorrecto.

## Lo que necesito que revises

1. Donde se carga la respuesta de `GET /v2/laundry-service-commercial-drafts/by-service/:id`
2. Donde se mapea esa respuesta al estado, formulario o view model
3. Que campo usa actualmente la UI para mostrar el precio del lavado por peso
4. Si existe logica local que recalcula el precio y pisa el valor que viene del backend
5. Si existe caching, `patchValue` parcial, merge incorrecto o estado derivado que este dejando el valor viejo
6. Que cambios hay que hacer para que la UI use el valor correcto devuelto por backend

## Regla funcional esperada

- La fuente de verdad del precio mostrado debe venir del backend
- Para el draft comercial, el frontend debe usar como referencia principal:
  - `response.payload.ui_model.weight_pricing_preview.final_price`
- Como respaldo, puede usar:
  - `response.payload.ui_model.quoted_service_amount`
  - `response.quoted_service_amount`
- El frontend no debe recalcular localmente este precio si el backend ya lo devolvio

## Quiero que me devuelvas

- archivo(s) exacto(s) donde esta el problema
- explicacion concreta de por que hoy se muestra `9.99`
- cambio recomendado
- snippet o patch sugerido en Angular
- si aplica, orden de prioridad de campos para poblar el precio mostrado

## Ejemplo de respuesta real del backend

```json
{
  "charged_by_user_id": null,
  "client_address_id": 11,
  "client_id": 2,
  "confirmed_at": null,
  "created_at": "2026-04-05T15:59:54-06:00",
  "created_by_user_id": 6,
  "delivery_fee_final": "0.00",
  "delivery_fee_override_reason": null,
  "delivery_fee_suggested": "0.00",
  "delivery_price_per_km": "0.63",
  "distance_km": "0.00",
  "global_discount_amount": "0.00",
  "global_discount_reason": null,
  "id": 9,
  "is_confirmed": false,
  "laundry_service_id": 67,
  "notes": null,
  "payload": {
    "laundry_service_payload": {
      "client_address_id": 11,
      "client_id": 2,
      "extras": [],
      "items": [],
      "notes": null,
      "scheduled_pickup_at": "2026-04-03T21:59:28-06:00",
      "service_label": "NORMAL",
      "status": "PENDING",
      "transaction_id": null,
      "weight_lb": 5
    },
    "order_payload": null,
    "ui_model": {
      "client_address_id": 11,
      "client_id": 2,
      "commercial_capture_pending": [
        {
          "category_name": "Planchado",
          "manual_price": 1.1,
          "notes": null,
          "quantity": 5,
          "selected_price_option_id": 63,
          "service_id": 27,
          "service_name": "Planchado de ropa"
        }
      ],
      "delivery_fee_final": 0,
      "delivery_fee_override_reason": null,
      "delivery_fee_suggested": 0,
      "delivery_price_per_km": 0.63,
      "delivery_zone_id": null,
      "distance_km": 0,
      "express_service_surcharge": 5,
      "extras": [],
      "global_discount_amount": 0,
      "global_discount_reason": null,
      "id": 67,
      "items": [],
      "notes": null,
      "payment_type_id": null,
      "pricing_profile_id": 7,
      "quoted_service_amount": "4.50",
      "scheduled_pickup_at": "2026-04-03T21:59:28-06:00",
      "service_label": "NORMAL",
      "status": "PENDING",
      "transaction_id": null,
      "weight_lb": 5,
      "weight_pricing_preview": {
        "allow_manual_override": true,
        "business_reason": "Perfil 'Perfil PACKAGE_BLOCKS' con estrategia PACKAGE_BLOCKS para peso 5.00 lb. Se evaluaron 1 alternativas: PACKAGE_BLOCKS_SMALL_WEIGHT_BY_LB=4.50. La alternativa seleccionada fue PACKAGE_BLOCKS_SMALL_WEIGHT_BY_LB con total 4.50. El minimo valido fue 4.50 y el maximo valido fue 4.50. Motivo comercial: Estrategia PACKAGE_BLOCKS con excepcion por servicio adicional cobrable: 5.00 lb cobradas por libra a 0.90. Total 4.50.",
        "evaluated_options": [
          {
            "extra_charge": "4.50",
            "extra_lb": "5.00",
            "option_type": "PACKAGE_BLOCKS_SMALL_WEIGHT_BY_LB",
            "reason": "Estrategia PACKAGE_BLOCKS con excepcion por servicio adicional cobrable: 5.00 lb cobradas por libra a 0.90. Total 4.50.",
            "selected": true,
            "tier_id": null,
            "tier_max_weight_lb": null,
            "tier_price": null,
            "total_price": "4.50"
          }
        ],
        "final_price": "4.50",
        "max_valid_price": "4.50",
        "min_valid_price": "4.50",
        "profile_id": 7,
        "profile_name": "Perfil PACKAGE_BLOCKS",
        "recommended_price": "4.50",
        "service_id": 0,
        "strategy_applied": "PACKAGE_BLOCKS",
        "weight_lb": "5.00"
      }
    },
    "validations": {
      "laundry_service": [],
      "order": [
        "payment_type_id es requerido para order",
        "falta construir el item comercial de lavado por peso para /v2/orders con service_id, weight_lb y final_unit_price"
      ]
    }
  },
  "payment_type_id": null,
  "pricing_profile_id": 7,
  "quoted_service_amount": "4.50",
  "scheduled_pickup_at": "2026-04-03T15:59:28-06:00",
  "service_label": "NORMAL",
  "status": "PENDING",
  "transaction_id": null,
  "updated_at": "2026-04-05T16:58:56-06:00",
  "updated_by_user_id": 6,
  "weight_lb": "5.00"
}
```

## Objetivo

Quiero que la pantalla muestre `4.50` y no `9.99`, y que quede consistente con la respuesta del backend en futuras ediciones del draft.
