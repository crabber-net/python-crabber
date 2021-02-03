class MaxTriesError(BaseException):
    """ Raised when attempts to make a request exceed maximum number of
        attempts.
    """
    pass


class RequiresAuthenticationError(BaseException):
    """ Raised when attempting to make a request without proper authentication.
    """
    pass
