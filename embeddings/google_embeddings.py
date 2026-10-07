from langchain_google_genai import GoogleGenerativeAIEmbeddings

from utils.errors import ProviderError
from utils.logging_config import event


class GoogleEmbeddingService:
    def __init__(self, settings):
        self.fingerprint = f"google:{settings.embedding_model}:768:retrieval-v1"
        self.client = GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model, google_api_key=settings.google_api_key,
            output_dimensionality=768, vertexai=False,
            # request_options exists in the SDK schema but is unused by version 4.4.0.
            client_args={"timeout": settings.api_timeout_seconds},
        )

    def embed_documents(self, texts):
        try:
            result = []
            for offset in range(0, len(texts), 32):
                result.extend(self.client.embed_documents(texts[offset:offset + 32],
                                                           task_type="RETRIEVAL_DOCUMENT"))
            return result
        except Exception as exc:
            event("embedding_failure", error_type=type(exc).__name__)
            raise ProviderError("Google embedding request failed. Check credentials, quota and connectivity.") from None

    def embed_query(self, text):
        try:
            return self.client.embed_query(text, task_type="RETRIEVAL_QUERY")
        except Exception as exc:
            event("embedding_failure", error_type=type(exc).__name__)
            raise ProviderError("Google query embedding failed. Check credentials, quota and connectivity.") from None
