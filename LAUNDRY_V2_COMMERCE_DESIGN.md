# Laundry V2 Commerce Design

## Fase 1

### Entidades propuestas

- `clients`, `client_addresses`, `users`: se reutilizan como maestros existentes.
- `service_categories`: agrupa servicios para orden, filtros y reportes.
- `services`: catalogo principal de servicios comerciales.
- `service_price_options`: multiples precios sugeridos para un mismo servicio.
- `extras_catalog`: adicionales cobrables por cantidad.
- `delivery_zones`: catalogo de zonas.
- `delivery_zone_prices`: historial de tarifas por zona.
- `weight_pricing_profiles`: configuracion comercial del motor por peso.
- `weight_pricing_tiers`: tiers configurables del perfil por peso.
- `orders`: pedido comercial con totales finales e historial economico.
- `order_items`: detalle de servicios cobrados.
- `order_extra_items`: detalle de extras cobrados.
- `order_status_history`: auditoria simple de cambios de estado.
- `order_weight_pricing_snapshot`: snapshot inmutable del calculo por peso aplicado.

### Logica de negocio

- El catalogo solo sugiere precios. Nunca gobierna el historico.
- El precio final cobrado vive en `orders`, `order_items` y `order_extra_items`.
- Cada item puede guardar precio sugerido, recomendado y final.
- Un override manual nunca borra el recomendado del motor.
- Delivery se guarda con precio sugerido y final en el pedido.
- Descuentos se guardan por item y a nivel global.
- El cobro queda ligado al usuario que lo realizo.

### Pricing por peso orientado a maximizar ingresos

- El perfil principal usa `MAX_REVENUE`.
- Para un peso dado el motor evalua alternativas comerciales validas.
- Las alternativas incluyen tier que cubre el peso, base mas extra y todos los tiers si `compare_all_tiers` esta activo.
- Bajo `MAX_REVENUE` se elige la alternativa con el mayor total valido.
- El resultado retorna opcion elegida, opciones evaluadas, diferencias monetarias y permiso de override.
- Si hay override manual, el snapshot conserva recomendado, final, usuario y motivo.
- La razon de decision ahora enumera las alternativas evaluadas y el por que comercial de la seleccion.

### Diagrama relacional en texto

- `service_categories 1 --- n services`
- `services 1 --- n service_price_options`
- `delivery_zones 1 --- n delivery_zone_prices`
- `weight_pricing_profiles 1 --- n weight_pricing_tiers`
- `clients 1 --- n orders`
- `orders 1 --- n order_items`
- `orders 1 --- n order_extra_items`
- `orders 1 --- n order_status_history`
- `order_items 1 --- 0..1 order_weight_pricing_snapshot`
- `services 1 --- n order_items`
- `extras_catalog 1 --- n order_extra_items`
- `users 1 --- n orders`, `order_items`, `order_status_history`, `order_weight_pricing_snapshot`

## Fase 2

El script base esta en [sql/20260327_commerce_v2.sql](/home/ness/Dev/Python/drinout-backend/sql/20260327_commerce_v2.sql).

Incluye:

- tablas nuevas
- llaves foraneas
- indices de consulta
- seed comercial inicial
- perfil principal `MAX_REVENUE`
- tiers iniciales `15 lb = 9.99` y `25 lb = 14.99`

## Fase 3

### Estructura recomendada

```text
app/
  extensions/
  modules/
    laundry/
      v2/
        service_categories/
        services_catalog/
        service_price_options/
        extras/
        delivery_zones/
        weight_pricing/
        orders/
  services/
models/
schemas/
sql/
```

### Responsabilidad

- `extensions/`: inicializacion de Flask, DB, JWT y sockets.
- `modules/.../routes.py`: capa HTTP y validaciones de entrada.
- `services/`: logica de negocio reusable. Aqui vive `weight_pricing.py`.
- `models/`: persistencia ORM y relaciones.
- `schemas/`: contratos de entrada y salida con Marshmallow.
- `sql/`: bootstrap de MariaDB y semillas operativas.

## Fase 4

Se implementaron:

- modelos SQLAlchemy para catalogo, pedidos, delivery y pricing por peso
- schemas Marshmallow para CRUD y respuestas
- blueprints CRUD minimos protegidos con JWT para:
  - `/v2/service-categories`
  - `/v2/services`
  - `/v2/service-price-options`
  - `/v2/extras`
  - `/v2/delivery-zones`
  - `/v2/weight-pricing/profiles`
  - `/v2/weight-pricing/tiers`
  - `/v2/orders`

## Fase 5

El motor vive en [app/services/weight_pricing.py](/home/ness/Dev/Python/drinout-backend/app/services/weight_pricing.py).

Soporta:

- `MAX_REVENUE`
- `BEST_TIER_FIT`
- `BASE_PLUS_EXTRA`
- `CUSTOMER_BEST_PRICE`
- `PROMOTIONAL_UPGRADE`
- `FORCE_UPGRADE_FROM_WEIGHT`

Retorna:

- precio seleccionado
- estrategia aplicada
- tier elegido
- opciones evaluadas
- diferencia contra minimo y maximo
- permiso de override
- razon comercial

### Casos minimos cubiertos

- Caso A: `22 lb` con tiers `15=9.99`, `25=14.99` y `extra_lb_price=0.90` selecciona `16.29`.
- Caso B: `20 lb` con tiers `15=9.99`, `25=14.99` y `extra_lb_price=0.90` selecciona `14.99`.
- Caso C: el motor expone si se permite override manual y el pedido persiste recomendado, final, usuario y motivo.

