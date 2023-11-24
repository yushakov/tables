from rest_framework import serializers
from list.models import Choice 

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'construct_name', 'name_txt', 'plan_start_date', 'plan_days_num', 'progress_percent_num']

