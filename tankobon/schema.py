# coding: utf8
"""Schema validifier for tankobon manifests.
"""

try:
    import jsonschema
except ImportError:
    jsonschema = None

# Schema for manga metadata.
# It should be emitted in this format as JSON.
SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Manga",
    "description": "A manga/comic, hosted on a webserver.",
    "type": "object",
    "definitions": {
        "pages": {"type": "array", "items": {"type": "string"}},
        "chapter": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "url": {"type": "string"},
                "pages": {"$ref": "#/definitions/pages"},
            },
        },
    },
    "properties": {
        "title": {"type": "string"},
        "url": {"type": "string"},
        "chapters": {
            "type": "object",
            "propertyNames": {"pattern": "^([0-9]+(\\.[0-9])?)$"},
            "$ref": "#/definitions/chapter",
        },
    },
    "required": ["title", "url", "chapters"],
}
