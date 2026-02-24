from rest_framework import serializers

from agents.serializers import AgentSerializer, AgentRoleSerializer
from geography.models import GeoPlace
from geography.serializers import GeoPlaceCompactSerializer

from .models import (
    Genre,
    Language,
    RightsStatement,
    Subject,
    Zine,
    ZineContributor,
    ZineCreator,
    ZinePublisher,
)


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ["code", "label"]


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["code", "label"]


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ["code", "label"]


class RightsStatementSerializer(serializers.ModelSerializer):
    class Meta:
        model = RightsStatement
        fields = ["code", "label", "uri", "description"]


class ZineCreatorSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = ZineCreator
        fields = ["agent", "order"]


class ZineContributorSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)
    role = AgentRoleSerializer(read_only=True)

    class Meta:
        model = ZineContributor
        fields = ["agent", "role", "order"]


class ZinePublisherSerializer(serializers.ModelSerializer):
    agent = AgentSerializer(read_only=True)

    class Meta:
        model = ZinePublisher
        fields = ["agent", "order"]


class ZineSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="zine_id")
    subjects = SubjectSerializer(many=True, read_only=True)
    genres = GenreSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    rights_statement = RightsStatementSerializer(read_only=True)
    place_of_publication = GeoPlaceCompactSerializer(read_only=True)

    # Through model serializers
    zinecreator_set = ZineCreatorSerializer(many=True, read_only=True)
    zinecontributor_set = ZineContributorSerializer(many=True, read_only=True)
    zinepublisher_set = ZinePublisherSerializer(many=True, read_only=True)

    # Derived dcterms-compatible flat lists
    subject = serializers.SerializerMethodField()
    genre = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    creator = serializers.SerializerMethodField()
    contributor = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()
    rights = serializers.SerializerMethodField()

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
            "zinecreator_set",
            "contributor",
            "zinecontributor_set",
            "subject",
            "subjects",
            "genre",
            "genres",
            "abstract",
            "table_of_contents",
            "public_notes",
            "publisher",
            "zinepublisher_set",
            "publish_date",
            "physical_dimensions",
            "number_of_pages",
            "format",
            "binding_features",
            "language",
            "languages",
            "place_of_publication",
            "coverage",
            "source",
            "relation",
            "rights",
            "rights_statement",
            "identifier",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_subject(self, obj):
        return list(obj.subjects.values_list("label", flat=True))

    def get_genre(self, obj):
        return list(obj.genres.values_list("label", flat=True))

    def get_language(self, obj):
        return list(obj.languages.values_list("code", flat=True))

    def get_creator(self, obj):
        return [
            zc.agent.display_name
            for zc in obj.zinecreator_set.all().order_by("order")
        ]

    def get_contributor(self, obj):
        return [
            zc.agent.display_name
            for zc in obj.zinecontributor_set.all().order_by("order")
        ]

    def get_publisher(self, obj):
        return [
            zp.agent.display_name
            for zp in obj.zinepublisher_set.all().order_by("order")
        ]

    def get_rights(self, obj):
        if obj.rights_statement:
            return [obj.rights_statement.label]
        return []


class ContributorDataSerializer(serializers.Serializer):
    agent_id = serializers.CharField()
    role_code = serializers.CharField()
    order = serializers.IntegerField(default=0)


class ZineWriteSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="zine_id", required=False)
    place_of_publication_geoname_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )
    subject_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    genre_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    language_codes = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    creator_ids = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    contributor_data = serializers.ListField(
        child=ContributorDataSerializer(), write_only=True, required=False
    )
    publisher_ids = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    rights_code = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Zine
        fields = [
            "id",
            "title",
            "series_title",
            "issue_designation",
            "edition_statement",
            "alternative_title",
            "abstract",
            "table_of_contents",
            "public_notes",
            "publish_date",
            "physical_dimensions",
            "number_of_pages",
            "format",
            "binding_features",
            "place_of_publication_geoname_id",
            "coverage",
            "source",
            "relation",
            "identifier",
            "subject_codes",
            "genre_codes",
            "language_codes",
            "creator_ids",
            "contributor_data",
            "publisher_ids",
            "rights_code",
        ]

    def _resolve_place_of_publication(self, validated_data):
        geoname_id = validated_data.pop("place_of_publication_geoname_id", None)
        if geoname_id is not None:
            validated_data["place_of_publication"] = GeoPlace.objects.get(
                geoname_id=geoname_id
            )
        return validated_data

    def create(self, validated_data):
        # Extract M2M and through model data
        subject_codes = validated_data.pop("subject_codes", [])
        genre_codes = validated_data.pop("genre_codes", [])
        language_codes = validated_data.pop("language_codes", [])
        creator_ids = validated_data.pop("creator_ids", [])
        contributor_data = validated_data.pop("contributor_data", [])
        publisher_ids = validated_data.pop("publisher_ids", [])
        rights_code = validated_data.pop("rights_code", None)

        # Resolve place of publication
        self._resolve_place_of_publication(validated_data)

        # Set rights statement
        if rights_code:
            validated_data["rights_statement"] = RightsStatement.objects.get(
                code=rights_code
            )

        # Create zine
        zine = Zine.objects.create(**validated_data)

        # Set M2M relationships
        if subject_codes:
            zine.subjects.set(Subject.objects.filter(code__in=subject_codes))
        if genre_codes:
            zine.genres.set(Genre.objects.filter(code__in=genre_codes))
        if language_codes:
            zine.languages.set(Language.objects.filter(code__in=language_codes))

        # Create through model instances
        from agents.models import Agent, AgentRole

        for order, agent_id in enumerate(creator_ids):
            agent = Agent.objects.get(agent_id=agent_id)
            ZineCreator.objects.create(zine=zine, agent=agent, order=order)

        for item in contributor_data:
            agent = Agent.objects.get(agent_id=item["agent_id"])
            role = AgentRole.objects.get(code=item["role_code"])
            ZineContributor.objects.create(
                zine=zine, agent=agent, role=role, order=item.get("order", 0)
            )

        for order, agent_id in enumerate(publisher_ids):
            agent = Agent.objects.get(agent_id=agent_id)
            ZinePublisher.objects.create(zine=zine, agent=agent, order=order)

        return zine

    def update(self, instance, validated_data):
        # Extract M2M and through model data
        subject_codes = validated_data.pop("subject_codes", None)
        genre_codes = validated_data.pop("genre_codes", None)
        language_codes = validated_data.pop("language_codes", None)
        creator_ids = validated_data.pop("creator_ids", None)
        contributor_data = validated_data.pop("contributor_data", None)
        publisher_ids = validated_data.pop("publisher_ids", None)
        rights_code = validated_data.pop("rights_code", None)

        # Resolve place of publication
        self._resolve_place_of_publication(validated_data)

        # Update rights statement
        if rights_code is not None:
            if rights_code:
                validated_data["rights_statement"] = RightsStatement.objects.get(
                    code=rights_code
                )
            else:
                validated_data["rights_statement"] = None

        # Update basic fields
        instance = super().update(instance, validated_data)

        # Update M2M relationships
        if subject_codes is not None:
            instance.subjects.set(Subject.objects.filter(code__in=subject_codes))
        if genre_codes is not None:
            instance.genres.set(Genre.objects.filter(code__in=genre_codes))
        if language_codes is not None:
            instance.languages.set(Language.objects.filter(code__in=language_codes))

        # Update through model instances
        from agents.models import Agent, AgentRole

        if creator_ids is not None:
            instance.zinecreator_set.all().delete()
            for order, agent_id in enumerate(creator_ids):
                agent = Agent.objects.get(agent_id=agent_id)
                ZineCreator.objects.create(zine=instance, agent=agent, order=order)

        if contributor_data is not None:
            instance.zinecontributor_set.all().delete()
            for item in contributor_data:
                agent = Agent.objects.get(agent_id=item["agent_id"])
                role = AgentRole.objects.get(code=item["role_code"])
                ZineContributor.objects.create(
                    zine=instance, agent=agent, role=role, order=item.get("order", 0)
                )

        if publisher_ids is not None:
            instance.zinepublisher_set.all().delete()
            for order, agent_id in enumerate(publisher_ids):
                agent = Agent.objects.get(agent_id=agent_id)
                ZinePublisher.objects.create(zine=instance, agent=agent, order=order)

        return instance
