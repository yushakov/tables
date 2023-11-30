from rest_framework import serializers
from list.models import Choice 

class TaskSerializer(serializers.Serializer):
    id = serializers.CharField(required=True, max_length=500)
    construct_name = serializers.CharField(required=False, allow_blank=True, max_length=500)
    name_txt = serializers.CharField(required=False, allow_blank=True, max_length=100)
    plan_start_date = serializers.DateField(required=True)
    plan_days_num = serializers.IntegerField(required=False)
    progress_percent_num = serializers.IntegerField(required=True)
    type = serializers.CharField(required=False, max_length=100)
    hide_children = serializers.IntegerField(read_only=True)
    display_order = serializers.IntegerField(read_only=True)

    def create(self, validated_data):
        # Simply return the validated data as a new "Task"
        return validated_data

    def update(self, instance, validated_data):
        # Update the instance dictionary with validated data
        for attr, value in validated_data.items():
            instance[attr] = value
        return instance

    @staticmethod
    def transform_choice_to_task(choice):
        return {
            'id': str(choice.id),
            'construct_name': choice.construct.title_text,
            'name_txt': choice.name_txt,
            'plan_start_date': choice.plan_start_date,
            'plan_days_num': choice.plan_days_num,
            'progress_percent_num': choice.progress_percent_num,
            'type': 'task'
        }
