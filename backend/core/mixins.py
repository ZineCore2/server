class CSVPaginationBypassMixin:
    """Disables pagination when the requested format is CSV so the full
    result set is returned in a single file download."""

    def list(self, request, *args, **kwargs):
        if getattr(request, "accepted_renderer", None) and request.accepted_renderer.format == "csv":
            self.pagination_class = None
        return super().list(request, *args, **kwargs)
