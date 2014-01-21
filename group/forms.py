from django.forms import ModelForm

from group.models import Group

class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'added']

