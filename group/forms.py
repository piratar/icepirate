from django.forms import ModelForm
from django.forms import CheckboxSelectMultiple
from django.forms import ModelMultipleChoiceField

from member.models import MemberGroup
from locationcode.models import LocationCode

class MemberGroupForm(ModelForm):
    auto_subgroups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=MemberGroup.objects.all())
    auto_locations = ModelMultipleChoiceField(required=False, queryset=LocationCode.objects.all())

    class Meta:
        model = Group
        fields = ['name', 'email', 'added',
                  'auto_subgroups', 'auto_locations', 'combination_method']
