import re

# Match valid email format
# [A-Za-z0-9]+: start with 1+ letters/numbers
# ([._-][A-Za-z0-9]+)*: optional delimiters followed by letters/numbers
# @[A-Za-z0-9-]+: domain
# (\.[A-Za-z0-9-]+)*: optional subdomains
# \.[A-Za-z]{2,}: top level domain (TLD)
EMAIL_REGEX = r'^[A-Za-z0-9]+([._-][A-Za-z0-9]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$'

class Email:
    def __init__(self, email: str):
        if not isinstance(email, str):
            raise TypeError(f'Bad type for email: {type(email)}')
        if not re.match(EMAIL_REGEX, email):
            raise ValueError(f'{email} does not match email format')
        self.email = email

    def __str__(self):
        return self.email

def main():
    email = Email("abc@example.com")
    print(email)

if __name__ == '__main__':
    main()