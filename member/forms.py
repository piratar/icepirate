from django.contrib.auth.models import User
from django.forms import CharField
from django.forms import CheckboxSelectMultiple
from django.forms import Form
from django.forms import ModelForm
from django.forms import ModelMultipleChoiceField
from django.forms import ValidationError

from member.models import Member
from member.models import MemberGroup
from member.models import Municipality

# We want to display users' names, not their usernames.
class MemberGroupAdminField(ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return '%s %s' % (obj.first_name, obj.last_name)


class MemberForm(ModelForm):

    user = None
    current_membergroups = []
    shown_membergroups = None

    membergroups = ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple(),
        queryset = MemberGroup.objects.none()
    )

    def __init__(self, user, *args, **kwargs):
        if user.__class__ is not User:
            raise AttributeError('First argument of MemberForm must be user')

        super(MemberForm, self).__init__(*args, **kwargs)

        # Save the user for later.
        self.user = user

        # In other words, if we're editing as opposed to adding.
        if 'instance' in kwargs:
            member = kwargs['instance']

            # We use list() to force the query's execution now, instead of
            # later in the save-function, because the data may already have
            # been altered at that point.
            self.current_membergroups = list(member.membergroups.all())

        # These are the membergroups that the currently logged in user (given
        # by the "user" argument) has the authority to manipulate.
        self.shown_membergroups = MemberGroup.objects.safe(user).all()

        self.fields['membergroups'].queryset = self.shown_membergroups

    def clean_membergroups(self):
        membergroups = self.cleaned_data['membergroups']

        if not self.user.is_superuser and len(membergroups) == 0:
            raise ValidationError('At least one membergroup must be selected')

        return membergroups

    def clean_email_wanted(self):
        # Normally, `email_wanted_reason` will be put in my the member after
        # having clicked the unsubscribe-link. This form is only available to
        # an admin, so there is no reason, but we fill it for traceability.
        if 'email_wanted' in self.changed_data:
            if self.instance.id is None:
                self.instance.email_wanted_reason = '[Set by admin when adding member in UI]'
            else:
                self.instance.email_wanted_reason = '[Updated by admin in UI]'

        return self.cleaned_data['email_wanted']

    def save(self, commit=True):

        instance = super(MemberForm, self).save(commit=commit)

        if commit:
            # The currently logged in user (given in the constructor) doesn't
            # necessarily have the authority to change the member's membership
            # to other membergroups. In fact, the user only sees those
            # membergroups in which they are a member (also limited in the
            # form's constructor).
            #
            # By default, the form will interpret the lack of other
            # membergroups in the input as meaning that the member should be
            # removed from them, but this is not the case but rather because
            # the currently logged in user doesn't even see them, let alone
            # control them. To combat this, we keep track of other
            # membergroups of which the member is a part of before the form is
            # executed and re-add them to those membergroups here.

            # Find the membergroups that the member was a part of before,
            # minus those that the current user has access to. This will give
            # us the membergroups of which the member was a part of before,
            # but the current user has no authority over. Those are the same
            # groups that we should ensure that the member will continue to be
            # a part of.
            retain = [mg for mg in self.current_membergroups if mg not in self.shown_membergroups]

            # Then, we re-add the member to those membergroups.
            for mg in retain:
                instance.membergroups.add(mg)

        return instance

    class Meta:
        model = Member
        fields = ['ssn', 'name', 'email', 'email_wanted', 'phone', 'added', 'membergroups']


class MemberGroupForm(ModelForm):
    admins = MemberGroupAdminField(
        required=False,
        widget=CheckboxSelectMultiple(),
        queryset=User.objects.filter(
            is_superuser=False
        ).order_by(
            'first_name',
            'last_name'
        )
    )
    auto_subgroups = ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple(),
        queryset=MemberGroup.objects.all()
    )

    condition_municipalities = ModelMultipleChoiceField(
        required=False,
        widget=CheckboxSelectMultiple(),
        queryset=Municipality.objects.all()
    )

    class Meta:
        model = MemberGroup
        fields = [
            'name',
            'email',
            'added',
            'admins',
            'auto_subgroups',
            'condition_municipalities',
        ]


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
