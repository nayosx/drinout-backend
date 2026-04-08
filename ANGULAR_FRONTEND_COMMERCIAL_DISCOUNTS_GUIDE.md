# Angular Frontend Commercial Global Discounts Guide

Guia para Angular sobre como manejar descuentos globales en el draft comercial de lavanderia.

## Objetivo

Permitir dos tipos de descuento global:

1. descuento global por porcentaje
2. descuento global por precio final objetivo

El descuento aplica al total comercial completo del draft, no solo al lavado por peso ni a un item individual.

## Regla funcional principal

El descuento es global.

Eso significa que puede aplicarse sobre un total compuesto por cualquier mezcla de:

- lavado por peso
- items fijos como edredones, camas de mascotas o vestidos
- servicios adicionales comerciales
- extras
- delivery
- recargo EXPRESS

No todos los servicios tienen lavado por peso, por lo tanto el descuento no debe depender del item de peso.

## Fuente de verdad del total base

Frontend debe construir un `gross_total` del draft usando los datos disponibles del backend y del estado actual de la UI.

## Componentes del `gross_total`

El total bruto recomendado debe salir de la suma de:

1. subtotal de servicios comerciales
2. subtotal de extras
3. delivery final
4. recargo EXPRESS

Formula:

```ts
grossTotal =
  servicesSubtotal +
  extrasSubtotal +
  deliveryFeeFinal +
  expressServiceSurcharge;
```

## Como obtener cada componente

## 1. Servicios comerciales

Debe incluir:

- item por peso si existe
- items comerciales adicionales

### Item por peso

Usar prioridad:

1. `payload.ui_model.weight_pricing_preview.final_price`
2. `payload.ui_model.quoted_service_amount`
3. `quoted_service_amount`

Pero ojo:

- si `quoted_service_amount` ya incluye EXPRESS, no lo sumes otra vez
- la mejor referencia pura del item por peso sigue siendo `weight_pricing_preview.final_price`

## 2. Servicios comerciales adicionales

Para cada fila en `commercial_capture_pending`, usar:

1. `manual_price` como precio unitario final si existe
2. si no existe, precio sugerido de la opcion seleccionada

Subtotal por fila:

```ts
lineSubtotal = round2(quantity * unitFinalPrice);
```

## 3. Extras

Para cada extra:

```ts
lineSubtotal = round2(quantity * unitPrice);
```

## 4. Delivery

Usar:

- `payload.ui_model.delivery_fee_final`

## 5. EXPRESS

Usar:

- `payload.ui_model.express_service_surcharge`

Si no existe, usar `0`.

## Importante

El recargo EXPRESS ya no debe inventarse en frontend.

Debe venir del backend como dato calculado/configurado.

## Tipos de descuento global en UI

## A. Descuento global por porcentaje

El usuario indica un porcentaje.

Formula:

```ts
globalDiscountAmount = round2(grossTotal * (percent / 100));
netTotal = round2(grossTotal - globalDiscountAmount);
```

## B. Descuento global por precio final objetivo

El usuario indica cuanto quiere cobrar al final.

Formula:

```ts
targetFinalTotal = round2(userTargetFinalTotal);
globalDiscountAmount = round2(grossTotal - targetFinalTotal);
netTotal = round2(grossTotal - globalDiscountAmount);
```

## Validaciones

Siempre validar:

- `grossTotal >= 0`
- `globalDiscountAmount >= 0`
- `netTotal >= 0`
- `targetFinalTotal <= grossTotal`

Si `targetFinalTotal > grossTotal`, eso ya no es descuento.

## Regla de comportamiento mientras el draft sigue cambiando

Este punto es clave.

Como el total del draft puede cambiar cuando el usuario:

- agrega o quita items
- agrega extras
- cambia delivery
- cambia `NORMAL` a `EXPRESS`
- pone o cambia peso

entonces el descuento global no debe tratarse como un monto fijo hasta el final.

## Regla recomendada

Si el usuario elige:

- descuento por porcentaje:
  guardar el porcentaje y recalcular `global_discount_amount` cada vez que cambie `gross_total`

- descuento por precio final objetivo:
  guardar el objetivo final y recalcular `global_discount_amount` cada vez que cambie `gross_total`

En otras palabras:

- el valor estable es la intencion del descuento
- el monto descontado es derivado del total actual

## Estado recomendado en Angular

Guardar en UI:

```ts
type GlobalDiscountType = 'PERCENT' | 'TARGET_FINAL_TOTAL' | null;

interface GlobalDiscountState {
  type: GlobalDiscountType;
  value: number | null;
  amount: number;
  reason: string | null;
}
```

## Campos sugeridos para guardar en `ui_model`

```json
{
  "global_discount_type": "PERCENT",
  "global_discount_value": 10,
  "global_discount_amount": 3.15,
  "global_discount_reason": "Cortesia comercial",
  "gross_total_before_global_discount": 31.51,
  "net_total_after_global_discount": 28.36
}
```

Si es por precio final objetivo:

```json
{
  "global_discount_type": "TARGET_FINAL_TOTAL",
  "global_discount_value": 25.00,
  "global_discount_amount": 6.51,
  "global_discount_reason": "Precio final negociado",
  "gross_total_before_global_discount": 31.51,
  "net_total_after_global_discount": 25.00
}
```

## Relacion con campos ya existentes

Backend ya tiene:

- `global_discount_amount`
- `global_discount_reason`

Por compatibilidad, frontend debe seguir poblando:

- `global_discount_amount`
- `global_discount_reason`

Y adicionalmente puede guardar en `ui_model`:

- `global_discount_type`
- `global_discount_value`
- `gross_total_before_global_discount`
- `net_total_after_global_discount`

## Snippets sugeridos

## Utilidad base

