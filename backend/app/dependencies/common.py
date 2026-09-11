from fastapi import Header, HTTPException


def verify_api_key(
    x_api_key: str | None = Header(default=None)
):
    if x_api_key != "demo-key":
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True