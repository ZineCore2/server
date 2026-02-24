from django.db import models


class GeoPlaceManager(models.Manager):
    def get_by_natural_key(self, geoname_id):
        return self.get(geoname_id=geoname_id)


class GeoPlace(models.Model):
    """Hierarchical geographic place backed by GeoNames data."""

    geoname_id = models.PositiveIntegerField(
        unique=True,
        help_text="GeoNames database ID.",
    )
    name = models.CharField(max_length=200)
    ascii_name = models.CharField(max_length=200, blank=True)

    feature_class = models.CharField(
        max_length=1,
        help_text="GeoNames feature class: 'A' admin, 'P' populated place.",
    )
    feature_code = models.CharField(
        max_length=10,
        help_text="GeoNames feature code: PCLI, ADM1, PPL, PPLA, etc.",
    )

    country_code = models.CharField(
        max_length=2,
        db_index=True,
        help_text="ISO 3166-1 alpha-2 country code.",
    )
    admin1_code = models.CharField(
        max_length=20,
        blank=True,
        help_text="First-order admin division code.",
    )
    continent_code = models.CharField(
        max_length=2,
        blank=True,
        help_text="Continent code (AF, AS, EU, NA, OC, SA, AN).",
    )

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    population = models.BigIntegerField(default=0)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
    )

    objects = GeoPlaceManager()

    class Meta:
        db_table = "geo_places"
        verbose_name = "Geographic Place"
        verbose_name_plural = "Geographic Places"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["geoname_id"]),
            models.Index(fields=["country_code", "admin1_code"]),
            models.Index(fields=["feature_code"]),
            models.Index(fields=["name"]),
        ]

    def natural_key(self):
        return (self.geoname_id,)

    def __str__(self):
        if self.feature_code == "PCLI":
            return self.name
        elif self.feature_code == "ADM1":
            return f"{self.name}, {self.country_code}"
        elif self.parent:
            return f"{self.name}, {self.parent.name}"
        return f"{self.name}, {self.country_code}"

    @property
    def level(self):
        if self.feature_code == "PCLI":
            return "country"
        elif self.feature_code == "ADM1":
            return "admin1"
        return "city"

    def ancestor_chain(self):
        """Return list of ancestors from self up to root."""
        chain = [self]
        current = self
        while current.parent_id is not None:
            current = current.parent
            chain.append(current)
        return chain
