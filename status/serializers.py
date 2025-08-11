from rest_framework import serializers

from .models import RVM

class RVMSerializer(serializers.ModelSerializer):
    class Meta:
        model=RVM
        fields=["id","name","location","is_active","last_usage"]
        read_only_fields=fields