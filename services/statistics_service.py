class StatisticsService:
    def __init__(self, repository, store):
        self.repository, self.store = repository, store

    def snapshot(self):
        stats = self.repository.statistics()
        stats["vectors"] = sum(self.store.document_counts().values())
        stats["vector_status"] = "Ready" if stats["vectors"] else "Empty - upload a PDF"
        return stats
