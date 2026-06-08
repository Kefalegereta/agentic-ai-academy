"""Knowledge base loader.

Reads every markdown blob from the Azure Blob Storage container ONCE at startup
and concatenates them into a single in-memory string. Same idea as exercice1's
baked-in /kb.txt: read once, serve fast and deterministic. The KB is small (a
few Notion pages) so the whole thing fits comfortably in the LLM context window,
no vector search needed.

The only Azure-specific surface here is the BlobServiceClient. To port to AWS,
swap this module for an S3 equivalent (boto3 list_objects_v2 + get_object); the
rest of the app never knows where the bytes came from.
"""

from azure.storage.blob import BlobServiceClient

from .config import Settings


def load_kb(settings: Settings) -> str:
    """Download and concatenate all blobs in the container into one string."""
    account_url = f"https://{settings.storage_account}.blob.core.windows.net"
    service = BlobServiceClient(account_url=account_url, credential=settings.storage_key)
    container = service.get_container_client(settings.storage_container)

    parts: list[str] = []
    for blob in sorted(container.list_blobs(), key=lambda b: b.name):
        text = container.download_blob(blob.name).readall().decode("utf-8")
        # Label each document so the model can attribute facts to a source.
        parts.append(f"# SOURCE: {blob.name}\n\n{text}")

    if not parts:
        raise RuntimeError(
            f"No blobs found in container '{settings.storage_container}'. "
            f"Check the container name and credentials."
        )

    return "\n\n---\n\n".join(parts)
