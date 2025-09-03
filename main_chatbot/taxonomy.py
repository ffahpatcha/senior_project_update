# taxonomy.py
import unicodedata as ud
import re
from typing import Dict, Set

# ---------- canonical allowed pairs ----------
ALLOWED: Dict[str, Set[str]] = {
    "หัตถการ": {
        "extraction",
        "surgical removal of impacted teeth",
        "dental implant surgery",
    },
    "อาการภาวะแทรกซ้อน": {
        "Physical Symptoms",
        "Digestive and Body Reactions",
        "Wound and Infection",
        "Respiratory and Throat",
    },
    "การปฏิบัติตัวหลังทำหัตถการ": {
        "all rounded post op instruction",
        "sleeping",
        "drinking straw",
        "smoking",
        "alcohol",
        "workout",
        "food",
        "oral hygiene",
        "compression",
        "medicine",
    },
}

# ---------- mapping แก้ชื่อที่มักพิมพ์ไม่ตรง → canonical ----------
# mapping แก้ชื่อที่มักพิมพ์ไม่ตรง → canonical
L1_MAP: Dict[str, str] = {
    "อาการ/ภาวะแทรกซ้อน": "อาการภาวะแทรกซ้อน",
    "อาการ ภาวะแทรกซ้อน": "อาการภาวะแทรกซ้อน",
    # รูปแตกของ "ทำ" → map กลับ
    "การปฏิบัติตัวหลังทําหัตถการ": "การปฏิบัติตัวหลังทำหัตถการ",
}


# เคสเฉพาะที่อยาก override แบบจงใจ (ตรงตัว ก่อนเข้ากระบวนการ simplify อัตโนมัติ)
L2_MAP: Dict[str, str] = {
    "wound and infection": "Wound and Infection",
    "oral  hygiene": "oral hygiene",
    "drinking-straw": "drinking straw",
    # เติมได้ตามที่เจอบ่อย
}

# ---------- utils ----------
def _collapse_ws(s: str) -> str:
    return " ".join((s or "").strip().split())
def _fix_thai_sara_am(s: str) -> str:
    # แปลง นิกคหิต+สระอา (U+0E4D U+0E32) ให้กลับเป็น สระอำ (U+0E33)
    # เผื่อมีหลายตำแหน่ง
    return s.replace("\u0E4D\u0E32", "\u0E33")
def norm(s: str) -> str:
    # ใช้ NFC เพื่อคงรูปสระอำไว้ ไม่แตกเป็น 0E4D+0E32
    s = ud.normalize("NFC", s or "")
    s = _fix_thai_sara_am(s)
    return _collapse_ws(s)

def _simplify_l2(s: str) -> str:
    """
    ทำให้รูปแบบสตริง L2 ‘ใจดี’ ขึ้นเพื่อจับคู่:
    - case-insensitive (casefold)
    - แทน '-' '_' '/' ด้วยช่องว่าง
    - เก็บเฉพาะตัวอักษร/ตัวเลข/ไทย กับช่องว่าง (เครื่องหมายอื่นให้เป็นช่องว่าง)
    - รวมช่องว่างซ้อน
    """
    s = ud.normalize("NFKC", s or "")
    s = s.casefold()
    # แทนที่เครื่องหมายเชื่อมทั่วไปด้วยช่องว่าง
    s = s.replace("-", " ").replace("_", " ").replace("/", " ")
    # เก็บเฉพาะอักษร/ตัวเลข/ไทย และช่องว่าง
    s = re.sub(r"[^\w\u0E00-\u0E7F\s]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

# ---------- canonicalizers ----------
def canonical_l1(s: str) -> str:
    s = norm(s)
    s = _fix_thai_sara_am(s)  # กันเคสแปลก ๆ อีกรอบ
    return L1_MAP.get(s, s)


# สร้างดิกชันนารีสำหรับแมป ‘simplified key’ → canonical L2
_L2_CANON_BY_SIMPLE: Dict[str, str] = {}
for _l1, _l2_set in ALLOWED.items():
    for _l2 in _l2_set:
        _L2_CANON_BY_SIMPLE[_simplify_l2(_l2)] = _l2

def canonical_l2(s: str) -> str:
    # 1) exact override ก่อน (รองรับช่องว่างเกิน/ตัวพิมพ์ไม่ตรงที่กำหนดไว้เอง)
    s_norm = norm(s)
    if s_norm in L2_MAP:
        return L2_MAP[s_norm]

    # 2) จับคู่แบบใจดีด้วย simplified key ที่สร้างจาก ALLOWED
    key = _simplify_l2(s_norm)
    if key in _L2_CANON_BY_SIMPLE:
        return _L2_CANON_BY_SIMPLE[key]

    # 3) ถ้าไม่แมตช์ก็คืนค่าที่ normalize แล้ว (ให้ valid_pair ตัดสินต่อ)
    return s_norm

# ---------- validators ----------
def valid_pair(l1: str, l2: str) -> bool:
    l1c, l2c = canonical_l1(l1), canonical_l2(l2)
    return l1c in ALLOWED and l2c in ALLOWED[l1c]

def cat_key(l1: str, l2: str) -> str:
    return f"{canonical_l1(l1)}|{canonical_l2(l2)}"
