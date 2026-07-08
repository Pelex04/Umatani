from app.modules.media.storage import StorageBackend, get_storage_backend


def get_storage() -> StorageBackend:
    return get_storage_backend()
