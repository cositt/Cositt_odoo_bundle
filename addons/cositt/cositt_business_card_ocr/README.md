# Cositt Business Card OCR

## Qué hace

Escanea una foto de tarjeta de visita, extrae los datos de contacto mediante OCR
local (Tesseract, sin enviar la imagen a ningún servicio externo) y deja que el
usuario revise/corrija los datos antes de crear un contacto en Odoo o añadirlo
como persona de contacto de una empresa existente. Antes de confirmar, avisa si
detecta un posible contacto duplicado (por email o teléfono/móvil).

## Problema que resuelve

Dar de alta contactos a partir de tarjetas de visita a mano es lento y genera
errores de transcripción. Este módulo automatiza la primera pasada, dejando al
usuario el control final.

## Instalación

1. Módulo estándar Odoo: copiar en `addons/cositt/` (ya montado por defecto en
   este proyecto) e instalar desde Aplicaciones.
2. Requiere el binario `tesseract-ocr` y las librerías Python `pytesseract` y
   `Pillow` en el servidor Odoo (ya incluidas en el `Dockerfile` de este
   proyecto).

## Configuración

Ninguna. Funciona nada más instalar.

## Uso

Manual con capturas de pantalla paso a paso: [`docs/manual_usuario.pdf`](./docs/manual_usuario.pdf).

1. Contactos → Escanear tarjeta → Nuevo.
2. Subir la foto de la tarjeta.
3. Pulsar "Extraer datos" y revisar/corregir los campos.
4. Si aparece aviso de duplicado, pulsar "Vincular a contacto existente"; si no,
   pulsar "Crear contacto" (opcionalmente indicando una empresa en "Añadir como
   contacto de" para crearlo como persona de esa empresa).

## Dependencias

- Community: sí (usa `res.partner` estándar).
- Enterprise: no requerido.
- Python: `pytesseract`, `Pillow`.
- Sistema: `tesseract-ocr` (+ paquete de idioma `tesseract-ocr-spa`).
- APIs externas: ninguna. Todo el procesamiento OCR es local.

## Seguridad

- Solo usuarios internos (`base.group_user`) pueden usar el modelo.
- Cada usuario ve únicamente sus propios escaneos; los administradores
  (grupo Ajustes/Técnico) los ven todos.
- La imagen se guarda como adjunto estándar de Odoo, con los permisos habituales.
- La imagen nunca sale del servidor: no hay llamadas a servicios externos.

## Compatibilidad

Odoo 19.0, Community y Enterprise.

## Limitaciones conocidas

- La extracción de nombre/empresa/cargo es heurística (basada en patrones de
  texto), no un modelo de IA: revisar siempre antes de confirmar.
- No se extraen ciudad/código postal/país por separado; se guardan como texto
  libre en "Dirección".
- Odoo 19 unificó "teléfono" y "móvil" en un único campo `phone` en
  `res.partner`. El escaneo conserva ambos valores por separado para revisión,
  pero al crear el contacto se usa el móvil si existe (si no, el fijo).
- La detección de duplicados por teléfono es más fiable si la compañía tiene
  un país configurado (Ajustes > Compañías) o si el número lleva prefijo de
  país (`+34...`); sin ninguno de los dos, solo detecta coincidencias exactas.
- La precisión depende de la calidad de la foto (enfoque, luz, ángulo).
