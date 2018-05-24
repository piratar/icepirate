from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelMultipleChoiceField

from member.models import Member
from group.models import Group

class MemberForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Member
        fields = ['ssn', 'name', 'email', 'email_wanted', 'phone', 'added', 'groups']


class SearchForm(Form):
    search_string = CharField(label='Search string', max_length=100)

    def clean_search_string(self):
        search = self.cleaned_data['search_string']

        # Reduce all spaces down to only one space.
        while '  ' in search:
            search = search.replace('  ', ' ')

        # Remove preceding and trailing spaces.
        search = search.strip()

        return search
