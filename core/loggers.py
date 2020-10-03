from django.conf import settings
from django.utils import timezone
import logging

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

mail_logger_handler = logging.handlers.RotatingFileHandler(
    '%s/mailing.log' % settings.LOG_DIR,
    maxBytes=4 * 1024 * 1024,
    backupCount=9,
)
mail_logger_handler.setFormatter(formatter)

mail_logger = logging.getLogger('mailing')
mail_logger.setLevel(logging.INFO)
mail_logger.addHandler(mail_logger_handler)

def log_mail(email, message, exception=None):
    class_type = message.__class__.__name__

    if class_type not in ['Message', 'InteractiveMessage']:
        raise Exception('log_mail function does not support message type %s' % class_type)

    if exception is None:
        mail_logger.info('%s:%d - %s' % (class_type, message.id, email))
    else:
        mail_logger.error('%s:%d - %s: (%s) %s' % (
            class_type,
            message.id,
            email,
            type(exception).__name__, exception.__str__()
        ))
