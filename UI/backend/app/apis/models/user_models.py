from marshmallow import Schema, fields

class ApiKeySchema(Schema):
    name = fields.Str(required=True, description="Name of the API key", example="OPENAI_API_KEY")
    value = fields.Str(required=True, description="Value of the API key", example="sk-...")

class ApiKeysUpdateSchema(Schema):
    apiKeys = fields.List(fields.Nested(ApiKeySchema), required=True, 
                         description="List of API keys to add or update")
    deletedKeys = fields.List(fields.Str(), required=False, 
                            description="List of API key names to delete")

class ApiKeyAvailabilitySchema(Schema):
    openai = fields.Bool(description="OpenAI API key availability status")
    mistral = fields.Bool(description="Mistral API key availability status")

class MessageResponseSchema(Schema):
    message = fields.Str(description="Response message")

class DefaultApiKeySchema(Schema):
    value = fields.Str(description="Default value for the requested API key")