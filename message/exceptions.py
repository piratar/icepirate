'''
Thrown when a bulk-send is attempted on a message already being processed.
'''
class MessageBeingProcessedException(Exception):
    pass
