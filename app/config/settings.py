from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    env: str = "dev"
    service_name: str = "mnp-service"
    version: str = "1.0.0"
    release_name: str = "technical-release"

    require_api_key: bool = False
    api_keys: str = "dev-key-123"

    # audit_backend: sqlite | postgres
    audit_backend: str = "sqlite"
    sqlite_path: str = "data/mnp.sqlite"
    postgres_dsn: str = "postgresql://mnp:mnp@localhost:5432/mnp"

    tenant_config_path: str = "app/config/tenants.yaml"

    # Basic masking for audit payloads.
    mask_sensitive_fields: bool = True
    sensitive_field_names: str = "password,token,api_key,authorization,cpf,email,phone,telefone,to"

    # Minimizacao de texto livre na auditoria (item 3): campos que podem
    # conter PII/dado sensivel sao substituidos por hash + comprimento, em
    # vez do conteudo bruto. Preserva auditabilidade (prova de qual texto
    # foi processado) sem reter o dado sensivel no banco de auditoria.
    minimize_free_text: bool = True
    free_text_field_names: str = "user_text,text,goal,prompt,message,draft_text"
    # Pepper por deployment: torna o hash nao trivialmente reversivel por
    # tabelas de frases comuns. Defina MNP_AUDIT_TEXT_HASH_SALT em producao.
    audit_text_hash_salt: str = "change-me-in-production"

    # Fact extraction settings
    default_fact_extractor: str = "heuristic"  # heuristic | llm_mock | openai_compatible
    fact_confidence_threshold: float = 0.70
    human_review_path: str = "data/human_review.jsonl"

    # OpenAI-compatible extraction adapter.
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2
    llm_retry_backoff_seconds: float = 0.5

    # Agentic/RAG settings
    rag_knowledge_base_path: str = "app/rag/knowledge_base"
    rag_top_k: int = 3
    agent_generator_mode: str = "mock"  # mock | openai_compatible
    agent_safe_rewrite_mode: str = "deterministic"  # deterministic for release demo

    # Release hardening
    enable_security_headers: bool = True
    enable_request_id: bool = True
    cors_allow_origins: str = ""
    max_request_body_bytes: int = 2_000_000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MNP_",
        extra="ignore",
    )

    @property
    def allowed_api_keys(self) -> set[str]:
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}

    @property
    def sensitive_fields(self) -> set[str]:
        return {name.strip().lower() for name in self.sensitive_field_names.split(",") if name.strip()}

    @property
    def free_text_fields(self) -> set[str]:
        return {name.strip().lower() for name in self.free_text_field_names.split(",") if name.strip()}

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


settings = Settings()
