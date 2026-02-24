from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import GeoPlace
from .serializers import GeoPlaceDetailSerializer, GeoPlaceSerializer


class GeoPlaceFilter(filters.FilterSet):
    level = filters.CharFilter(method="filter_level")
    parent = filters.NumberFilter(field_name="parent__geoname_id")
    parent_isnull = filters.BooleanFilter(field_name="parent", lookup_expr="isnull")
    country_code = filters.CharFilter(field_name="country_code")
    continent_code = filters.CharFilter(field_name="continent_code")

    class Meta:
        model = GeoPlace
        fields = ["level", "parent", "parent_isnull", "country_code", "continent_code"]

    def filter_level(self, queryset, name, value):
        mapping = {
            "country": "PCLI",
            "admin1": "ADM1",
        }
        feature_code = mapping.get(value)
        if feature_code:
            return queryset.filter(feature_code=feature_code)
        elif value == "city":
            return queryset.filter(feature_class="P")
        return queryset


class GeoPlaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GeoPlace.objects.select_related("parent").all()
    search_fields = ["name", "ascii_name"]
    ordering_fields = ["name", "population"]
    ordering = ["name"]
    lookup_field = "geoname_id"
    filterset_class = GeoPlaceFilter

    def get_serializer_class(self):
        if self.action == "retrieve":
            return GeoPlaceDetailSerializer
        return GeoPlaceSerializer
