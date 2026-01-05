#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import uuid
from typing import Any, Dict, Iterable, Tuple


def _js_stringify(value: Any) -> str:
    """
    Mimic the JS `${value}` behavior used in:
      "".concat(key, "=").concat(obj[key], "&")
    enough for the request params seen in this mini-program.
    """

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # JS number -> string (close enough for typical request params).
        # Keep Python's default string form.
        return str(value)
    if isinstance(value, (list, tuple)):
        # JS Array#toString() => elements joined by comma
        return ",".join(_js_stringify(v) for v in value)
    if isinstance(value, dict):
        # JS default Object#toString() => "[object Object]"
        return "[object Object]"
    return str(value)


def generate_nonce() -> str:
    """UUID v4 with hyphens (same shape as `uuid.v4()` in JS)."""

    return str(uuid.uuid4())


def generate_timestamp_ms() -> int:
    """13-digit milliseconds timestamp, like `(new Date()).getTime()`."""

    return int(time.time() * 1000)


def canonical_query(params: Dict[str, Any]) -> str:
    """
    Canonicalize request data the same way the mini-program does before signing:
    - keys are sorted ascending (Object.keys(obj).sort())
    - null/undefined are deleted before signing
    - string is built as: k1=v1&k2=v2...
      (no URL encoding)
    """

    pairs: list[str] = []
    for key in sorted(params.keys()):
        value = params[key]
        # In JS: null/undefined -> delete
        if value is None:
            continue
        pairs.append(f"{key}={_js_stringify(value)}")
    return "&".join(pairs)


def md5_hex_lower(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def get_x_ca_signature(params: Dict[str, Any]) -> str:
    """
    Reproduce app's `getSignature`:

      md5_1 = md5(canonical_query(params))
      sig   = md5(md5_1 + params.timestamp).toUpperCase()
    """

    if "timestamp" not in params:
        raise ValueError("params must contain `timestamp` (ms) before signing")

    canonical = canonical_query(params)
    md5_1 = md5_hex_lower(canonical)
    md5_2 = md5_hex_lower(f"{md5_1}{_js_stringify(params['timestamp'])}")
    return md5_2.upper()


def build_signed_params(
    data: Dict[str, Any],
    *,
    nonce: str | None = None,
    timestamp_ms: int | None = None,
) -> Tuple[Dict[str, Any], str, int, str]:
    """
    Return (params_with_nonce_timestamp, nonce, timestamp_ms, x_ca_signature)
    """

    nonce = nonce or generate_nonce()
    timestamp_ms = int(timestamp_ms if timestamp_ms is not None else generate_timestamp_ms())

    params = dict(data)
    params["timestamp"] = timestamp_ms
    params["nonce"] = nonce

    signature = get_x_ca_signature(params)
    return params, nonce, timestamp_ms, signature


def _parse_data_json(data_json: str | None) -> Dict[str, Any]:
    if not data_json:
        return {}
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid --data-json: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("--data-json must be a JSON object, e.g. '{\"a\":1}'")
    return data


def _parse_kv_pairs(pairs: Iterable[str]) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    for raw in pairs:
        if "=" not in raw:
            raise SystemExit(f"Invalid --data item (expected key=value): {raw!r}")
        key, value_raw = raw.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"Invalid --data item (empty key): {raw!r}")

        value_raw = value_raw.strip()
        if value_raw == "":
            data[key] = ""
            continue

        # Try to parse primitive JSON (numbers/true/false/null/"string").
        # If it fails, keep as raw string (e.g. "0,1").
        try:
            data[key] = json.loads(value_raw)
        except json.JSONDecodeError:
            data[key] = value_raw
    return data


def main(argv: Iterable[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Generate `nonce` and `X-Ca-Signature` exactly like the mini-program.",
    )
    parser.add_argument(
        "--data",
        action="append",
        default=[],
        help="Request body parameter as key=value (repeatable), e.g. --data page=2 --data stubGroupTypes=0,1",
    )
    parser.add_argument(
        "--data-file",
        help="Read request body parameters from a JSON file (object at top-level).",
    )
    parser.add_argument(
        "--data-stdin",
        action="store_true",
        help="Read request body parameters from stdin as JSON (object).",
    )
    parser.add_argument(
        "--data-json",
        help='Request body parameters as JSON object, e.g. \'{"page":1,"stubGroupTypes":"0,1"}\'',
    )
    parser.add_argument("--nonce", help="Use a fixed nonce (UUIDv4). If omitted, generate one.")
    parser.add_argument(
        "--timestamp",
        type=int,
        help="Use a fixed timestamp in ms. If omitted, use current time in ms.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print canonical string and intermediate md5 values (for verification).",
    )

    args = parser.parse_args(list(argv))

    data: Dict[str, Any] = {}
    if args.data_file:
        try:
            with open(args.data_file, "r", encoding="utf-8") as f:
                file_obj = json.loads(f.read())
        except OSError as exc:
            raise SystemExit(f"Cannot read --data-file: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in --data-file: {exc}") from exc
        if not isinstance(file_obj, dict):
            raise SystemExit("--data-file JSON must be an object at top-level")
        data.update(file_obj)

    if args.data_stdin:
        try:
            stdin_obj = json.loads(sys.stdin.read())
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON from stdin: {exc}") from exc
        if not isinstance(stdin_obj, dict):
            raise SystemExit("stdin JSON must be an object at top-level")
        data.update(stdin_obj)

    # This option is convenient on Unix shells; on Windows PowerShell, passing JSON with
    # embedded double-quotes can be lossy for native executables, so prefer --data / --data-file.
    data.update(_parse_data_json(args.data_json))

    data.update(_parse_kv_pairs(args.data))

    params, nonce, timestamp_ms, signature = build_signed_params(
        data,
        nonce=args.nonce,
        timestamp_ms=args.timestamp,
    )

    out: Dict[str, Any] = {
        "nonce": nonce,
        "timestamp": timestamp_ms,
        "x_ca_signature": signature,
    }

    if args.debug:
        canonical = canonical_query(params)
        md5_1 = md5_hex_lower(canonical)
        md5_2 = md5_hex_lower(f"{md5_1}{_js_stringify(params['timestamp'])}").upper()
        out.update(
            {
                "canonical": canonical,
                "md5_1": md5_1,
                "md5_2": md5_2,
            }
        )

    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