Las pruebas minimas quedaron en [tests/test_weight_pricing.py](/home/ness/Dev/Python/drinout-backend/tests/test_weight_pricing.py).

## Fase 6

### Endpoints recomendados

- `GET /v2/service-categories`
- `POST /v2/service-categories`
- `PATCH /v2/service-categories/:id`
- `GET /v2/services?category_id=&pricing_mode=&is_active=`
- `POST /v2/services`
- `PATCH /v2/services/:id`
- `GET /v2/service-price-options?service_id=`
- `POST /v2/service-price-options`
- `PATCH /v2/service-price-options/:id`
- `GET /v2/extras`
- `POST /v2/extras`
- `PATCH /v2/extras/:id`
- `GET /v2/delivery-zones`
- `POST /v2/delivery-zones`
- `PATCH /v2/delivery-zones/:id`
- `POST /v2/delivery-zones/:id/prices`
- `GET /v2/weight-pricing/profiles`
- `POST /v2/weight-pricing/profiles`
- `PATCH /v2/weight-pricing/profiles/:id`
- `GET /v2/weight-pricing/tiers?profile_id=`
- `POST /v2/weight-pricing/tiers`
- `PATCH /v2/weight-pricing/tiers/:id`
- `POST /v2/weight-pricing/quote`
- `GET /v2/orders?client_id=&status=&charged_by_user_id=&page=&per_page=`
- `POST /v2/orders`
- `GET /v2/orders/:id`
- `PATCH /v2/orders/:id`

## Fase 7

### Payload JSON ejemplo

```json
{
  "client_id": 12,
  "client_address_id": 33,
  "pricing_profile_id": 1,
  "delivery_zone_id": 2,
  "delivery_fee_final": "3.50",
  "delivery_fee_override_reason": "Ajuste por zona extendida",
  "status": "CONFIRMED",
  "global_discount_amount": "2.00",
  "global_discount_reason": "Cortesia comercial",
  "notes": "Pedido con mezcla de precio sugerido, manual y por peso",
  "items": [
    {
      "service_id": 1,
      "suggested_price_option_id": 3,
      "quantity": "1.00",
      "discount_amount": "0.00",
      "notes": "Alfombra mediana"
    },
    {
      "service_id": 21,
      "suggested_price_option_id": 2,
      "quantity": "1.00",
      "final_unit_price": "6.50",
      "discount_amount": "0.00",
      "manual_price_override_reason": "Mayor suciedad de lo normal",
      "notes": "Mochila con manchas fuertes"
    },
    {
      "service_id": 26,
      "weight_lb": "22.00",
      "final_unit_price": "16.29",
      "discount_amount": "0.00",
      "manual_price_override_reason": "Se respeta calculo recomendado del motor",
      "notes": "Lavado por peso"
    }
  ],
  "extras": [
    {
      "extra_id": 2,
      "quantity": "1.00",
      "notes": "Suavisante generico"
    },
    {
      "extra_id": 3,
      "quantity": "2.00",
      "notes": "Suavitel"
    }
  ]
}
```

### Snapshot esperado para el item por peso

```json
{
  "pricing_profile_name_snapshot": "Perfil Principal MAX_REVENUE",
  "strategy_applied": "MAX_REVENUE",
  "weight_lb": "22.00",
  "recommended_price": "16.29",
  "final_price": "16.29",
  "override_applied": false,
  "allow_manual_override": true,
  "lowest_valid_price": "14.99",
  "highest_valid_price": "16.29",
  "difference_selected_vs_lowest": "1.30",
  "difference_selected_vs_highest": "0.00"
}
```

## Fase 8

### Validaciones backend

- impedir pedidos sin items
- validar que `client_address_id` pertenezca al cliente
- validar que price option pertenezca al servicio
- obligar `weight_lb` en servicios `WEIGHT`
- obligar motivo cuando haya override manual relevante
- impedir descuentos mayores al subtotal
- impedir crear pedidos sobre catalogos inexistentes

### Historico de precios

- nunca recalcular pedidos historicos desde catalogo
- siempre persistir snapshots de nombres, labels y precios
- mantener delivery sugerido y final en el pedido
- guardar snapshot del motor por peso por item

### Manejo correcto de dinero

- usar `Decimal` en Python
- usar `DECIMAL(10,2)` en MariaDB
- evitar `float` para calculos monetarios
- serializar precios como string en JSON cuando se requiera exactitud

### Reportes futuros

- ventas por categoria
- ventas por usuario cobrador
- revenue por estrategia de pricing
- diferencia entre recomendado y cobrado
- uso por extra
- revenue por zona delivery

## Riesgos a evitar

- recalcular pedidos viejos con reglas nuevas
- mezclar catalogo con historico facturable
- guardar solo precio final sin recomendado
- esconder los overrides manuales
- fijar enums demasiado rigidos para negocio cambiante

## Tablas o clases a fortalecer primero

- `weight_pricing_profiles`
- `weight_pricing_tiers`
- `orders`
- `order_items`
- `order_weight_pricing_snapshot`

## Preparacion para promociones futuras

- perfiles de pricing alternos
- reglas promocionales por rango de peso
- vigencia por fechas en `delivery_zone_prices`
- multiples listas de precio sugerido por temporada

## Mejoras recomendadas despues

- repositorios para desacoplar DB de rutas
- tests unitarios del motor de pricing
- endpoint de re-cotizacion previa antes de crear pedido
- auditoria avanzada de overrides y descuentos
- soporte de impuestos y metodos de pago del pedido
