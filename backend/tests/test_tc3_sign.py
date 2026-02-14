from app.infra.tc3 import sign_tc3


def test_sign_tc3_headers_shape():
    headers, canonical = sign_tc3(
        service="tcb",
        host="tcb.tencentcloudapi.com",
        region="ap-shanghai",
        action="CommonServiceAPI",
        version="2018-06-08",
        secret_id="AKIDEXAMPLE",
        secret_key="SECRET",
        payload={"EnvId": "env-1", "Service": "database", "Action": "Ping", "Data": {}},
        timestamp=1725753600,  # fixed timestamp
    )
    assert headers["X-TC-Action"] == "CommonServiceAPI"
    assert headers["X-TC-Version"] == "2018-06-08"
    assert headers["X-TC-Region"] == "ap-shanghai"
    assert headers["Host"] == "tcb.tencentcloudapi.com"
    assert headers["Authorization"].startswith("TC3-HMAC-SHA256 ")

