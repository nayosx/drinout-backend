# Angular Frontend Work Sessions Guide

Guia para Angular sobre el modulo visual de control de horas y jornadas de usuarios.

Este brief esta pensado para implementarse con:

- Angular
- PrimeNG
- `node_modules/drstyles`
- un calendario visual con vista semana y mes

## Objetivo

Construir una experiencia visual para que el usuario de la plataforma pueda:

- ver si tiene una jornada activa
- iniciar y finalizar jornada
- ver sus horas trabajadas del dia
- revisar su control de horas en vista semanal
- revisar su control de horas en vista mensual
- ver rapidamente horas extra y horas faltantes
- consultar historial de jornadas

Para perfiles administrativos:

- ver jornadas de cualquier usuario
- filtrar por usuario
- cerrar jornadas manualmente
- consultar reporte resumido
- descargar CSV

## Endpoints reales del backend

### Login

Usar:

- `POST /auth/login`

Body:

```json
{
  "username": "string",
  "password": "string"
}
```

Respuesta:

```json
{
  "message": "Login successful",
  "access_token": "jwt",
  "refresh_token": "jwt",
  "user": {
    "id": 1,
    "username": "admin",
    "role_id": 1,
    "name": "Nombre Usuario",
    "phone": "7777-7777",
    "created_at": "2026-04-05T08:00:00-06:00",
    "updated_at": "2026-04-05T08:00:00-06:00"
  }
}
```

### Iniciar jornada

Usar:

- `POST /work_sessions/start`

Sin body.

Respuesta exitosa:

```json
{
  "message": "Jornada iniciada",
  "session": {
    "id": 10,
    "user_id": 3,
    "login_time": "2026-04-05T08:00:00-06:00",
    "logout_time": null,
    "status": "IN_PROGRESS",
    "comments": null
  }
}
```

Si ya existe una jornada activa:

```json
{
  "message": "Ya tienes una jornada en curso."
}
```

### Finalizar jornada

Usar:

- `POST /work_sessions/end`

Sin body.

Respuesta exitosa:

```json
{
  "message": "Jornada finalizada",
  "session": {
    "id": 10,
    "user_id": 3,
    "login_time": "2026-04-05T08:00:00-06:00",
    "logout_time": "2026-04-05T17:30:00-06:00",
    "status": "COMPLETED",
    "comments": null
  }
}
```

Si no tiene jornada activa:

```json
{
  "message": "No tienes una jornada activa."
}
```

### Ultima jornada del usuario logueado

Usar:

- `GET /work_sessions/latest`

Respuesta:

```json
{
  "session": {
    "id": 10,
    "user_id": 3,
    "login_time": "2026-04-05T08:00:00-06:00",
    "logout_time": null,
    "status": "IN_PROGRESS",
    "comments": null
  }
}
```

Si no existen registros:

```json
{
  "message": "No hay sesiones registradas"
}
```

### Historial de jornadas

Usar:

- `GET /work_sessions`

Query params opcionales:

- `user_id`
- `start_date=YYYY-MM-DD`
- `end_date=YYYY-MM-DD`

Respuesta:

```json
[
  {
    "id": 10,
    "user_id": 3,
    "login_time": "2026-04-05T08:00:00-06:00",
    "logout_time": "2026-04-05T17:30:00-06:00",
    "status": "COMPLETED",
    "comments": null
  }
]
```

### Cierre manual para admin

Usar:

- `POST /work_sessions/force_end`

Body:

```json
{
  "user_id": 3,
  "comments": "Cierre manual por olvido de marcacion"
}
```

Respuesta:

```json
{
  "message": "Work session forcibly closed",
  "session": {
    "id": 10,
    "user_id": 3,
    "login_time": "2026-04-05T08:00:00-06:00",
    "logout_time": "2026-04-05T18:00:00-06:00",
    "status": "COMPLETED",
    "comments": "Cierre manual por olvido de marcacion"
  }
}
```

### Reporte por rango

Usar:

- `GET /work_sessions/report?start_date=2026-04-01&end_date=2026-04-30`

Respuesta:

```json
{
  "daily_target_time": "09:00:00",
  "report": [
    {
      "user_id": 3,
      "nombre_usuario": "Juan Perez",
      "total_sesiones": 20,
      "total_duracion": "190:30:00",
      "total_extra": "05:00:00",
      "total_faltante": "01:30:00"
    }
  ]
}
```

### Descargar CSV

Usar:

- `GET /work_sessions/report?start_date=2026-04-01&end_date=2026-04-30&download_csv=true`

### Usuarios para filtros

Usar:

- `GET /users?lite=true`

Respuesta:

```json
[
  { "id": 1, "name": "Admin" },
  { "id": 3, "name": "Juan Perez" }
]
```

## Reglas de negocio

- Una jornada activa tiene `status = "IN_PROGRESS"` y `logout_time = null`
- Una jornada cerrada tiene `status = "COMPLETED"`
- La meta diaria debe leerse de `GET /v2/global-settings/work_session_daily_target_time`
- Si ese parametro no se consulta en frontend, usar temporalmente `09:00:00`
- El backend trabaja en UTC internamente pero serializa fechas a `America/El_Salvador`
- El frontend debe respetar esas fechas y no romperlas por conversiones innecesarias
- Si `GET /work_sessions/latest` devuelve una sesion `IN_PROGRESS`, el usuario esta trabajando

