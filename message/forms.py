from django.forms import ModelForm, EmailField, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.forms import EmailField
from django.forms import ValidationError

from message.models import InteractiveMessage
from message.models import Message
from group.models import Group

class MessageForm(ModelForm):
    groups = ModelMultipleChoiceField(required=False, widget=CheckboxSelectMultiple(), queryset=Group.objects.all())

    class Meta:
        model = Message
        fields = ['from_address', 'subject', 'body', 'send_to_all', 'groups',
                  'groups_include_subgroups', 'groups_include_locations',
                  'locations', 'wasa2il_usage']

class InteractiveMessageForm(ModelForm):

    def clean_body(self):
        data = self.cleaned_data['body']
        if self.instance.interactive_type in InteractiveMessage.INTERACTIVE_TYPES_DETAILS:
            missing_links = ''
            for link in InteractiveMessage.INTERACTIVE_TYPES_DETAILS[self.instance.interactive_type]['links']:
                if ('{{%s}}' % link) not in data:
                    missing_links = missing_links + (', {{%s}}' % link) if len(missing_links) > 0 else '{{%s}}' % link

            if len(missing_links) > 0:
                raise ValidationError('Missing link strings: %(missing_links)s', params={'missing_links': missing_links})

        return data

    class Meta:
        model = InteractiveMessage
        fields = ['from_address', 'subject', 'body']

