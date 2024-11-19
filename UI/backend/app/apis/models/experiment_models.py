from marshmallow import Schema, fields, validate
from datetime import datetime
import json

class ExperimentListSchema(Schema):
    name = fields.Str(required=True)
    date = fields.Str(required=True)
    models = fields.List(fields.Str())
    questions = fields.Int()
    facts = fields.Int()
    chunks = fields.Int()
    retriever = fields.Str()
    results_path = fields.Str()
    validation_set = fields.Str()

class ExperimentSchema(Schema):
    meta = fields.Dict()
    items = fields.List(fields.Dict())

class ExperimentConfigSchema(Schema):
    name = fields.Str(required=True)
    validationSet = fields.Str(required=True)
    evaluationModel = fields.Str(required=True)
    answerGenerationModels = fields.List(fields.Str(), required=True)
    evaluateAnswers = fields.Bool(default=True)
    evaluateChunks = fields.Bool(default=False)
    useRetriever = fields.Bool(default=False)
    retrieverType = fields.Str(allow_none=True)
    validationSetData = fields.Dict()
    withCSV = fields.Bool(default=False)

class ExperimentResponseSchema(Schema):
    message = fields.Str(required=True)
    results_path = fields.Str(required=True)

class MessageResponseSchema(Schema):
    message = fields.Str(required=True)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
class ParameterSchema(Schema):
    name = fields.Str(required=True)
    required = fields.Bool(required=True)
    default = fields.Raw(allow_none=True)
    type = fields.Str(required=True)

class LLMInfoSchema(Schema):
    name = fields.Str(required=True)
    built_in_retriever = fields.Bool(default=False)
    description = fields.Str(allow_none=True)
    parameters = fields.List(fields.Nested(ParameterSchema), missing=[])

class RetrieverInfoSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str(allow_none=True)
    parameters = fields.List(fields.Nested(ParameterSchema), missing=[])