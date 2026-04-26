from app.enums import ImportSourceType
from app.influencers.ingestion.adapters import InfluencerImportAdapter, ModashCsvImportAdapter


class UnsupportedImportSourceError(ValueError):
    pass


class ImportAdapterRegistry:
    def __init__(
        self, adapters: list[InfluencerImportAdapter] | None = None
    ) -> None:
        self._adapters = {
            adapter.source_type: adapter for adapter in (adapters or [ModashCsvImportAdapter()])
        }

    def get(self, source_type: ImportSourceType) -> InfluencerImportAdapter:
        adapter = self._adapters.get(source_type)
        if not adapter:
            raise UnsupportedImportSourceError(f"Unsupported import source: {source_type}")
        return adapter
