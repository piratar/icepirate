from django.forms import ModelForm, EmailField, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.forms import EmailField

from member.models import Member
from group.models import Group

class MemberForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Member
        fields = ['kennitala', 'name', 'username', 'email', 'phone', 'added', 'groups']

