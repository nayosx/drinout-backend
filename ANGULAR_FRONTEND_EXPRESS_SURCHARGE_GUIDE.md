# Angular Frontend Express Surcharge Guide

Guia para Angular sobre la nueva regla de recargo para servicios `EXPRESS`.

## Regla de negocio

- Si `service_label` es `NORMAL`, el recargo es `0.00`
- Si `service_label` es `EXPRESS`, se suma un recargo fijo configurable desde base de datos

Parametro configurable en backend:

- `express_service_surcharge`

Valor inicial sembrado:

- `5.00`

## Donde se obtiene

Usar:

- `GET /v2/global-settings/express_service_surcharge`

Respuesta esperada:

```json
{
  "id": 2,
  "key": "express_service_surcharge",
  "name": "Recargo por servicio EXPRESS",
  "description": "Recargo fijo configurable que se suma al precio del servicio cuando service_label es EXPRESS",
  "value_type": "DECIMAL",
  "value": "5.00",
  "is_active": true,
  "created_at": "2026-04-04T00:00:00",
  "updated_at": "2026-04-04T00:00:00"
}
```

## Como debe calcular Angular

Base del servicio:

- tomar `weight_pricing_preview.final_price`

Recargo por modalidad:

- si `service_label === 'EXPRESS'`, usar `express_service_surcharge`
- si `service_label === 'NORMAL'`, usar `0.00`

Precio cotizado final del servicio:

```ts
const baseServiceAmount = Number(weightPricingPreview?.final_price ?? 0);
const expressSurcharge = serviceLabel === 'EXPRESS'
  ? Number(expressServiceSurcharge ?? 0)
  : 0;

const quotedServiceAmount = Number((baseServiceAmount + expressSurcharge).toFixed(2));
```

## Que guardar en el draft

Se recomienda que el `ui_model` guarde explicitamente estos campos:

- `express_service_surcharge`
- `quoted_service_amount`

Ejemplo dentro de `ui_model`:

```json
{
  "service_label": "EXPRESS",
  "weight_lb": 54,
  "weight_pricing_preview": {
    "final_price": "33.58"
  },
  "express_service_surcharge": 5,
  "quoted_service_amount": 38.58
}
```

## Importante para drafts

El backend del draft ya intenta guardar `quoted_service_amount` como columna util.

Prioridad actual:

1. `ui_model.quoted_service_amount`
2. si no existe, `weight_pricing_preview.final_price`

Por eso Angular debe mandar `quoted_service_amount` si quiere que el draft refleje el precio final incluyendo el recargo EXPRESS.

## UI recomendada

Mostrar al usuario:

- `Precio base por peso: $33.58`
- `Recargo EXPRESS: $5.00`
- `Precio cotizado del servicio: $38.58`

## Nota

Este recargo no debe modelarse como extra tipo sal, vanish, remojo o perlitas.

Se trata como una regla comercial del servicio, no como un extra consumible independiente.
