"""Publish a tested preview to Hex's S3-backed index without overwriting assets."""

import argparse
import base64
import hashlib
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

from preview import INDEX, PREFIX, sha256


def verified_assets(directory: Path, release: str) -> list[Path]:
    """Reject incomplete or altered payloads before making any AWS requests."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", release):
        raise ValueError("Invalid preview identifier")
    checksums = directory / "SHA256SUMS"
    listed: set[str] = set()
    for line in checksums.read_text().splitlines():
        digest, name = line.split("  ", 1)
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or name in listed:
            raise ValueError(f"Invalid checksum path: {name}")
        asset = directory / path
        if asset.is_symlink() or not asset.is_file() or sha256(asset) != digest:
            raise ValueError(f"Checksum mismatch: {name}")
        listed.add(name)
    actual = {
        asset.relative_to(directory).as_posix()
        for asset in directory.rglob("*")
        if asset.is_file()
    }
    required = {
        "requirements.txt",
        "SOURCES.txt",
        "RELEASE_NOTES.md",
        "simple/index.html",
        "simple/apache-ossie/index.html",
        "simple/ossie-hex/index.html",
    }
    if (
        actual != listed | {"SHA256SUMS"}
        or not required <= listed
        or len(list(directory.glob("*-py3-none-any.whl"))) != 2
        or any(asset.is_symlink() for asset in directory.rglob("*"))
    ):
        raise ValueError("Expected a complete preview payload with exactly two wheels")
    if (
        f"--extra-index-url {INDEX}/{PREFIX}/{release}/simple/\n"
        not in (directory / "requirements.txt").read_text()
    ):
        raise ValueError(
            "Installation requirements do not match the preview identifier"
        )
    # Reserve the identity with its checksum manifest before uploading anything
    # else. Publish the installation entry point only after all assets exist.
    return (
        [checksums]
        + sorted(directory / name for name in listed if name != "requirements.txt")
        + [directory / "requirements.txt"]
    )


def upload(asset: Path, command: list[str], bucket: str, key: str) -> None:
    """Allow retries of identical bytes; never replace an existing S3 object."""
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        return
    if "PreconditionFailed" not in result.stderr:
        raise RuntimeError(result.stderr)
    with tempfile.TemporaryDirectory(prefix="ossie-preview-existing-") as temporary:
        existing = Path(temporary) / "object"
        subprocess.run(
            [
                "aws",
                "s3api",
                "get-object",
                "--bucket",
                bucket,
                "--key",
                key,
                str(existing),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        if sha256(existing) != sha256(asset):
            raise ValueError(
                f"Refusing to overwrite a different published object: {key}"
            )
    print(f"Already published identical bytes: {key}")


def main() -> None:
    """Print the upload plan by default; CI explicitly opts into publication."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release")
    parser.add_argument("--assets", type=Path, default=Path("dist/ossie-preview"))
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--kms-key", required=True)
    parser.add_argument("--distribution-id")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.bucket or not args.kms_key:
        raise ValueError("Configure the index bucket and KMS key before publishing")
    if args.execute and not args.distribution_id:
        raise ValueError("Configure CloudFront invalidation before publishing")
    directory = args.assets.resolve()
    assets = verified_assets(directory, args.release)
    for asset in assets:
        key = f"{PREFIX}/{args.release}/{asset.relative_to(directory).as_posix()}"
        content_type = (
            "text/html; charset=utf-8"
            if asset.suffix == ".html"
            else "application/octet-stream"
            if asset.suffix == ".whl"
            else "text/plain; charset=utf-8"
        )
        digest = base64.b64encode(hashlib.sha256(asset.read_bytes()).digest()).decode()
        command = [
            "aws",
            "s3api",
            "put-object",
            "--bucket",
            args.bucket,
            "--key",
            key,
            "--body",
            str(asset),
            "--content-type",
            content_type,
            "--cache-control",
            "public,max-age=31536000,immutable",
            "--server-side-encryption",
            "aws:kms",
            "--ssekms-key-id",
            args.kms_key,
            "--checksum-algorithm",
            "SHA256",
            "--checksum-sha256",
            digest,
            "--if-none-match",
            "*",
        ]
        if args.execute:
            upload(asset, command, args.bucket, key)
        else:
            print(shlex.join(command))
    if args.execute:
        subprocess.run(
            [
                "aws",
                "cloudfront",
                "create-invalidation",
                "--distribution-id",
                args.distribution_id,
                "--paths",
                f"/{PREFIX}/{args.release}/*",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        print(f"Published {INDEX}/{PREFIX}/{args.release}/requirements.txt")
    else:
        print("Dry run only: no AWS requests were made")


if __name__ == "__main__":
    main()
