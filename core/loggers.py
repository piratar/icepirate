from django.conf import settings
from django.utils import timezone
import logging

#################
# Logger setup. #
#################

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Set up action logging.
action_logger_handler = logging.FileHandler(
    '%s/actions.log' % settings.LOG_DIR
)
action_logger_handler.setFormatter(formatter)
action_logger = logging.getLogger('actions')
action_logger.setLevel(logging.INFO)
action_logger.addHandler(action_logger_handler)

# Set up mail logging.
mail_logger_handler = logging.handlers.RotatingFileHandler(
    '%s/mailing.log' % settings.LOG_DIR,
    maxBytes=4 * 1024 * 1024,
    backupCount=9,
)
mail_logger_handler.setFormatter(formatter)
mail_logger = logging.getLogger('mailing')
mail_logger.setLevel(logging.INFO)
mail_logger.addHandler(mail_logger_handler)

######################
# Logging functions. #
######################

# Logging of sent mail, successful when no exception is given, unsuccessful
# if one is provided.
def log_mail(email, message, exception=None, testsend=False):
    class_type = message.__class__.__name__

    # Make sure that only objects of supported types are provided.
    if class_type not in ['Message', 'InteractiveMessage']:
        raise Exception('log_mail function does not support message type %s' % class_type)

    # Determine which slightly more detailed information on the object in
    # question we might want to report.
    detail = ''
    if class_type == 'Message':
        detail = str(message.id)
    elif class_type == 'InteractiveMessage':
        detail = message.interactive_type

    # If this is a testsend, include that information in the logging. This
    # means that the content may differ radically from what eventually gets
    # sent out to members and subscribers.
    if testsend:
        detail += '(TESTING)'

    # Main message, includes the basics that all mail log entries have in
    # common.
    msg = '%s:%s - %s' % (class_type, detail, email)

    # Actually log info or error, depending on circumstances.
    if exception is None:
        mail_logger.info(msg)
    else:
        mail_logger.error('%s: (%s) %s' % (
            msg,
            type(exception).__name__,
            exception.__str__()
        ))

# Logging of user actions, for auditing purposes.
def log_action(user, action, action_details=None, affected_members=None):
    # A comma-separated list of member row IDs that were affected by the
    # action. Information on the affected members is preserved in this manner
    # to retain the IDs of those who were affected, even after they've been
    # deleted from the database. That way, the data is in some sense more
    # accurate, even though no information on the deleted member's information
    # can be retrieved.
    affected_member_ids = ''

    # Auto-populated field for keeping track of how many users are needed.
    # Using this field is preferable to using `affected_members` in displaying
    # events because we prefer displaying statistics rather than personal
    # data, even when personal data needs to be retained. This also retains
    # the number of affected users instead of the `affected_members` field,
    # because members are removed from that field upon their deletion.
    affected_member_count = 0

    if affected_members is not None:
        affected_member_ids = ','.join([str(m.id) for m in affected_members])
        affected_member_count = len(affected_members)

    # Only one user is ever deleted at a time, so we'll know that the number
    # of affected users was 1, even though we can't store information on the
    # deleted user for privacy reasons.
    if action == 'member_delete':
        affected_member_count = 1

    msg = 'User: %s - Action: %s - Affected user count: %d' % (
        # The user performing the action.
        user.username,
        # Example: 'member_search', 'member_view' etc.
        action,
        # See comment above.
        affected_member_count
    )
    if action_details is not None:
        # More detail on the action taken, when appropriate. For example, the
        # search string of a member search.
        msg += ' - Action details: %s' % str(action_details)
    if affected_members is not None:
        # See comment above.
        msg += ' - Affected user IDs: [%s]' % affected_member_ids

    action_logger.info(msg)
