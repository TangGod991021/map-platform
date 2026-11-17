from typing import Any


def ok(data: Any = None, msg: str = "ok") -> dict[str, Any]:
    return {"code": 200, "msg": msg, "success": True, "data": data}


def page(rows: list[Any], total: int, msg: str = "ok") -> dict[str, Any]:
    return {"code": 200, "msg": msg, "success": True, "rows": rows, "total": total}


def fail(msg: str, code: int = 400) -> dict[str, Any]:
    return {"code": code, "msg": msg, "success": False, "data": None}
