from pydantic.error_wrappers import ValidationError


class EmailDoesExist(ValueError):
    """
    Unique constraint violation for user's email.
    """
    pass


def bypass_email_validation_error(error: ValidationError):
    """
    If the ValidationError is raised for the email field ONLY (because of the unique constraint violation)
    skip it.
    Otherwise - if other validations fail - raise the ValidationError.
    """
    if not all([e.get('type') == 'value_error.emaildoesexist' for e in error.errors()]):
        raise error
