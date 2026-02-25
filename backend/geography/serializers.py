from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import GeoPlace


class GeoPlaceCompactSerializer(serializers.ModelSerializer):
    """Minimal representation for FK embedding (in Repository/Zine responses)."""

    level = serializers.CharField(read_only=True)

    class Meta:
        model = GeoPlace
        fields = ["geoname_id", "name", "feature_code", "country_code", "level"]


class GeoPlaceSerializer(serializers.ModelSerializer):
    """Full serializer for the geography list API."""

    level = serializers.CharField(read_only=True)
    parent_geoname_id = serializers.IntegerField(
        source="parent.geoname_id", read_only=True, default=None
    )

    class Meta:
        model = GeoPlace
        fields = [
            "geoname_id",
            "name",
            "ascii_name",
            "feature_class",
            "feature_code",
            "country_code",
            "admin1_code",
            "continent_code",
            "latitude",
            "longitude",
            "population",
            "level",
            "parent_geoname_id",
        ]


class GeoPlaceAncestorSerializer(serializers.ModelSerializer):
    """Compact ancestor entry for detail responses."""

    level = serializers.CharField(read_only=True)

    class Meta:
        model = GeoPlace
        fields = ["geoname_id", "name", "feature_code", "level"]


class GeoPlaceDetailSerializer(GeoPlaceSerializer):
    """Detail serializer with full ancestor chain."""

    ancestors = serializers.SerializerMethodField()

    class Meta(GeoPlaceSerializer.Meta):
        fields = [*GeoPlaceSerializer.Meta.fields, "ancestors"]

    @extend_schema_field(GeoPlaceAncestorSerializer(many=True))
    def get_ancestors(self, obj):
        chain = obj.ancestor_chain()
        return GeoPlaceAncestorSerializer(chain[1:], many=True).data
