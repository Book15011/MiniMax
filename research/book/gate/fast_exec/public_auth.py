"""Explicitly suppress implicit netrc/account authentication on public observations."""
from requests.auth import AuthBase
class PublicAuth(AuthBase):
    def __call__(self,request):return request
