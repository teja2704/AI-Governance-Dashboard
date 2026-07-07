import os


SENSITIVE_WORDS = [
    "forbidden",
    "password",
    "secret",
    "ssn",
    "api key"
]

NEAR_EMPTY_RESPONSE_LENGTH = 20


def max_response_length() -> int:
    return int(
        os.getenv(
            "AUTOMATED_EVALUATION_MAX_RESPONSE_LENGTH",
            "4000"
        )
    )
