# Laundry V2 Commercial Redesign

## Objetivo

Reordenar el flujo comercial de lavanderia para que:

- `laundry_services` siga siendo la entidad operativa principal.
- `laundry_service_commercial_drafts` deje de comportarse como fuente de verdad permanente.
- `orders` se convierta en la entidad comercial confirmada.
- `transactions` vuelva a ser el movimiento financiero real.
- el frontend actual pueda seguir funcionando mientras se hace la transicion.

Este rediseño busca corregir la ambiguedad actual sin exigir un rewrite total del frontend.

## Problema actual

Hoy el sistema tiene cuatro piezas con responsabilidades parcialmente solapadas:

1. `laundry_services`
2. `laundry_service_commercial_drafts`
3. `orders`
4. `transactions`

Los sintomas principales son:

- el draft comercial duplica datos del servicio
- el draft guarda payload de UI, validaciones y montos en el mismo objeto
- el precio por peso puede existir en varios lugares del response
- extras e items del draft no siempre se materializan en tablas normalizadas
- `payment_type_id` puede vivir en draft, en order y en transaction
- el frontend termina teniendo que adivinar cual campo manda

En la practica, el draft actual funciona como:

- snapshot editable de UI
- borrador comercial
- pseudo orden

Eso vuelve dificil saber:

- cual es la fuente de verdad del precio
- cuando un servicio ya esta comercialmente listo
- cuando un cobro existe de verdad

## Principios del rediseño

1. Una entidad, una responsabilidad principal.
2. El estado operativo del servicio no debe depender del cobro.
3. El draft debe ser temporal y derivado.
4. La venta confirmada debe tener datos normalizados y congelados.
5. La transaccion financiera debe existir solo cuando hay cobro real.
6. El frontend no debe recalcular precios si backend ya devolvio el valor final.

## Modelo propuesto

### 1. `laundry_services`

Representa la orden operativa de trabajo.

Debe responder:

- quien es el cliente
- donde se atiende
- cuando se recoge o procesa
- que prendas, extras y peso se recibieron
- en que estado operativo va el servicio

Debe contener:

- `client_id`
- `client_address_id`
- `scheduled_pickup_at`
- `status`
- `service_label`
- `weight_lb`
- `notes`
- `items`
- `extras`
- `created_by_user_id`

Debe dejar de cargar responsabilidad comercial final.

Decision recomendada:

- mantener `transaction_id` por compatibilidad mientras se migra
- dejar de usarlo como relacion comercial principal
- agregar a futuro `order_id` nullable como referencia comercial principal

### 2. `laundry_service_commercial_drafts`

Representa un borrador temporal de trabajo comercial.

Debe responder:

- que propuesta comercial se esta editando para un servicio
- cual es el precio recomendado por backend
- que validaciones faltan para confirmar
- que datos temporales necesita la UI para seguir editando

No debe ser fuente de verdad historica.

Debe contener:

- `laundry_service_id`
- `payload_json`
- `is_confirmed`
- auditoria

El payload debe ser tratado explicitamente como:

- estado de edicion
- snapshot temporal
- soporte de UI

No debe ser usado como base principal para reportes.

### 3. `orders`

Representa la venta confirmada.

Debe responder:

- que se va a cobrar
- cuanto se va a cobrar
- con que metodo de pago se quiere cobrar
- que snapshots comerciales deben congelarse

Debe ser la fuente de verdad comercial despues de confirmar.

Debe contener:

- cliente y direccion
- `pricing_profile_id`
- `payment_type_id`
- items cobrables normalizados
- extras cobrables normalizados
- delivery
- descuentos
- subtotales
- total final
- snapshots necesarios para historico

### 4. `transactions`

Representa el movimiento financiero real.

Debe responder:

- que dinero entro o salio
- quien lo registro
- por que medio se pago
- por cuanto monto

`transactions.payment_type_id` sigue siendo correcto, porque el medio de pago pertenece naturalmente al hecho financiero.

## Relacion correcta entre entidades

Flujo deseado:

`laundry_service` -> `commercial_draft` -> `order` -> `transaction`

Semantica:

- `laundry_service`: existe desde que se recibe el trabajo
- `commercial_draft`: existe mientras se cotiza y edita
- `order`: existe cuando se confirma comercialmente
- `transaction`: existe cuando se cobra

## Fuente de verdad por tema

### Operacion del servicio

Fuente de verdad:

- `laundry_services`

### Edicion comercial temporal

Fuente de verdad:

- `laundry_service_commercial_drafts.payload_json`

### Venta confirmada

Fuente de verdad:

- `orders`

### Movimiento financiero real

Fuente de verdad:

- `transactions`

## Cambios de modelo recomendados

## Fase 1: sin romper frontend actual

Objetivo:

- mantener contratos actuales
- aclarar responsabilidad interna
- preparar terreno para migracion

Cambios:

1. Tratar `commercial_draft` como temporal.
2. Seguir devolviendo `payload.ui_model` al frontend actual.
3. Al guardar draft, sincronizar `items` y `extras` tambien en tablas normalizadas del servicio cuando aplique.
4. Al confirmar draft, crear `order`.
5. No crear `transaction` todavia en esa confirmacion si el cobro no ha ocurrido.

Resultado:

- el frontend actual casi no cambia
- backend gana consistencia operativa
- se habilitan reportes sobre `laundry_service_items` y `laundry_service_extras`

## Fase 2: formalizar relacion comercial

Objetivo:

- mover la verdad comercial confirmada a `orders`

Cambios recomendados:

1. Agregar `order_id` nullable en `laundry_services`.
2. Al confirmar un draft:
   - crear o actualizar `order`
   - guardar `laundry_services.order_id`
   - marcar draft como confirmado
