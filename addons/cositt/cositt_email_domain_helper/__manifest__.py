{
    "name": "Cositt Email Domain Helper",
    "version": "19.0.1.0.0",
    "summary": "Identifica el dominio de email de un contacto, sugiere su empresa y detecta dominios duplicados",
    "description": """
Al introducir el email de un contacto, calcula su dominio (p.ej.
"pedro@acme.com" -> "acme.com") y permite:

- Vincular el contacto a una empresa existente que use el mismo dominio,
  con un botón junto al email (excluye proveedores de email genéricos como
  Gmail u Outlook, que no identifican una empresa concreta).
- Revisar, agrupando por dominio desde Contactos, qué empresas comparten
  dominio de email: señal habitual de duplicados o de la misma
  organización dada de alta más de una vez.

Todo el cálculo es local (reutiliza odoo.tools.email_domain_extract del
propio core), sin consultar ningún servicio externo.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Contacts",
    "license": "LGPL-3",
    "depends": ["contacts"],
    "data": [
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
