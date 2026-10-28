from django.core.validators import RegexValidator

# 아이디: 영문 소문자 + 숫자, 1~16자
USERNAME_REGEX = r"^[a-z0-9]{1,16}$"
USERNAME_MESSAGE = "아이디는 영문 소문자와 숫자만 사용해 최대 16자까지 입력할 수 있습니다."

username_validator = RegexValidator(regex=USERNAME_REGEX, message=USERNAME_MESSAGE)

# 전화번호: 010-1234-5678 형식만 허용
PHONE_REGEX = r"^010-\d{4}-\d{4}$"
PHONE_MESSAGE = "010-1234-5678 형식으로 입력해 주세요."

phone_validator = RegexValidator(regex=PHONE_REGEX, message=PHONE_MESSAGE)