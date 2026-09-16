{
    "name": "Cositt Attachment Lock",
    "version": "19.0.1.0.0",
    "summary": "Bloquea el borrado de adjuntos mientras la protección esté activada",
    "description": """
Interruptor global (Ajustes > Técnico > Parámetros del sistema,
`cositt_attachment_lock.enabled`): mientras esté en `True`, ningún
usuario normal puede eliminar un adjunto vinculado a un registro
(factura, contacto, proyecto...), ni desde la interfaz ni por RPC
directo — el bloqueo vive en el propio `unlink()` de ir.attachment, no
en un botón oculto. Los administradores (grupo "Ajustes", vía el grupo
`Cositt Attachment Lock / Puede eliminar adjuntos protegidos`, implicado
automáticamente) siguen pudiendo eliminar adjuntos. No afecta a
adjuntos técnicos (paquetes de assets, campos binarios auto-generados,
adjuntos temporales sin registro vinculado) ni a ninguna operación
interna de Odoo que ya se ejecuta con sudo.
""",
    "author": "Cositt Technology",
    "website": "https://www.cositt.com",
    "category": "Productivity",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [
        "security/security.xml",
        "data/ir_config_parameter.xml",
    ],
    "installable": True,
    "application": False,
}
