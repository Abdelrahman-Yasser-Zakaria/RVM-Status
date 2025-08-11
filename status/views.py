from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets
import django_filters
from .serializers import RVMSerializer
from .models import RVM


class RVMFilter(django_filters.FilterSet):
    # substring match: ?loc=alex
    loc = django_filters.CharFilter(
        field_name="location", lookup_expr="icontains", label="Location contains"
    )
    # recent flag: ?recent=true limits to last 24h
    recent = django_filters.BooleanFilter(
        method="filter_recent", label="Used in last 24h"
    )

    class Meta:
        model = RVM
        fields = ["location", "loc", "recent"]

    def filter_recent(self, queryset, name, value):  # noqa: D401
        if value:
            cutoff = timezone.now() - timedelta(hours=24)
            return queryset.filter(last_usage__isnull=False, last_usage__gte=cutoff)
        return queryset


class RVMViewSet(viewsets.ModelViewSet):
    queryset = RVM.objects.filter(is_active=True)
    serializer_class = RVMSerializer
    filterset_class = RVMFilter
