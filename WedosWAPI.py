# WedosWAPI.py
import hashlib
import json
import uuid
from datetime import datetime
import pytz
import requests

class WedosWAPI:
    """
    Basic WEDOS WAPI client (JSON).
    Usage:
        client = WedosWAPI(user='you@example.tld', wapi_password='WAPI_PASSWORD')
        resp = client.ping()
        print(resp)
    """

    JSON_URL = "https://api.wedos.com/wapi/json"
    XML_URL = "https://api.wedos.com/wapi/xml"

    def __init__(self, user: str, wapi_password: str, *,
                 use_json: bool = True, timeout: int = 60):
        self.user = user
        self.wapi_password = wapi_password
        self.use_json = use_json
        self.timeout = timeout
        self._tz = pytz.timezone("Europe/Prague")

    def _current_hour_str(self) -> str:
        """Hour in Europe/Prague timezone, zero-padded 00-23 (same as PHP date('H'))."""
        return datetime.now(self._tz).strftime("%H")

    def _auth_string(self) -> str:
        """
        auth = sha1(user + sha1(wapi_password) + currentHour)
        (currentHour is 00-23 in Europe/Prague)
        """
        inner = hashlib.sha1(self.wapi_password.encode("utf-8")).hexdigest()
        to_hash = f"{self.user}{inner}{self._current_hour_str()}"
        return hashlib.sha1(to_hash.encode("utf-8")).hexdigest()

    def _endpoint(self) -> str:
        return self.JSON_URL if self.use_json else self.XML_URL

    def _build_request(self, command: str, data: dict | None = None,
                       clTRID: str | None = None, test: bool | None = None) -> dict:
        req = {
            "user": self.user,
            "auth": self._auth_string(),
            "command": command
        }
        if data is not None:
            req["data"] = data
        if clTRID is None:
            clTRID = str(uuid.uuid4())
        req["clTRID"] = clTRID
        if test is not None:
            req["test"] = 1 if test else 0
        return {"request": req}

    def _post(self, payload: dict) -> dict:
        """
        Send request to WAPI. WAPI expects a single POST field named 'request'
        containing the JSON (URL-encoded form).
        """
        url = self._endpoint()
        body = json.dumps(payload, ensure_ascii=False)
        # send as form data: request=<json>
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = requests.post(url, data={"request": body}, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        # Expect JSON response when using JSON endpoint
        return resp.json()

    def request(self, command: str, data: dict | None = None, *,
                clTRID: str | None = None, test: bool | None = None) -> dict:
        """
        Generic request helper. Returns parsed JSON response.
        """
        payload = self._build_request(command=command, data=data, clTRID=clTRID, test=test)
        return self._post(payload)

    # Convenience methods
    def ping(self, *, clTRID: str | None = None) -> dict:
        return self.request("ping", clTRID=clTRID)

    # Provides domains list
    def domains_list(self) -> dict:
        return self.request("domains-list")

    # Provides domain info
    def domain_info(self, domain: str) -> dict:
        data = {"name": domain}
        return self.request("domain-info", data)
    
    # Provides domains list with DNS records
    def dns_domains_list(self) -> dict:
        return self.request("dns-domains-list")

    # Provides DNS domain information
    def dns_domain_info(self, domain: str) -> dict:
        data = {"name": domain}
        return self.request("dns-domains-list", data)

    # Provides DNS domain DNS records
    def dns_rows_list(self, domain: str) -> dict:
        data = {"domain": domain}
        return self.request("dns-rows-list", data)

    # Provides top level/root DNS domain DNS records
    def dns_get_top_level_records(self, domain: str) -> dict:
        data = {"domain": domain}
        response = self.request("dns-rows-list", data)
        records = []
        for row in response['response']['data']['row']:
            if row['name'] == '':
                records.append(row)
        return records

    # Adds new domain DNS record
    def dns_row_add(self, domain: str, name: str, ttl: str, type: str, rdata: str) -> dict:
        data = {"domain": domain, "name": name, "ttl": ttl, "type": type, "rdata": rdata}
        return self.request("dns-row-add", data)

    # Commits DNS domain changes
    def dns_domain_commit(self, domain: str) -> dict:
        data = {"name": domain}
        return self.request("dns-domain-commit", data)

    # Updates existing domain DNS record
    def dns_row_update(self, domain: str, row_id: int, ttl: str, rdata: str) -> dict:
        data = {"domain": domain, "row_id": row_id, "ttl": ttl, "rdata": rdata}
        return self.request("dns-row-update", data)

    # Deletes existing domain DNS record
    def dns_row_delete(self, domain: str, row_id: int) -> dict:
        data = {"domain": domain, "row_id": row_id}
        return self.request("dns-row-delete", data)




