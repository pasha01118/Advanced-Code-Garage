from pydantic import BaseModel, Field


class ProviderCatalogEntry(BaseModel):
    id: str
    name: str
    tagline: str
    description: str
    free_tier: str
    signup_url: str
    kind: str
    requires_key: bool


class ProviderCatalogListOut(BaseModel):
    providers: list[ProviderCatalogEntry] = []


class AIModelInfo(BaseModel):
    id: str
    context_length: int | None = None
    owned_by: str | None = None
    tags: list[str] | None = Field(default=None, description="Loose labels (e.g. `:free`) parsed from the model id.")


class AIModelListOut(BaseModel):
    provider: str
    cached: bool = False
    models: list[AIModelInfo] = []


class AIKeyStatus(BaseModel):
    provider: str
    has_key: bool = False
    status: str = "untested"
    message: str = ""
    model_count: int = 0
    last_validated_at: str | None = None


class AIKeyStatusListOut(BaseModel):
    entries: list[AIKeyStatus] = []


class AISaveKeyRequest(BaseModel):
    provider: str
    api_key: str | None = None
    ollama_base_url: str | None = None


class AIValidateOut(BaseModel):
    provider: str
    status: str
    message: str = ""
    model_count: int = 0
    models: list[AIModelInfo] = []


class AIDeleteOut(BaseModel):
    provider: str
    deleted: bool