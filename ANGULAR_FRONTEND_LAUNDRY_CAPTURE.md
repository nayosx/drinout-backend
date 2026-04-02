# Angular Frontend Laundry Capture Guide

## Objetivo

Implementar en el frontend Angular el flujo de captura de lavanderia en 2 pantallas:

1. Pantalla 1: datos generales del servicio.
2. Pantalla 2: detalle operativo del servicio.

El frontend debe usar:

- PrimeNG v19 para componentes UI.
- estilos base desde `node_modules/drstyles`.


## Stack visual requerido

- Usar componentes de PrimeNG v19.
- Mantener consistencia con el theme y utilidades provistas por `node_modules/drstyles`.
- No crear estilos visuales aislados si ya existe una clase/utilidad equivalente en `drstyles`.
- Priorizar layout limpio con acordeones, cards, inputs numericos y tablas ligeras.

Sugerencia de componentes PrimeNG v19:

- `p-card`
- `p-accordion`
- `p-inputText`
- `p-inputNumber`
- `p-dropdown` o `p-select`
- `p-calendar` o componente de fecha equivalente del proyecto
- `p-textarea`
- `p-button`
- `p-divider`
- `p-table` si hace falta vista resumida
- `p-checkbox` si se agregan toggles de seleccion


## Flujo funcional

### Pantalla 1: datos generales

Esta pantalla ya captura:

- cliente
- direccion
- fecha de recoleccion
- tipo

Estos campos corresponden a la entidad `laundry_services` v2.

Payload minimo recomendado para crear el servicio:

```json
{
  "client_id": 5,
  "client_address_id": 4,
  "scheduled_pickup_at": "2026-04-01T10:30:00",
  "status": "PENDING",
  "service_label": "NORMAL",
  "transaction_id": null,
  "weight_lb": null,
  "notes": null,
  "items": [],
  "extras": []
}
```

Endpoint:

- `POST /v2/laundry_services`

Comportamiento esperado:

- Al guardar esta pantalla, crear el servicio.
- Conservar el `id` del servicio creado.
- Navegar a la Pantalla 2 usando ese `id`.


### Pantalla 2: detalle operativo

En esta pantalla se completan:

- peso en libras
- observaciones
- prendas por conteo
- piezas especiales con precio fijo
- extras

Esta pantalla debe actualizar el mismo servicio creado en la Pantalla 1.

Endpoint principal:

- `PUT /v2/laundry_services/:id`

Notas importantes:

- `items` reemplaza la lista actual completa cuando se envia.
- `extras` reemplaza la lista actual completa cuando se envia.
- Si el frontend hace edicion parcial, debe enviar la lista consolidada final, no solo diffs.


## Modelo conceptual actual del backend

Hoy existen 2 mundos funcionales:

### 1. Mundo operativo: `laundry_services`

Se usa para recepcion y seguimiento del servicio.

Incluye:

- cliente
- direccion
- fecha de recoleccion
- tipo de servicio (`NORMAL` o `EXPRESS`)
- peso
- observaciones
- prendas por conteo
- extras

Catalogos asociados:

- `GET /v2/garment_types`
- `GET /v2/service_extra_types`


### 2. Mundo comercial: `services`

Se usa para catalogo de servicios especiales o cobros fijos.

Catalogos asociados:

- `GET /v2/services`
- `GET /v2/service_categories`
- `GET /v2/service-price-options`

Aqui viven servicios como:

- alfombras
- tapetes de bano
- vestidos formales
- zapatos
- planchado
- mochilas


## Decision de UI recomendada

En la Pantalla 2 usar 3 acordeones principales:

1. `Prendas por conteo`
2. `Piezas especiales con precio fijo`
3. `Extras`

Ademas, arriba de los acordeones:

- campo `weight_lb`
- campo `notes`


## Acordeon 1: Prendas por conteo

Fuente:

- `GET /v2/garment_types`

Agrupar por `category`:

- `CLOTHING`
- `BEDDING`
- `HOUSEHOLD`
- `RUG`
- `PLUSH`
- `FOOTWEAR`

Cada item del catalogo debe mostrar:

- nombre
- cantidad
- unidad por defecto
- precio unitario opcional
- observacion opcional

Estructura sugerida en estado:

```ts
type LaundryCountItemForm = {
  garment_type_id: number;
  name: string;
  category: string;
  quantity: number | null;
  unit_type: 'UNIT' | 'PAIR';
  unit_price: number | null;
  notes: string | null;
};
```

Regla de serializacion:

- Solo enviar al backend los items con `quantity > 0`.

Payload esperado dentro de `items`:

```json
[
  {
    "garment_type_id": 1,
    "quantity": 10,
    "unit_type": "UNIT",
    "unit_price": null,
    "notes": "Camisas blancas"
  }
]
```


## Acordeon 2: Piezas especiales con precio fijo

Fuente:

- `GET /v2/services`

Agrupar por categoria comercial:

- Hogar y volumen
- Ropa formal
- Accesorios
- Lavado por peso
- Planchado

Ejemplos reales del catalogo:

- Alfombras
- Tapetes de bano
- Peluches
- Almohadas
- Edredones
- Cortinas
- Vestidos formales
- Zapatos
- Mochilas
- Gorras
- Planchado de ropa

Importante:

- Este catalogo pertenece al mundo comercial.
- No existe hoy una relacion directa dentro de `PUT /v2/laundry_services` para guardar estas piezas especiales como parte de `items`.
- Por ahora el frontend puede capturarlas en estado UI y dejarlas listas para futura integracion comercial.

