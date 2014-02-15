from django.forms import ModelForm, EmailField, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.forms import EmailField

from member.models import Member
from group.models import Group

class MemberForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Member
        fields = ['kennitala', 'name', 'username', 'email', 'phone', 'added', 'groups']

    def clean_username(self):
        # Usernames are unique but not required, and forms return empty strings which can't then be unique
        # So we turn empty strings into None so that we can retain both optionality and uniqueness.
        return self.cleaned_data['username'] or None

