# Cómo añadir funcionalidad a CRITERIUM COMPÁS sin tocar el fork

## La regla

> **En el fork solo entra la marca. Todo lo demás va por fuera.**

El monorepo de Twenty son ~500k líneas con 300 colaboradores detrás. Cada línea nuestra dentro
de su código es una línea que pagamos en cada actualización (conflictos, regresiones, CVE).
La marca son ~15 ficheros y se rebasa en minutos; una funcionalidad incrustada no.

Twenty ya trae los dos puntos de extensión que necesitamos: **objetos propios** (modelo de
datos a medida desde la interfaz o por API) y **API completa** (GraphQL, REST y webhooks)
para leer/escribir desde nuestros sistemas. Todo lo que hace Compás hoy —señal, cadencia,
Telegram— puede vivir en un servicio nuestro que hable con COMPÁS por API.

## Vía 1 — Objetos y campos desde la interfaz

`Ajustes → Modelo de datos → Nuevo objeto`. Así se creó «Negocios» y su campo «Fase»
(select con las 8 fases de la captación). Cada campo nuevo aparece al momento en tabla,
vista kanban, filtros y buscador, sin desplegar nada.

## Vía 2 — API

Los endpoints del servidor:

| Endpoint | Para qué |
|---|---|
| `POST /graphql` | registros: consultas y mutaciones (`negocios`, `createNegocios`, …) |
| `POST /metadata` | modelo: crear objetos y campos por código |
| `GET/POST /rest/*` | lo mismo que graphql en REST (`/rest/negocios`) |
| Webhooks | `Ajustes → MCP y API → Webhooks`: aviso HTTP a nuestros servicios en cada alta/cambio |

**Autenticación**: API key desde `Ajustes → MCP y API` → `Authorization: Bearer <key>`.
La key se guarda en el Llavero (`~/.secrets/kc set pruebas/twenty/API_KEY`), nunca en un
`.env` del repo ni en un chat.

Ejemplo real — así se cargaron los 54 leads (script completo en `scripts/importar-leads.py`):

```graphql
mutation($data:[NegocioCreateInput!]!) {
  createNegocios(data:$data) { id slug }
}
```

con `data` = lista de `{name, slug, fase, prioridad, queTieneHoy, gancho, demo:{primaryLinkUrl}, comercial, zona, municipio, notaGoogle}`.

Y los campos se crearon por `/metadata`:

```graphql
mutation($input:CreateOneFieldMetadataInput!) {
  createOneField(input:$input) { id name }
}
```

## Qué NO hacer

- No añadir pantallas, rutas ni componentes al front de Twenty.
- No tocar el servidor NestJS ni sus migraciones.
- Si parece que «hace falta tocar el núcleo», parar y buscar la vía API — casi siempre existe
  (workflows nativos, webhooks + servicio propio, o un objeto con campos calculados fuera).
- La única excepción viva es la rama `marca/criterium-compas`, y solo para marca.

## El puente con Compás

La base de Compás (`compas-nexia`) es la fuente de verdad mientras dure la evaluación.
De ella **solo se lee**. El volcado se repite con `scripts/importar-leads.py` (idempotente
por slug: borra e importa, o filtra los existentes).
