# CRITERIUM COMPÁS

Fork de [Twenty CRM](https://github.com/twentyhq/twenty) con la marca de Criterium / Estudio Nexia.
**Uso estrictamente interno** del equipo comercial. No se revende ni se sirve a terceros.

## La regla que gobierna este fork

> **En el fork solo entra la marca. Todo lo demás va por fuera, por API y objetos propios.**

Cuanto más pequeño sea el diff contra upstream, más barata es cada actualización. Antes de tocar
el núcleo para una funcionalidad, mira `docs/COMO-EXTENDER.md`: casi siempre hay una vía por API.

La rama de marca es `marca/criterium-compas`; `main` se mantiene limpia siguiendo a upstream.

## Licencia (AGPL-3.0) — léelo antes de cambiar el plan

Twenty es AGPL-3.0. La obligación de publicar el código modificado nace al **servir el software a
terceros por red**. Para uso interno del equipo no aplica. **Si algún día esto se replica para otras
agencias o clientes, hay que revisar la licencia ANTES de desplegar** — publicar este fork o
negociar licencia comercial con Twenty. Que nadie lo olvide.

## Cómo traerse una actualización de upstream

```bash
git fetch upstream --tags
git checkout main && git merge --ff-only upstream/main   # main sigue a upstream, sin commits propios
git checkout marca/criterium-compas
git rebase main            # o: git merge main — reaplicar la marca encima
# conflictos esperables: README.md (quedarse con el nuestro: git checkout --ours README.md),
# es-ES.po y los ficheros de marca listados abajo. Son pocos y triviales.
```

Después: reconstruir la imagen (ver abajo) y probar en local antes de nada.

## Qué toca este fork (y nada más)

- `packages/twenty-ui/src/theme/constants/AccentDark.ts` y `AccentLight.ts` — acento esmeralda
- `packages/twenty-front/src/modules/auth/components/Logo.tsx` — lockup horizontal en la entrada
- `packages/twenty-front/index.html`, `public/manifest.json` — título, favicon, metas
- `public/images/icons/**`, `public/images/criterium-horizontal.svg`,
  `public/images/integrations/twenty-logo.svg` — activos de marca
- Textos «Twenty» visibles (SignInUp, NotFound, import, settings community/legal/enterprise)
- `src/locales/es-ES.po` — traducciones de esos textos
- `DefaultWorkspaceLogo.ts` — logo de workspace por defecto local, sin URL de Twenty

## Construir la imagen

```bash
docker build --target twenty -f packages/twenty-docker/twenty/Dockerfile -t criterium-compas:2.30 .
```

El compose de la instancia (en `~/DEV/pruebas/twenty/docker-compose.yml`) apunta a esta imagen.