Recomendacion de implementacion:

- Mostrar este acordeon desde ya.
- Permitir seleccionar servicio, cantidad, precio sugerido y observaciones.
- Marcar internamente esta seccion como `pendiente de persistencia comercial`.

Estructura sugerida:

```ts
type FixedPriceSpecialItemForm = {
  service_id: number;
  service_name: string;
  category_name: string;
  quantity: number | null;
  selected_price_option_id?: number | null;
  manual_price?: number | null;
  notes?: string | null;
};
```

Si mas adelante se conecta con el flujo comercial, esto probablemente terminara persistiendo en `orders`.


## Acordeon 3: Extras

Fuente:

- `GET /v2/service_extra_types`

Ejemplos existentes:

- Planchado
- Perlitas de olor
- Remojo
- Vinagre
- Sal
- Vanish

Cada fila debe permitir:

- activar/agregar extra
- cantidad
- precio unitario opcional
- observaciones

Estructura sugerida:

```ts
type LaundryExtraForm = {
  service_extra_type_id: number;
  name: string;
  quantity: number | null;
  unit_price: number | null;
  notes: string | null;
};
```

Regla de serializacion:

- Solo enviar extras con `quantity > 0`.

Payload esperado dentro de `extras`:

```json
[
  {
    "service_extra_type_id": 2,
    "quantity": 1,
    "unit_price": null,
    "notes": "Aplicar en toda la ropa"
  }
]
```


## Payload recomendado para Pantalla 2

```json
{
  "weight_lb": 18.5,
  "notes": "Cliente solicita cuidado especial con prendas blancas.",
  "items": [
    {
      "garment_type_id": 1,
      "quantity": 12,
      "unit_type": "UNIT",
      "unit_price": null,
      "notes": "Camisas"
    },
    {
      "garment_type_id": 2,
      "quantity": 8,
      "unit_type": "UNIT",
      "unit_price": null,
      "notes": "Pantalones"
    }
  ],
  "extras": [
    {
      "service_extra_type_id": 6,
      "quantity": 1,
      "unit_price": null,
      "notes": "Agregar al lavado"
    }
  ]
}
```


## Estrategia de carga inicial

Al entrar a la Pantalla 2:

1. Leer el servicio actual por `id`.
2. Cargar catalogo de prendas.
3. Cargar catalogo de extras.
4. Cargar catalogo de servicios especiales.
5. Hacer merge entre datos existentes del servicio y catalogos base para hidratar el formulario.

Endpoints:

- `GET /v2/laundry_services/:id`
- `GET /v2/garment_types`
- `GET /v2/service_extra_types`
- `GET /v2/services`


## Reglas de UX

- Mantener visible un resumen superior con:
  - cliente
  - direccion
  - fecha de recoleccion
  - tipo
- Mostrar `peso` y `observaciones` antes de los acordeones.
- Cada acordeon debe mostrar badge o contador de items seleccionados.
- Permitir colapsar y expandir por grupo.
- En `Prendas por conteo`, agrupar visualmente por categoria.
- En `Piezas especiales con precio fijo`, mostrar precio sugerido si existe.
- En `Extras`, dejar campos rapidos de cantidad para captura operativa.
- Agregar validacion para evitar guardar cantidades negativas o cero cuando el item esta activo.


## Reglas tecnicas para Angular

- Usar Reactive Forms.
- Modelar cada acordeon con `FormArray`.
- Centralizar catalogos en servicios Angular.
- No hardcodear listas de prendas ni extras si ya vienen del backend.
- Usar interfaces o types para separar:
  - datos del catalogo
  - datos del formulario
  - payloads de API

Servicios Angular sugeridos:

- `LaundryServicesApiService`
- `GarmentTypesApiService`
- `ServiceExtraTypesApiService`
- `CommercialServicesApiService`


## Reglas de estilos

- La UI debe construirse con PrimeNG v19.
- Aplicar la base visual disponible en `node_modules/drstyles`.
- Reutilizar variables, mixins, utilidades o clases del paquete `drstyles` antes de crear CSS nuevo.
- Mantener una apariencia consistente con el resto del sistema.
- Evitar estilos inline salvo casos muy puntuales.


## Riesgo funcional actual

La seccion `Piezas especiales con precio fijo` todavia no tiene persistencia natural dentro de `laundry_services`.

Por eso, de momento:

- `Prendas por conteo` y `Extras` si deben persistirse en `PUT /v2/laundry_services/:id`.
- `Piezas especiales con precio fijo` puede quedar inicialmente como captura preparada para futura integracion comercial.

Si el producto decide que tambien deben guardarse ya mismo, habra que definir una de estas 2 opciones:

1. Extender `laundry_services` para soportarlas.
2. Integrarlas con el flujo comercial de `orders`.


## Resumen de endpoints para frontend

- `POST /v2/laundry_services`
- `PUT /v2/laundry_services/:id`
- `GET /v2/laundry_services/:id`
- `GET /v2/garment_types`
- `GET /v2/service_extra_types`
- `GET /v2/services`


## Resultado esperado

El frontend debe permitir:

- crear un servicio basico en la Pantalla 1
- completar detalle operativo en la Pantalla 2
- capturar peso y observaciones
- capturar prendas por conteo por categoria
- capturar extras
- preparar la UI para piezas especiales con precio fijo
- usar acordeones con PrimeNG v19
- mantener consistencia visual con `node_modules/drstyles`