Global sugerido:

- `work_session_daily_target_time = "09:00:00"`

## Consideraciones del frontend ya implementado

El backend debe asumir este contrato visual ya existente:

- `Mi jornada` es solo para el usuario autenticado
- la vista personal cruza `GET /work_sessions/latest` y `GET /work_sessions`
- el frontend considera activa una sesion cuando:
  - `status = "IN_PROGRESS"`
  - `logout_time = null`
- el frontend no debe mezclar jornadas de otros usuarios en la vista personal
- la UI muestra `message` del backend cuando viene en respuesta
- el frontend ya tiene loaders y bloqueo de acciones criticas en iniciar/finalizar/cierre manual

Implicacion para backend:

- mantener `message` en respuestas exitosas y errores funcionales
- no cambiar los nombres actuales de campos
- no cambiar la regla de sesion activa
- cualquier dato adicional debe ser aditivo y no romper respuestas existentes

## Librerias recomendadas

Para que la experiencia sea visual en semana y mes, agregar estas librerias:

```bash
npm install @fullcalendar/angular @fullcalendar/core @fullcalendar/daygrid @fullcalendar/timegrid @fullcalendar/interaction dayjs
```

Notas:

- `FullCalendar` se recomienda para la vista visual semanal y mensual
- `dayjs` se recomienda para calculo de duraciones, agrupacion por dia, semana y mes
- Para filtros de fecha usar componentes de PrimeNG
- Si el proyecto ya usa otra libreria de fechas consistente, se puede mantener, pero no reinventar la vista calendario manualmente

## Objetivo de UI

Quiero una UI mas visual que administrativa.

La experiencia debe sentirse como un panel personal de productividad y asistencia, no solo como una tabla cruda.

La vista principal debe ayudar al usuario a responder rapido:

- si hoy ya entro
- cuantas horas lleva hoy
- como va su semana
- como va su mes
- si tiene horas extra o faltantes

## Stack visual esperado

Usar:

- componentes PrimeNG
- estilos base del proyecto desde `node_modules/drstyles`
- cards, tabs, badges, chips, toolbar, paneles y tablas de PrimeNG
- calendario visual para semana y mes

Evitar:

- pantallas planas o demasiado CRUD
- solo una tabla sin resumen visual
- layouts genericos sin jerarquia visual

## Pantallas y componentes a construir

### 1. Pantalla Mi Jornada

Pantalla principal del usuario autenticado.

Debe incluir:

- card superior con estado actual
- texto grande:
  - `Jornada activa`
  - `Sin jornada activa`
- hora de entrada
- hora de salida si ya finalizo
- contador en tiempo real si esta activa
- botones:
  - `Iniciar jornada`
  - `Finalizar jornada`
- resumen rapido del dia:
  - horas trabajadas hoy
  - diferencia contra meta diaria de 9h

Comportamiento:

- al entrar consultar `GET /work_sessions/latest`
- si hay sesion activa, mostrar contador vivo actualizandose cada segundo o cada minuto
- deshabilitar botones durante requests
- mostrar mensajes del backend con toast o mensaje inline

### 2. Vista Semanal

Debe mostrar una semana visual con enfoque en control de horas.

Puede ser:

- calendario semanal tipo time grid
- o cards por dia si el equipo decide complementar el calendario

Cada dia debe mostrar:

- hora de entrada
- hora de salida
- total del dia
- estado
- indicador visual:
  - completo
  - incompleto
  - activo
  - sin registro

Resumen semanal:

- total trabajado en la semana
- horas extra
- horas faltantes
- cantidad de jornadas registradas

### 3. Vista Mensual

Debe mostrar el mes en formato calendario visual.

Cada dia debe poder reflejar:

- si hubo jornada
- cuantas horas se trabajaron
- si hubo horas extra o faltantes

Interaccion esperada:

- click en un dia para abrir detalle
- colores suaves y claros para estados
- leyenda visual para interpretar los colores

Estados sugeridos:

- verde: jornada completa o dentro de objetivo
- azul: jornada activa
- amarillo: jornada corta o incompleta
- gris: sin registro

### 4. Historial de jornadas

Tabla con filtros.

Columnas:

- ID
- Fecha
- Hora entrada
- Hora salida
- Estado
- Comentarios
- Duracion

Filtros:

- fecha inicio
- fecha fin
- usuario si el perfil tiene acceso admin

UI sugerida:

- `p-table`
- `p-datepicker`
- `p-dropdown` o `p-select` para usuarios
- `p-tag` para estado

### 5. Reporte de horas

Pantalla de resumen por rango.

Debe incluir:

- filtros de fecha
- tabla resumen
- KPIs arriba
- boton de descargar CSV

KPIs sugeridos:

- total sesiones
- total horas
- total extra
- total faltante

Tabla:

- Usuario
- Total sesiones
- Total duracion
- Horas extra
- Horas faltantes

