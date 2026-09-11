# 12 meses, 12 plugins para Odoo

Colección de módulos pequeños y gratuitos para Odoo, desarrollados por Cositt Technology,
uno por mes. Prefijo técnico: `cositt_`.

Entorno **exclusivamente de desarrollo local**. Nunca producción, nunca datos de clientes.

## Stack

- Odoo **19.0** (Community vía imagen oficial `odoo:19.0` + Enterprise montado como volumen)
- PostgreSQL 16
- Docker Compose

## Estructura

```
.
├── docker-compose.yml
├── Dockerfile              # FROM odoo:19.0 (punto de extensión para deps futuras, ej. OCR)
├── config/odoo.conf
├── enterprise/              # Odoo Enterprise 19.0 (NO se sube a git, licenciado)
├── addons/cositt/           # Módulos propios Cositt (cositt_xxx)
├── scripts/
├── docs/
├── tests/
├── .env                     # credenciales dev, NO se sube a git
└── .env.example
```

## Levantar el entorno

```bash
cp .env.example .env   # si no existe ya
docker compose up -d
docker compose ps
docker compose logs -f odoo
```

Odoo queda accesible en [http://localhost:8079](http://localhost:8079) (puerto configurable
en `.env` vía `ODOO_PORT`).

## Crear base de desarrollo

Desde el asistente de creación de base de datos de Odoo (primera pantalla al entrar), o:

```bash
docker compose exec odoo odoo -d cositt_plugins_dev --db_host=db -i base --stop-after-init
```

Nombre sugerido: `cositt_plugins_dev`. Nunca usar dumps ni bases de clientes reales.

## Activar modo desarrollador

Ajustes → Activar el modo desarrollador (o añadir `?debug=1` a la URL).

## Actualizar un módulo Cositt

```bash
docker compose exec odoo odoo -d cositt_plugins_dev -u cositt_nombre_modulo --stop-after-init
docker compose restart odoo
```

Los módulos en `addons/cositt/` están montados como volumen: los cambios de código se
reflejan sin reconstruir la imagen (solo hace falta reiniciar/actualizar el módulo).

## Tests

```bash
docker compose exec odoo odoo -d cositt_plugins_dev --test-enable -i cositt_nombre_modulo --stop-after-init
```

## Buenas prácticas

- Un módulo, una función concreta.
- Community + Enterprise cuando sea posible; documentar si algo requiere Enterprise.
- No modificar core de Odoo ni los fuentes de Enterprise.
- No SQL directo salvo necesidad real; usar el ORM.
- Cada módulo con su propio README (ver plantilla en `docs/`).

Ver también [AGENTS.md](./AGENTS.md) y [CLAUDE.md](./CLAUDE.md) para contexto de agentes IA.
