from django.forms import ModelForm
from django.forms import CheckboxSelectMultiple
from django.forms import ModelMultipleChoiceField

from group.models import Group
from locationcode.models import LocationCode

class GroupForm(ModelForm):
    auto_subgroups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())
    auto_locations = ModelMultipleChoiceField(required=False, queryset=LocationCode.objects.all())

    class Meta:
        model = Group
        fields = ['name', 'email', 'added', 'auto_subgroups', 'auto_locations']
