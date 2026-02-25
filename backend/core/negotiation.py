from rest_framework.negotiation import DefaultContentNegotiation


class FormatOverrideNegotiation(DefaultContentNegotiation):
    """Content negotiation that lets an explicit ?format= query parameter
    win outright, bypassing Accept header matching.

    DRF's default behaviour filters renderers by ?format= but still requires
    the selected renderer's media_type to satisfy the Accept header.  This
    causes 406 errors when clients (e.g. the Swagger UI) unconditionally send
    ``Accept: application/json`` while also supplying ``?format=csv`` or
    ``?format=marcxml``.  When ?format= is present we return the matching
    renderer directly.
    """

    def select_renderer(self, request, renderers, format_suffix=None):
        format_query_param = self.settings.URL_FORMAT_OVERRIDE
        fmt = format_suffix or request.query_params.get(format_query_param)

        if fmt:
            filtered = self.filter_renderers(renderers, fmt)
            if filtered:
                return filtered[0], filtered[0].media_type

        return super().select_renderer(request, renderers, format_suffix)
