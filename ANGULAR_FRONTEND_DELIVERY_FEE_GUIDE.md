# Angular Frontend Delivery Fee Guide

Guia practica para Angular sobre como precargar y mostrar el cobro de envio en la captura de ordenes `v2`.

## Objetivo

El frontend debe mostrar dos referencias separadas:

- precio sugerido por zona
- ultimo costo de envio usado para ese cliente

La intencion es que el usuario pueda ver el precio por zona como referencia, pero editar o confirmar el ultimo costo real que normalmente se le cobra a ese cliente.

## Endpoint nuevo

`GET /v2/orders/delivery-fee-suggestion`

### Query params

- `client_id` obligatorio
- `client_address_id` opcional
- `delivery_zone_id` opcional

### Ejemplo

```http
GET /v2/orders/delivery-fee-suggestion?client_id=3&client_address_id=2&delivery_zone_id=1
Authorization: Bearer <token>
```

### Respuesta esperada

```json
{
  "client_id": 3,
  "client_address_id": 2,
  "delivery_zone_id": 1,
  "delivery_zone_name": "Centro",
  "delivery_zone_price_id": 10,
  "delivery_fee_suggested_by_zone": "2.50",
  "last_delivery_fee_final_for_client_address": "5.20",
  "last_delivery_fee_final_for_client": "5.20",
  "last_delivery_order_id_for_client_address": 15,
  "last_delivery_order_id_for_client": 15,
  "has_previous_delivery_for_client_address": true,
  "has_previous_delivery_for_client": true,
  "initial_delivery_fee_final": "5.20"
}
```

## Regla de negocio para frontend

- Mostrar `delivery_fee_suggested_by_zone` como referencia visual, no como el unico valor editable.
- Mostrar un `input` aparte para `delivery_fee_final`.
- Ese `input` debe inicializarse con `initial_delivery_fee_final`.
- Si no existe historial previo para esa direccion ni para el cliente, `initial_delivery_fee_final` vendra en `"0.00"`.
- Si `initial_delivery_fee_final` viene en `"0.00"`, el usuario define manualmente el valor a cobrar.

## Prioridad del valor inicial

El backend devuelve `initial_delivery_fee_final` con esta prioridad:

1. ultimo `delivery_fee_final` usado para esa misma `client_address_id`
2. si no existe, ultimo `delivery_fee_final` usado para ese `client_id`
3. si nunca ha tenido envio, `0.00`

## Mapeo recomendado en Angular

Campos sugeridos en el state o form:

```ts
type DeliveryFeeSuggestionDto = {
  client_id: number;
  client_address_id: number | null;
  delivery_zone_id: number | null;
  delivery_zone_name: string | null;
  delivery_zone_price_id: number | null;
  delivery_fee_suggested_by_zone: string;
  last_delivery_fee_final_for_client_address: string;
  last_delivery_fee_final_for_client: string;
  last_delivery_order_id_for_client_address: number | null;
  last_delivery_order_id_for_client: number | null;
  has_previous_delivery_for_client_address: boolean;
  has_previous_delivery_for_client: boolean;
  initial_delivery_fee_final: string;
};
```

```ts
form.patchValue({
  delivery_fee_final: suggestion.initial_delivery_fee_final
});
```

## UI recomendada

Bloque visual sugerido:

- `Precio sugerido por zona: $2.50`
- `Ultimo costo cobrado a este cliente: $5.20`
- `Costo de envio a cobrar:` input editable con `5.20`

Si no hay historial:

- `Precio sugerido por zona: $2.50`
- `Ultimo costo cobrado a este cliente: $0.00`
- `Costo de envio a cobrar:` input editable vacio o con `0.00`

## Como enviar la orden

Al crear la orden, Angular debe seguir enviando:

- `delivery_zone_id`
- `delivery_fee_final`
- `delivery_fee_override_reason` si aplica

Ejemplo:

```json
{
  "client_id": 3,
  "client_address_id": 2,
  "pricing_profile_id": 7,
  "payment_type_id": 3,
  "delivery_zone_id": 1,
  "delivery_fee_final": "5.20",
  "delivery_fee_override_reason": "Costo historico del cliente",
  "status": "CONFIRMED",
  "items": [
    {
      "service_id": 10,
      "weight_lb": "32.00"
    }
  ],
  "extras": []
}
```

## Nota importante

Si la zona tiene precio activo, el backend lo guarda como `delivery_fee_suggested`.

Si el usuario escribe otro valor en `delivery_fee_final`, el backend lo guarda como override y conserva ambos:

- sugerido por zona
- final cobrado
