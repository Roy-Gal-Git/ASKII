"""Custom embedding function for ChromaDB using Google Gemini API."""

from google import genai

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from src.utils.retry import retry_gemini_api


class GeminiEmbeddingFunction(EmbeddingFunction):
    """
    Custom embedding function for ChromaDB using google-genai package and gemini-embedding-001 model.

    This replaces the deprecated chromadb.utils.embedding_functions.GoogleGenerativeAiEmbeddingFunction.

    The API key is automatically inferred from GEMINI_API_KEY or GOOGLE_API_KEY environment variables.
    """

    def __init__(self) -> None:
        """
        Initialize the embedding function.

        The API key is automatically inferred from GEMINI_API_KEY or GOOGLE_API_KEY environment variables.
        """
        self._client = genai.Client()
        self._model = "gemini-embedding-001"

    @retry_gemini_api(max_attempts=8, base_delay=2.0, max_delay=120.0)
    def __call__(self, input: Documents) -> Embeddings:
        """
        Generate embeddings for a list of texts.

        This method is automatically retried with exponential backoff and jitter
        on transient API errors. It processes inputs in batches of 100 to respect
        the Gemini API batch limit.

        Args:
            input: List of text strings (Documents) to embed.

        Returns:
            List of embedding vectors (Embeddings), where each vector is a list of floats.

        Raises:
            Exception: If the API call fails after all retry attempts.
        """
        if not input:
            return []

        embeddings = []
        batch_size = 100  # Gemini API limit: at most 100 requests per batch

        # Process in batches to respect API limits
        for i in range(0, len(input), batch_size):
            batch = input[i : i + batch_size]

            result = self._client.models.embed_content(
                model=self._model,
                contents=batch,
            )

            # Extract values from ContentEmbedding objects to get list of lists of floats
            if hasattr(result, "embeddings"):
                # result.embeddings is a list of ContentEmbedding objects
                for content_embedding in result.embeddings:
                    # Each ContentEmbedding has a .values attribute
                    if hasattr(content_embedding, "values"):
                        embeddings.append(content_embedding.values)
                    elif isinstance(content_embedding, list):
                        # Fallback: if it's already a list
                        embeddings.append(content_embedding)
                    else:
                        # Try to convert to list
                        embeddings.append(list(content_embedding))
            else:
                raise RuntimeError(
                    "Unexpected result structure from Gemini embedding API"
                )

        return embeddings

