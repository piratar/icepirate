from django.forms import ModelForm, EmailField, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.forms import EmailField

from message.models import Message
from group.models import Group

class MessageForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Message
        fields = ['from_address', 'subject', 'body', 'send_to_all', 'groups']

