from rest_framework import serializers

from .models import Genre, RightsStatement, Subject, Zine


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["code", "label"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["code", "label"]


class RightsStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RightsStatement
        fields = ["code", "label", "uri", "description"]


class ZineSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="zine_id")
    subjects = SubjectSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    # Derived dcterms-compatible flat lists from M2M
    subject = serializers.SerializerMethodField()
    genre = serializers.SerializerMethodField()

    class Meta:
        model = Zine
        fields = [
            "id",
            "title",
            "series_title",
            "issue_designation",
            "edition_statement",
            "alternative_title",
            "creator",
            "contributor",
            "subject",
            "subjects",
            "genre",
            "genres",
            "abstract",
            "table_of_contents",
            "public_notes",
            "publisher",
            "date",
            "physical_dimensions",
            "number_of_pages",
            "format",
            "binding_features",
            "language",
            "place_of_publication",
            "coverage",
            "source",
            "relation",
            "rights",
            "identifier",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_subject(self, obj):
        return list(obj.subjects.values_list("label", flat=True))

    def get_genre(self, obj):
        return list(obj.genres.values_list("label", flat=True))


class ZineWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="zine_id")
    subject_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    genre_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Zine
        fields = [
            "id",
            "title",
            "series_title",
            "issue_designation",
            "edition_statement",
            "alternative_title",
            "creator",
            "contributor",
            "abstract",
            "table_of_contents",
            "public_notes",
            "publisher",
            "date",
            "physical_dimensions",
            "number_of_pages",
            "format",
            "binding_features",
            "language",
            "place_of_publication",
            "coverage",
            "source",
            "relation",
            "rights",
            "identifier",
            "subject_codes",
            "genre_codes",
        ]

    def create(self, validated_data):
        subject_codes = validated_data.pop("subject_codes", [])
        genre_codes = validated_data.pop("genre_codes", [])
        zine = Zine.objects.create(**validated_data)
        if subject_codes:
            zine.subjects.set(Subject.objects.filter(code__in=subject_codes))
        if genre_codes:
            zine.genres.set(Genre.objects.filter(code__in=genre_codes))
        return zine

    def update(self, instance, validated_data):
        subject_codes = validated_data.pop("subject_codes", None)
        genre_codes = validated_data.pop("genre_codes", None)
        instance = super().update(instance, validated_data)
        if subject_codes is not None:
            instance.subjects.set(Subject.objects.filter(code__in=subject_codes))
        if genre_codes is not None:
            instance.genres.set(Genre.objects.filter(code__in=genre_codes))
        return instance
