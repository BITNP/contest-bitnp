"""Authentication backend for CAS"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django_cas_ng.backends import CASBackend as AbstractCASBackend

from .models import Student

if TYPE_CHECKING:
    from django_cas_ng.backends import User


class CASBackend(AbstractCASBackend):
    """Authentication backend for CAS"""

    def configure_user(self, user: User) -> User:
        """CAS 自动创建 User 后，继续建立 Student"""
        # todo: Not all users are students.
        Student.objects.create(
            user=user,  # type: ignore[misc]
            name=user.first_name + user.last_name or user.username,
        )
        # `AbstractCASBackend`中`User`被标注为标准`User`，
        # 而`Student`需要自定义的，导致虚警。
        # `AbstractCASBackend`实际会用`django.contrib.auth.get_user_model`，
        # 遵从`settings.AUTH_USER_MODEL`，并无问题。

        return super().configure_user(user)
