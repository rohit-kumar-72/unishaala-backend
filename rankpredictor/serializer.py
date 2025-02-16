from rest_framework import serializers
from .models import Slots,AnswerSheet

class SlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Slots
        fields='__all__'
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        department = validated_data.get('department')
        shift = validated_data.get('shift')
        date = validated_data.get('date')

        # Check if the slot already exists
        # created is boolean flag which wil show it is created or already present
        slot, created = Slots.objects.get_or_create(
            department=department,
            shift=shift,
            date=date
        )

        return slot

class AnswerSheetSerializer(serializers.ModelSerializer):
    mark = serializers.FloatField(required=False)
    slot = serializers.CharField(required=False)

    class Meta:
        model = AnswerSheet
        fields = '__all__'

    def validate(self, attrs):
        mode = self.context.get('mode', 'create')  # Default to 'create'

        if mode == 'create':  # Validation only for creation
            if 'mark' not in attrs:
                raise serializers.ValidationError({'mark': ['This field is required.']})
            if 'slot' not in attrs:
                raise serializers.ValidationError({'slot': ['This field is required.']})

        return attrs