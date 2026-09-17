{
    "name": "Cositt Report Watermark",
    "version": "19.0.1.0.0",
    "summary": "Marca de agua de texto configurable en todos los reportes PDF",
    "description": """
Superpone un texto de marca de agua (ej. "BORRADOR", "COPIA",
"CONFIDENCIAL") en TODOS los reportes PDF del sistema, con opacidad y
rotación configurables — sin tocar ningún reporte individual.

Se ancla en `web.report_layout`, la plantilla raíz que envuelve
absolutamente todo reporte QWeb-PDF (facturas, presupuestos, albaranes,
reportes técnicos...) independientemente del estilo de encabezado/pie
que la compañía tenga elegido (standard, boxed, bold...). El texto se
pinta con `position: fixed` en CSS — un truco bien documentado de
wkhtmltopdf (el motor de PDF de Odoo): un elemento fixed dentro del
body se repite en TODAS las páginas generadas, sin necesitar tocar el
mecanismo de header/footer.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/report_templates.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "cositt_report_watermark/static/src/report/report_watermark.scss",
        ],
    },
    "installable": True,
    "application": False,
}
