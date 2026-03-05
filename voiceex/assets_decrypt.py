import struct
from pathlib import Path

# From https://github.com/MarshmallowAndroid/UmamusumeExplorer/blob/master/UmamusumeData/UmaDataHelper.cs
META_KEYS = [
    "9c2bab97bcf8c0c4f1a9ea7881a213f6c9ebf9d8d4c6a8e43ce5a259bde7e9fd",
    "a713a5c79dbc9497c0a88669",
]

BASE_KEYS = bytes([0x53, 0x2B, 0x46, 0x31, 0xE4, 0xA7, 0xB9, 0x47, 0x3E, 0x7C, 0xFB])
HEADER_SIZE = 256
SQLITE_MAGIC_U32_LE = 0x694C5153  # "SQLi" little-endian


def build_xor_keys(encryption_key: int) -> bytes:
    key_bytes = struct.pack("<q", int(encryption_key))
    out = bytearray(len(BASE_KEYS) * 8)
    for i, bk in enumerate(BASE_KEYS):
        for j in range(8):
            out[i * 8 + j] = bk ^ key_bytes[j]
    return bytes(out)

def decrypt_assetbundle(raw: bytes, encryption_key: int) -> bytes:
    if encryption_key == 0:
        return raw

    keys = build_xor_keys(encryption_key)
    data = bytearray(raw)

    for i in range(256, len(data)):
        data[i] ^= keys[i % len(keys)]

    return bytes(data)


def is_meta_encrypted(meta_path: Path) -> bool:
    with meta_path.open("rb") as f:
        first4 = f.read(4)
    if len(first4) < 4:
        raise RuntimeError(f"meta file too short: {meta_path}")
    return struct.unpack("<I", first4)[0] != SQLITE_MAGIC_U32_LE
