import random
import string
from django.http  import HttpRequest
from django.utils import timezone
from datetime     import timedelta


class SessionSubsystem:
    def __init__(self: 'SessionSubsystem'):
        pass

    def clean_session_data(self: 'SessionSubsystem', request: HttpRequest, keys: list) -> None:
        """
        Cleans the session data for the current user's session. 

        Args:
            self (SessionSubsystem): The self class object. 
            request (HttpRequest): The HTTP request object. 
            keys (list): The keys retrieved from the session dictionary.
        """
        for key in keys:
            if key in request.session:
                del request.session[key]

    def check_session_expiration(self: 'SessionSubsystem', request: HttpRequest, timestamp_key: str, minutes: int = 10) -> bool:
        """
        Checks if the session has expired based on a timestamp stored in the session.

        Args:
            self (SessionSubsystem): The self class object. 
            request (HttpRequest): The HTTP request object. 
            timestamp_key (str): The key in the session dictionary where the timestamp is stored.
            minuter (int, optional): The expiration time in minutes. Defaults to 10.

        Returns:
            bool: True if the session has expired, False otherwise.
        """
        timestamp_str = request.session.get(timestamp_key)
        if timestamp_str:
            try:
                timestamp = timezone.datetime.fromisoformat(timestamp_str)
                return timezone.now() - timestamp > timedelta(minutes=minutes)
            except (ValueError, TypeError):
                return True
        return True

    def generate_verification_code(self: 'SessionSubsystem'):
        """
        Helper: Generate a 6-digit verification code.
        """
        return ''.join(random.choices(string.digits, k=6))
