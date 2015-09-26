from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import ModelForm
from django.forms import ModelMultipleChoiceField
from django.forms import TextInput

from member.models import Member
from group.models import Group

class MemberForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Member
        fields = ['ssn', 'name', 'email', 'email_unwanted', 'phone', 'added', 'groups']

