from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple
from django.forms import EmailField
from django.forms import HiddenInput
from django.forms import ModelForm
from django.forms import ModelMultipleChoiceField
from django.forms import ValidationError

from member.models import MemberGroup

from message.models import InteractiveMessage
from message.models import Message

from urllib.parse import unquote

class MessageForm(ModelForm):

    user = None
    shown_membergroups = None

    membergroups = ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple(),
        queryset=MemberGroup.objects.none()
    )

    def __init__(self, user, *args, **kwargs):
        self.exclude = ['send_to_all']
        if user.__class__ is not User:
            raise AttributeError('First argument of MessageForm must be user')

        super(MessageForm, self).__init__(*args, **kwargs)

        # Only superuser can send to all.
        if not user.is_superuser:
            self.fields['send_to_all'].widget = HiddenInput()

        # Save the user for later.
        self.user = user

        # These are the membergroups that the currently logged in user (given
        # by the "user" argument) has the authority to manipulate.
        self.shown_membergroups = MemberGroup.objects.safe(user).all()

        self.fields['membergroups'].queryset = self.shown_membergroups

    def clean_send_to_all(self):
        send_to_all = self.cleaned_data['send_to_all']

        # Only superuser can send to all.
        if not self.user.is_superuser:
            return False

        return send_to_all

    def clean_membergroups(self):
        membergroups = self.cleaned_data['membergroups']

        if not self.user.is_superuser and len(membergroups) == 0:
            raise ValidationError('At least one membergroup must be selected')

        return membergroups

    class Meta:
        model = Message
        fields = [
            'from_address',
            'subject',
            'body',
            'send_to_all',
            'membergroups',
            'groups_include_subgroups',
            #'groups_include_locations',
            #'locations',
            'wasa2il_usage',
            'generate_html_mail'
        ]


class InteractiveMessageForm(ModelForm):

    def clean_body(self):
        data = unquote(self.cleaned_data['body'])
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