3. Mantener `transaction_id` nullable en `laundry_services` solo por compatibilidad.
4. Dejar de depender de `laundry_services.transaction_id` como indicador de cierre comercial.

Resultado:

- el servicio sabe cual es su venta confirmada
- el cobro queda desacoplado de la operacion

## Fase 3: simplificar semantica de cobro

Objetivo:

- hacer que el cobro cuelgue de la venta, no del servicio operativo

Cambios recomendados:

1. Agregar `transaction_id` nullable en `orders`, o una relacion `order_transactions` si luego se quieren pagos multiples.
2. Crear `transaction` al momento de cobrar.
3. Mantener `orders.payment_type_id` como medio de pago esperado o elegido al confirmar.
4. Si el medio real de cobro cambia al pagar, permitir actualizarlo en el cobro final y reflejarlo en transaction.

Resultado:

- `order` representa el compromiso comercial
- `transaction` representa la realizacion financiera

## Que campos deberian vivir en cada lado

### En `laundry_services`

Debe vivir:

- cliente
- direccion
- pickup
- estado operativo
- peso
- notas
- items operativos
- extras operativos
- `order_id` futuro

No deberia vivir como fuente principal:

- total final de venta
- validaciones comerciales
- payload UI

### En `commercial_drafts`

Debe vivir:

- payload editable
- `weight_pricing_preview`
- `commercial_capture_pending`
- validaciones
- delivery y descuentos temporales
- `payment_type_id` tentativo

No deberia vivir de forma definitiva:

- historico facturable final
- fuente de reportes

### En `orders`

Debe vivir:

- item por peso final
- items comerciales finales
- extras comerciales finales
- delivery final
- descuento final
- `payment_type_id`
- total final
- snapshots comerciales

### En `transactions`

Debe vivir:

- monto cobrado real
- `payment_type_id` usado realmente
- usuario que cobro
- tipo de movimiento
- fecha de movimiento

## Contrato recomendado para frontend

Mientras exista el draft:

- la pantalla de edicion comercial sigue leyendo del draft
- el precio mostrado debe salir primero de backend

Prioridad recomendada para mostrar precio por peso:

1. `response.payload.ui_model.weight_pricing_preview.final_price`
2. `response.payload.ui_model.quoted_service_amount`
3. `response.quoted_service_amount`

Nunca recalcular localmente si backend ya devolvio alguno de esos campos.

Cuando el draft sea confirmado:

- la pantalla de resumen comercial debe empezar a leer desde `order`
- el frontend no deberia seguir usando el draft como fuente principal para mostrar totales confirmados

## Compatibilidad con frontend actual

Este rediseño no exige romper el frontend actual en una sola entrega.

Compatibilidad minima:

1. Mantener `GET /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id`.
2. Mantener `payload.ui_model`.
3. Seguir devolviendo `quoted_service_amount`.
4. Empezar a alinear internamente `payload.ui_model.items` y `payload.ui_model.extras` con tablas reales.
5. Agregar, despues, endpoints o campos para exponer el `order` confirmado.

## Cambios backend recomendados

### Cambio 1

Hacer que guardar draft sincronice tambien `laundry_service_items` y `laundry_service_extras` cuando esos arreglos existan en el payload.

Beneficio:

- reportabilidad
- menos divergencia entre servicio y draft

### Cambio 2

Crear un endpoint explicito de confirmacion comercial.

Ejemplo:

- `POST /v2/laundry-service-commercial-drafts/by-service/:laundry_service_id/confirm`

Responsabilidad:

- validar draft
- materializar `order`
- marcar draft como confirmado
- enlazar `laundry_service` con `order`

### Cambio 3

Separar confirmacion comercial de cobro.

Ejemplo:

- confirmar draft no crea transaccion
- cobrar order si crea transaccion

### Cambio 4

Agregar un endpoint de consulta consolidada para front.

Ejemplo:

- `GET /v2/laundry_services/:id/commercial-summary`

Que devuelva:

- servicio operativo
- draft si existe y no esta confirmado
- order si existe
- transaction si existe
- `current_source_of_truth`

Eso reduce logica condicional en Angular.

## Riesgos que evita este rediseño

- mostrar precios viejos por leer campos equivocados
- dejar extras solo en JSON
- confundir cotizacion con venta cerrada
- crear transacciones antes del cobro real
- amarrar el servicio operativo al estado financiero
- duplicar logica de negocio entre frontend y backend

## Plan de migracion sugerido

### Paso 1

Mantener tablas actuales y contratos actuales.

### Paso 2

Sincronizar items y extras del draft hacia tablas operativas.

### Paso 3

Agregar `order_id` nullable a `laundry_services`.

### Paso 4

Crear confirmacion de draft que materialice `order`.

### Paso 5

Actualizar frontend para que:

- pantalla de edicion use draft
- pantalla confirmada use order

### Paso 6

Mover el cobro real a `transaction` creada desde `order`.

### Paso 7

Deprecar gradualmente el uso de `laundry_services.transaction_id` como referencia comercial principal.

## Resumen ejecutivo

La mejor forma de ordenar esto sin romper todo es:

- dejar `laundry_services` como entidad operativa principal
- dejar `commercial_draft` como entidad temporal de edicion
- usar `orders` como venta confirmada
- usar `transactions` como cobro real

El frontend actual puede seguir funcionando si backend mantiene el draft como contrato de edicion, pero internamente se debe dejar de tratar ese draft como si fuera la entidad comercial final.

## Nota para frontend

Mientras se completa la transicion:

- para edicion, consumir draft
- para confirmados, consumir order cuando exista
- para precio por peso, usar siempre el valor final devuelto por backend
- no recalcular localmente si backend ya devolvio `final_price`