```ts
function round2(value: number): number {
  return Number((value || 0).toFixed(2));
}
```

## Calcular subtotal de servicios

```ts
function getServicesSubtotal(uiModel: any, selectedPriceMap: Record<number, number>): number {
  const weightPrice = Number(uiModel?.weight_pricing_preview?.final_price ?? 0);

  const pending = Array.isArray(uiModel?.commercial_capture_pending)
    ? uiModel.commercial_capture_pending
    : [];

  const pendingSubtotal = pending.reduce((acc: number, row: any) => {
    const quantity = Number(row?.quantity ?? 0);
    const unitPrice =
      row?.manual_price != null
        ? Number(row.manual_price)
        : Number(selectedPriceMap[row?.selected_price_option_id] ?? 0);

    return acc + round2(quantity * unitPrice);
  }, 0);

  return round2(weightPrice + pendingSubtotal);
}
```

## Calcular subtotal de extras

```ts
function getExtrasSubtotal(uiModel: any): number {
  const extras = Array.isArray(uiModel?.extras) ? uiModel.extras : [];

  return round2(
    extras.reduce((acc: number, row: any) => {
      const quantity = Number(row?.quantity ?? 0);
      const unitPrice = Number(row?.unit_price ?? 0);
      return acc + round2(quantity * unitPrice);
    }, 0)
  );
}
```

## Calcular total bruto

```ts
function getGrossTotal(uiModel: any, selectedPriceMap: Record<number, number>): number {
  const servicesSubtotal = getServicesSubtotal(uiModel, selectedPriceMap);
  const extrasSubtotal = getExtrasSubtotal(uiModel);
  const deliveryFeeFinal = Number(uiModel?.delivery_fee_final ?? 0);
  const expressServiceSurcharge = Number(uiModel?.express_service_surcharge ?? 0);

  return round2(
    servicesSubtotal +
    extrasSubtotal +
    deliveryFeeFinal +
    expressServiceSurcharge
  );
}
```

## Descuento por porcentaje

```ts
function applyGlobalPercentDiscount(grossTotal: number, percent: number) {
  const safeGross = round2(grossTotal);
  const safePercent = Math.max(0, percent || 0);
  const amount = round2(safeGross * (safePercent / 100));
  const netTotal = round2(Math.max(0, safeGross - amount));

  return {
    type: 'PERCENT',
    value: safePercent,
    amount,
    netTotal,
  };
}
```

## Descuento por precio final objetivo

```ts
function applyGlobalTargetFinalDiscount(grossTotal: number, targetFinalTotal: number) {
  const safeGross = round2(grossTotal);
  const safeTarget = round2(Math.max(0, targetFinalTotal || 0));
  const boundedTarget = Math.min(safeGross, safeTarget);
  const amount = round2(safeGross - boundedTarget);

  return {
    type: 'TARGET_FINAL_TOTAL',
    value: boundedTarget,
    amount,
    netTotal: boundedTarget,
  };
}
```

## Actualizar `ui_model`

```ts
function applyGlobalDiscountToUiModel(
  uiModel: any,
  selectedPriceMap: Record<number, number>,
  discountState: GlobalDiscountState
) {
  const grossTotal = getGrossTotal(uiModel, selectedPriceMap);

  const computed =
    discountState.type === 'PERCENT'
      ? applyGlobalPercentDiscount(grossTotal, Number(discountState.value ?? 0))
      : discountState.type === 'TARGET_FINAL_TOTAL'
        ? applyGlobalTargetFinalDiscount(grossTotal, Number(discountState.value ?? 0))
        : {
            type: null,
            value: null,
            amount: 0,
            netTotal: grossTotal,
          };

  return {
    ...uiModel,
    global_discount_amount: computed.amount,
    global_discount_reason: discountState.reason ?? null,
    global_discount_type: computed.type,
    global_discount_value: computed.value,
    gross_total_before_global_discount: grossTotal,
    net_total_after_global_discount: computed.netTotal,
  };
}
```

## Que debe mandar frontend en autosave

Frontend debe seguir mandando:

- `global_discount_amount`
- `global_discount_reason`

Y adicionalmente:

- `global_discount_type`
- `global_discount_value`
- `gross_total_before_global_discount`
- `net_total_after_global_discount`

Ejemplo:

```ts
const nextPayload = {
  ...draft.payload,
  ui_model: applyGlobalDiscountToUiModel(
    draft.payload.ui_model,
    selectedPriceMap,
    globalDiscountState
  ),
};
```

## Relacion con backend

Con el backend actual:

- `global_discount_amount` ya se persiste en `orders`
- `global_discount_reason` ya se persiste en `orders`

Eso significa que Angular ya puede trabajar desde ya con descuento global si mantiene esos dos campos alineados.

## Recomendacion importante

No repartas el descuento global manualmente entre items en frontend.

No hace falta:

- tocar `discount_amount` por item
- reescribir precios item por item
- alterar `weight_pricing_preview.final_price`

El descuento global debe vivir como descuento global.

## Resumen operativo

La forma correcta de hacerlo en frontend es:

1. construir `gross_total` con todos los componentes del draft
2. capturar descuento global por porcentaje o por precio final objetivo
3. recalcular `global_discount_amount` cada vez que cambie el total
4. guardar la intencion del descuento y el monto recalculado en `ui_model`
5. mandar `global_discount_amount` y `global_discount_reason` para que backend lo persista al confirmar

## Siguiente paso recomendado

Si despues quieres cerrar el loop completamente, el backend puede:

- recalcular `gross_total` tambien al confirmar
- validar si el `global_discount_amount` recibido es coherente
- devolver `gross_total_before_global_discount` y `net_total_after_global_discount` ya normalizados

Pero para empezar, Angular ya puede implementar el descuento global correctamente con esta guia.
