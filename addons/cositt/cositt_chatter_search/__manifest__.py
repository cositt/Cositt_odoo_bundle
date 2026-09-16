{
    "name": "Cositt Chatter Search",
    "version": "19.0.1.0.0",
    "summary": "Añade búsqueda por autor al buscador nativo del chatter",
    "description": """
Odoo 19 ya trae un buscador de mensajes integrado en el chatter (icono de
lupa, arriba a la derecha de cualquier chatter), con paginación real en
servidor, que busca en cuerpo, asunto, adjuntos y valores de seguimiento
de cualquier modelo con mail.thread. Lo único que no busca es el autor
del mensaje. Este módulo amplía ese buscador nativo (sin tocar ninguna
plantilla ni componente OWL) para que el mismo cuadro de búsqueda
encuentre también mensajes por nombre de autor (usuario/contacto),
remitente de email (mensajes entrantes sin contacto vinculado) o
nombre de invitado (mail.guest, p.ej. chat de portal/website).
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Discuss",
    "license": "LGPL-3",
    "depends": ["mail"],
    "data": [],
    "installable": True,
    "application": False,
}