### 6. Cierre manual admin

Formulario simple:

- selector de usuario
- textarea para comentario
- boton `Cerrar jornada`
- confirmacion antes de enviar

## Arquitectura Angular sugerida

Crear:

- `work-sessions-api.service.ts`
- `work-session-status.service.ts` o signal store equivalente
- `work-sessions-history.service.ts`
- `work-sessions-report.service.ts`

Crear modulos o features como:

- `pages/work-sessions/my-work-session`
- `pages/work-sessions/work-session-calendar`
- `pages/work-sessions/work-session-history`
- `pages/work-sessions/work-session-report`
- `pages/work-sessions/admin-force-close`

Modelos sugeridos:

```ts
export interface WorkSession {
  id: number;
  user_id: number;
  login_time: string;
  logout_time: string | null;
  status: 'IN_PROGRESS' | 'COMPLETED';
  comments: string | null;
}

export interface WorkSessionsReportRow {
  user_id: number;
  nombre_usuario: string;
  total_sesiones: number;
  total_duracion: string;
  total_extra: string;
  total_faltante: string;
}

export interface LiteUser {
  id: number;
  name: string;
}
```

## Adaptadores para calendario

Convertir jornadas a eventos visuales para `FullCalendar`.

Sugerencia:

```ts
const event = {
  id: String(session.id),
  title: buildSessionTitle(session),
  start: session.login_time,
  end: session.logout_time ?? session.login_time,
  allDay: false,
  extendedProps: {
    session
  }
};
```

Titulo sugerido del evento:

- `08:00 - 17:30`
- `08:00 - Activa`
- `9h 15m trabajadas`

## Reglas visuales sugeridas

Si una jornada esta activa:

- resaltar con badge azul
- mostrar contador en vivo
- mostrar boton primario de finalizar

Si una jornada ya termino:

- mostrar duracion total
- marcar si supero o no la meta diaria

Si no hay registro en un dia:

- mostrar estado vacio sin ruido visual

Si el usuario supera la jornada objetivo:

- marcar horas extra en verde

Si el usuario queda corto:

- marcar faltante en naranja o amarillo

## Requisitos tecnicos

- usar `Authorization: Bearer <access_token>` en todos los endpoints protegidos
- refrescar estado despues de iniciar o finalizar jornada
- manejar `401`, `400` y `404`
- mostrar estados de carga
- mostrar estados vacios amigables
- no inventar endpoints
- respetar nombres reales de campos del backend
- calcular duracion en frontend si la sesion sigue activa
- agrupar jornadas por dia para la vista semanal y mensual

## Requisitos de experiencia de usuario

- mobile first pero bien resuelto en desktop
- panel principal con resumen claro
- visualizacion rapida de progreso semanal
- visualizacion intuitiva del mes
- detalles visibles sin demasiados clicks
- feedback claro al iniciar y cerrar jornada

## Componentes PrimeNG sugeridos

- `p-card`
- `p-toolbar`
- `p-button`
- `p-tag`
- `p-chip`
- `p-divider`
- `p-table`
- `p-datepicker`
- `p-dropdown` o el selector equivalente del proyecto
- `p-dialog`
- `p-confirmDialog`
- `p-toast`
- `p-skeleton`
- `p-tabView` o tabs equivalentes

## Integracion con drstyles

Usar `drstyles` para:

- tipografia
- espaciados
- grillas
- cards
- colores semanticos del proyecto

La pantalla debe sentirse parte de la plataforma actual.

No crear un tema desconectado del resto del sistema.

## Prompt recomendado para implementar

```text
Implementa en Angular un modulo visual de control de horas y jornadas usando PrimeNG, drstyles y FullCalendar.

Debe consumir estos endpoints reales:
- POST /work_sessions/start
- POST /work_sessions/end
- POST /work_sessions/force_end
- GET /work_sessions/latest
- GET /work_sessions
- GET /work_sessions/report
- GET /users?lite=true

Requisitos:
- pantalla principal "Mi jornada" con estado actual, contador en vivo, hora de entrada, resumen diario y botones de iniciar/finalizar
- vista semanal visual
- vista mensual visual
- historial filtrable
- reporte con KPIs y descarga CSV
- cierre manual para admin

Usa FullCalendar para semana y mes.
Usa PrimeNG para cards, tablas, datepickers, dialogs, toast y tags.
Usa drstyles para que la UI mantenga la identidad visual del proyecto.

No inventes endpoints.
Respeta los nombres reales de campos:
- id
- user_id
- login_time
- logout_time
- status
- comments

Estados reales:
- IN_PROGRESS
- COMPLETED

La API ya entrega fechas en America/El_Salvador.
Mostrar mensajes del backend tal como vengan cuando sea posible.

Agregar una experiencia visual clara para que el usuario vea como va en su semana y su mes respecto a su control de horas.
```

## Nota final

Priorizar una UX visual y clara antes que una implementacion centrada solo en tablas.

La tabla sirve como apoyo, pero el valor principal de esta funcionalidad debe estar en:

- panel personal
- calendario semanal
- calendario mensual
- resumenes de horas faciles de entender
