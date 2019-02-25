from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelMultipleChoiceField

from locationcode.models import LocationCode

from member.models import Member
from member.models import MemberGroup

class MemberForm(ModelForm):
    membergroups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=MemberGroup.objects.all())

    class Meta:
        model = Member
        fields = ['ssn', 'name', 'email', 'email_wanted', 'phone', 'added', 'membergroups']


class MemberGroupForm(ModelForm):
    auto_subgroups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=MemberGroup.objects.all())
    auto_locations = ModelMultipleChoiceField(required=False, queryset=LocationCode.objects.all())

    class Meta:
        model = MemberGroup
        fields = ['name', 'email', 'added',
                  'auto_subgroups', 'auto_locations', 'combination_method']


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
