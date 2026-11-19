import hashlib
import re

from allauth.account.utils import user_username
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from allauth.core.exceptions import ImmediateHttpResponse

from .models import Manager, extract_social_phone

# 네이버로그인 username값 없을때
class SocialAdapter(DefaultSocialAccountAdapter):
    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        # 이메일 앞부분 영문소문자+숫자만..16자까지
        email = data.get("email") or user.email or ""
        base = re.sub(r"[^a-z0-9]", "", email.split("@")[0].lower())[:16]

        # 이메일 없으면 provider + uid 해시대체
        if not base:
            provider = sociallogin.account.provider[:2]
            digest = hashlib.sha1(str(sociallogin.account.uid).encode()).hexdigest()[:12]
            base = f"{provider}{digest}"

        user_username(user, self._unique_username(base))
        return user

    def _unique_username(self, base):
        User = get_user_model()
        candidate, n = base, 1
        while User.objects.filter(username__iexact=candidate).exists():
            suffix = str(n)
            candidate = base[: 16 - len(suffix)] + suffix  # 16자까지
            n += 1
        return candidate

    def pre_social_login(self, request, sociallogin):
        phone = extract_social_phone(sociallogin)
        print("[kakao phone]", phone[:5] + "***-****" if phone else repr(phone))

        # 이미 연결된 소셜 계정의 재로그인 -> 통과
        if sociallogin.is_existing:
            print("")
            print("CASE0 이미연결 재로그인")
            return

        # 소셜연결관리의 연결 요청만 통과 (로그인상태라는 이유로 통과X)
        if sociallogin.state.get("process") == "connect":
            print("")
            print(sociallogin.state.get("process"))
            print("CASE1 소셜연결요청")
            return

        # 번호없으면 비교X -> 일반가입
        phone = extract_social_phone(sociallogin)
        if not phone:
            print("")
            print("CASE2 일반가입")
            return

        # 처음보는 번호 -> 새계정 생성
        managers = list(Manager.objects.filter(manager_phone=phone).select_related("user"))
        if not managers:
            print("")
            print("CASE3 새계정생성 ")
            return

        # 같은 번호가 여러 계정에 -> 차단
        if len(managers) == 1 and managers[0].user.socialaccount_set.exists():
            print("")
            print("CASE4 차단")
            # 소셜로 가입한 계정(번호가 provider 제공값) → 자동 연결
            sociallogin.connect(request, managers[0].user)
            print("")
            print("CASE5 소셜 자동연결")
            return

        # 직접 가입 계정 -> 차단하고 안내
        messages.error(
            request,
            "이미 가입된 전화번호입니다. 기존 방식으로 로그인한 뒤 '소셜 계정 연결 관리'에서 추가해 주세요.",
        )
        raise ImmediateHttpResponse(redirect("login"))

    # 기존
    # def pre_social_login(self, request, sociallogin):
    #     phone = extract_social_phone(sociallogin)
    #     print("[kakao phone]", phone[:5] + "***-****" if phone else repr(phone))

    #     # 이미 연결된 소셜 계정의 재로그인이나, 로그인 상태에서의 연결요청은 건드리지 않음
    #     if sociallogin.is_existing or request.user.is_authenticated:
    #         print("")
    #         print("CASE1 이미연결 재로그인")
    #         return

    #     # 번호없으면 비교X -> 일반가입
    #     phone = extract_social_phone(sociallogin)
    #     if not phone:
    #         print("")
    #         print("CASE2 일반가입")
    #         return

    #     # 처음보는 번호 -> 새계정 생성
    #     managers = list(Manager.objects.filter(manager_phone=phone).select_related("user"))
    #     if not managers:
    #         print("")
    #         print("CASE3 새계정생성 ")
    #         return

    #     # 같은 번호가 여러 계정에 -> 차단
    #     if len(managers) == 1 and managers[0].user.socialaccount_set.exists():
    #         print("")
    #         print("CASE4 차단")
    #         # 소셜로 가입한 계정(번호가 provider 제공값) → 자동 연결
    #         sociallogin.connect(request, managers[0].user)
    #         print("")
    #         print("CASE5 소셜 자동연결")
    #         return

    #     # 직접 가입 계정 -> 차단하고 안내
    #     messages.error(
    #         request,
    #         "이미 가입된 전화번호입니다. 기존 방식으로 로그인한 뒤 '소셜 계정 연결 관리'에서 추가해 주세요.",
    #     )
    #     raise ImmediateHttpResponse(redirect("login"))