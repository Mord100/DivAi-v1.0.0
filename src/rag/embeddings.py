import time
from langchain_voyageai import VoyageAIEmbeddings


class RetryEmbeddings(VoyageAIEmbeddings):
    """
    VoyageAI embeddings with automatic retry on rate-limit errors.

    VoyageAI's free tier is 3 RPM. When the use_case and solution agents
    both embed queries within the same minute, the second call fails.
    This wrapper catches the 429 / rate-limit error and waits with
    exponential backoff before retrying.
    """

    def _with_retry(self, fn, max_retries: int = 4, base_delay: int = 22):
        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                msg = str(e).lower()
                is_rate_limit = any(k in msg for k in ("rate", "429", "rpm", "tpm", "reduced rate"))
                if is_rate_limit and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)   # 22s → 44s → 88s
                    print(f"[Embeddings] Rate limited — waiting {delay}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    raise

    def embed_documents(self, texts):
        return self._with_retry(lambda: super(RetryEmbeddings, self).embed_documents(texts))

    def embed_query(self, text):
        return self._with_retry(lambda: super(RetryEmbeddings, self).embed_query(text))


def get_embeddings(model: str = "voyage-3-lite") -> RetryEmbeddings:
    return RetryEmbeddings(model=model)
