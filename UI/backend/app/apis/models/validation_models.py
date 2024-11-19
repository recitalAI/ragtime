# validation_models.py
from marshmallow import Schema, fields, validate

class FactSchema(Schema):
    meta = fields.Dict(missing=dict)
    text = fields.Str(required=True)

class ValidationSetItemSchema(Schema):
    question = fields.Dict(required=True, keys=fields.Str(), values=fields.Str())
    facts = fields.Dict(required=True, keys=fields.Str(), values=fields.List(fields.Nested(FactSchema)))

class ValidationSetSchema(Schema):
    meta = fields.Dict(missing=dict)
    items = fields.List(fields.Nested(ValidationSetItemSchema), required=True)

class ValidationSetStatsSchema(Schema):
    name = fields.Str()
    date = fields.Str()
    questions = fields.Int()
    facts = fields.Int()
    chunks = fields.Int()
    answers = fields.Int()
    human_eval = fields.Int()
    auto_eval = fields.Int()
    models = fields.Int()

class MessageResponseSchema(Schema):
    message = fields.Str(description="Response message")