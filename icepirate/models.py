from django.apps import apps
from django.contrib.auth.models import User
from django.db.models import Manager
from django.db.models import Q

# A model manager for offering the ".safe(request.user)" functionality, which
# allows us to easily limit results to what the given user should have access
# to. This enables us to handle such things in one place and reduces the risk
# of accidents in views where such limitations are needed. Several different
# models are supported as can be seen in the code below.
#
# If the given user is a superuser, they get access to anything they want. If
# not, then the data retrieved is limited to that of which they are an admin
# (MemberGroup.admins field).
#
# Example usage (assuming Member uses SafetyManager as model manager):
#     members = Member.objects.safe(request.user).filter(something=something)
#
class SafetyManager(Manager):
    def safe(self, user):
        if user.__class__ is not User:
            raise AttributeError('safe() function takes exactly one User object')

        if user.is_superuser:
            return self
        else:
            Member = apps.get_model('member', 'Member')
            MemberGroup = apps.get_model('member', 'MemberGroup')
            Message = apps.get_model('message', 'Message')
            if self.model is Member:
                return self.filter(membergroups__admins=user).distinct()
            elif self.model is MemberGroup:
                return self.filter(admins=user).distinct()
            elif self.model is Message:
                return self.filter(Q(membergroups__admins=user) | Q(send_to_all=True)).distinct()
            else:
                raise NotImplementedError()
