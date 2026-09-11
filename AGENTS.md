# AGENTS.md — contexto para agentes IA

## Objetivo del proyecto

"12 meses, 12 plugins para Odoo": Cositt Technology libera un módulo Odoo pequeño y
gratuito al mes. Colección final: "Cositt Essentials for Odoo". Prefijo técnico: `cositt_`.

## Arquitectura

- Odoo 19.0 vía Docker (imagen oficial `odoo:19.0`, Community incluida).
- Enterprise 19.0 montado en `/mnt/enterprise` desde `./enterprise/` (no se sube a git).
- Módulos propios en `/mnt/cositt` desde `./addons/cositt/`.
- PostgreSQL 16 en contenedor `db`, un solo volumen persistente.
- Base de desarrollo: `cositt_plugins_dev`. Nunca datos reales de clientes.

## Reglas absolutas

- **Nunca** tocar producción: sin credenciales de cliente, sin servidores externos,
  sin bases reales, sin despliegues fuera de este Docker local.
- **Nunca** modificar el core de Odoo ni los fuentes de `enterprise/`.
- **Nunca** subir `enterprise/`, `.env`, dumps o backups a git.
- Todo cambio de funcionalidad va en un módulo `cositt_xxx` independiente,
  instalable/desinstalable sin afectar al resto.
- Community + Enterprise siempre que sea posible. Si algo requiere Enterprise,
  documentarlo explícitamente en el README del módulo.

## Convenciones de módulo

```
cositt_xxxxx/
├── __init__.py
├── __manifest__.py
├── models/
├── views/
├── security/
├── data/
├── static/
├── tests/
└── README.md
```

- Solo crear las carpetas que el módulo realmente necesite.
- ORM de Odoo, evitar SQL directo.
- Evitar monkey patching y overrides completos de métodos: usar `super()`.
- Seguridad mínima necesaria (`ir.model.access.csv` + grupos si aplica).
- Un módulo, una función concreta y fácil de entender.
- README por módulo: qué hace, problema que resuelve, instalación, configuración,
  uso, dependencias, seguridad, compatibilidad, limitaciones.
- Tests automatizados cuando el módulo tenga lógica funcional relevante.
- Cada módulo debe entregar un **manual en PDF con capturas de pantalla reales**
  del flujo de uso completo (`docs/manual_usuario.pdf` dentro del propio módulo,
  enlazado desde su README). Se genera con capturas del navegador tomadas sobre
  el propio entorno de desarrollo (no mockups), convertidas a PDF (p.ej. Chrome
  headless `--print-to-pdf` sobre un HTML con las imágenes embebidas).

## Flujo de trabajo

El proyecto avanza mes a mes, un plugin cada vez. No desarrollar varios plugins en
paralelo salvo petición explícita. Antes de escribir código: analizar requisitos,
alternativas, arquitectura, seguridad y UX del plugin en curso.

## Criterio de decisión (en orden)

1. Compatibilidad Odoo estándar
2. Simplicidad
3. Estabilidad
4. Seguridad
5. Mantenibilidad
6. Facilidad de instalación
7. Community + Enterprise
8. Sin dependencias externas
9. Rendimiento
10. Sofisticación técnica
