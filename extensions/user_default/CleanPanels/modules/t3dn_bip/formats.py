class _BIPFormat:
    """BIP format info."""

    def __init__(self, exts: list, magic: bytes):
        self.exts = exts
        self.magic = magic


BIP_FORMATS = {
    "BIP2": _BIPFormat(
        exts=[".bip", ".bip2"],
        magic=b"BIP2",
    ),
}

MAGIC_LENGTH = max(len(spec.magic) for spec in BIP_FORMATS.values())
