# Cositt Email Domain Helper

## Qué hace

Calcula el dominio de email de cada contacto (`pedro@acme.com` → `acme.com`)
y ofrece dos ayudas a partir de ese dato:

- Un botón junto al email de una persona de contacto para vincularla
  automáticamente a la empresa existente que use ese mismo dominio.
- Una vista agrupada por dominio en Contactos, para detectar de un vistazo
  qué empresas comparten dominio de email (señal habitual de duplicados o
  de la misma organización dada de alta más de una vez).

## Problema que resuelve

Al dar de alta contactos a mano (o importarlos), es fácil que una persona
quede sin vincular a su empresa, o que la misma empresa termine creada dos
veces con nombres ligeramente distintos. El dominio de email es una pista
fiable para detectar ambos casos sin depender de que el usuario recuerde
buscarlo manualmente.

## Instalación

Módulo estándar Odoo: copiar en `addons/cositt/` e instalar desde
Aplicaciones. Sin dependencias externas, sin configuración.

## Configuración

Ninguna.

## Uso

Manual con capturas de pantalla: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

En la ficha de una persona de contacto con email, aparece un botón junto
al campo Email (icono de edificio). Al pulsarlo:

- Si hay exactamente una empresa con ese mismo dominio, vincula el
  contacto a ella.
- Si el dominio es de un proveedor de email genérico (Gmail, Outlook...),
  avisa de que no identifica una empresa concreta.
- Si no hay ninguna empresa con ese dominio, si hay varias, o si el
  contacto ya está vinculado a otra empresa, avisa con un mensaje claro en
  vez de adivinar o sobrescribir el vínculo existente.

Desde Contactos → menú "Dominios de email duplicados" se listan las
empresas con dominio de email conocido, agrupadas por dominio: las que
comparten grupo son candidatas a revisión manual (duplicado, o
sencillamente varias empresas del mismo grupo que comparten dominio
corporativo).

## Dependencias

- Community: sí, funciona igual en Community.
- Enterprise: no requerido.
- Python / APIs externas: ninguna. Todo el cálculo es local, reutiliza
  `odoo.tools.email_domain_extract` del propio core de Odoo.

## Seguridad

No añade modelos, ACL ni reglas de registro nuevas: usa el modelo
`res.partner` con los permisos y el aislamiento multiusuario que Odoo ya
aplica de forma nativa sobre contactos.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- La lista de proveedores de email genéricos (`FREE_EMAIL_DOMAINS`) es
  manual y orientada al mercado español; no es exhaustiva.
- Si varias empresas distintas comparten el mismo dominio de email
  legítimamente (p.ej. filiales de un mismo grupo), el botón no vincula
  automáticamente y pide revisión manual — es una limitación deliberada
  para no adivinar en casos ambiguos.
