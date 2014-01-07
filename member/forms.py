from django.forms import ModelForm
from django.forms import EmailField

from member.models import Member

class MemberForm(ModelForm):
    class Meta:
        model = Member
        fields = ['kennitala', 'name', 'username', 'email', 'phone', 'added']

