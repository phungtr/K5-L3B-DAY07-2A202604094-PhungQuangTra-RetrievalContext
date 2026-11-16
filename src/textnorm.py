"""Chuẩn hóa văn bản để so khớp evidence, cùng quy tắc với Day 6 (starter/src/ingestion.py)."""
import re
import unicodedata

# Dấu nháy cong, gạch ngang dài, soft hyphen -> ASCII như lúc Day 6 nạp PDF.
_CHAR_MAP = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"',
                           "–": "-", "—": "-", "­": ""})
_PRIVATE_USE = re.compile("[-]")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_CHAR_MAP)
    return _PRIVATE_USE.sub("•", text)


def canonical(text: str) -> str:
    """Dạng so khớp: chuẩn hóa ký tự, gộp mọi khoảng trắng, không phân biệt hoa thường."""
    return " ".join(normalize(text).split()).casefold()


def contains_evidence(chunk_text: str, evidence: str) -> bool:
    """True nếu chunk chứa TRỌN evidence sau chuẩn hóa; evidence bị cắt qua hai chunk -> False."""
    return canonical(evidence) in canonical(chunk_text)


def exact_span(chunk_text: str, evidence: str) -> str | None:
    """Tìm đoạn nguyên văn trong chunk ứng với evidence (cho phép khác khoảng trắng/dấu nháy).

    Dùng khi chuyển benchmark Day 6 sang schema starter, vốn so khớp bằng `in` không chuẩn hóa.
    """
    target = " ".join(normalize(evidence).split())
    if target in chunk_text:
        return target
    words = [re.escape(w) for w in target.split()]
    match = re.search(r"\s+".join(words), chunk_text, flags=re.IGNORECASE)
    return match.group(0) if match else None
