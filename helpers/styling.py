normal_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def get_char_list(start_lower, start_upper, start_digit=None, exceptions=None):
    if exceptions is None:
        exceptions = {}
    l = []
    for i in range(26):
        c = start_lower + i
        l.append(exceptions.get(c, chr(c)))
    u = []
    for i in range(26):
        c = start_upper + i
        u.append(exceptions.get(c, chr(c)))
    d = []
    if start_digit is not None:
        for i in range(10):
            d.append(chr(start_digit + i))
    return "".join(l), "".join(u), "".join(d)

# 1. Monospace (Typewriter)
mono_l, mono_u, mono_d = get_char_list(0x1D68A, 0x1D670, 0x1D7F6)
mono_map = dict(zip(normal_chars, mono_l + mono_u + mono_d))

# 2. Outline (Double struck)
outline_exceptions = {
    0x1D53A: chr(0x2102), 0x1D53F: chr(0x210D), 0x1D545: chr(0x2115),
    0x1D547: chr(0x2119), 0x1D548: chr(0x211A), 0x1D549: chr(0x211D),
    0x1D551: chr(0x2124),
}
out_l, out_u, out_d = get_char_list(0x1D552, 0x1D538, 0x1D7D8, outline_exceptions)
outline_map = dict(zip(normal_chars, out_l + out_u + out_d))

# 3. Serif Bold
sb_l, sb_u, sb_d = get_char_list(0x1D41A, 0x1D400, 0x1D7CE)
sb_map = dict(zip(normal_chars, sb_l + sb_u + sb_d))

# 4. Serif Italic
si_exceptions = {0x1D455: chr(0x210E)}
si_l, si_u, _ = get_char_list(0x1D44E, 0x1D434, exceptions=si_exceptions)
si_map = dict(zip(normal_chars[:52], si_l + si_u))

# 5. Serif Bold Italic
sbi_l, sbi_u, _ = get_char_list(0x1D482, 0x1D468)
sbi_map = dict(zip(normal_chars[:52], sbi_l + sbi_u))

# 6. Script (Cursive)
script_exceptions = {
    0x1D4BA: chr(0x212F), 0x1D4BC: chr(0x210A), 0x1D4C4: chr(0x2134),
    0x1D49D: chr(0x212C), 0x1D4A0: chr(0x2130), 0x1D4A1: chr(0x2131),
    0x1D4A3: chr(0x210B), 0x1D4A4: chr(0x2110), 0x1D4A7: chr(0x2112),
    0x1D4A8: chr(0x2133), 0x1D4AD: chr(0x211B),
}
sc_l, sc_u, _ = get_char_list(0x1D4B6, 0x1D49C, exceptions=script_exceptions)
sc_map = dict(zip(normal_chars[:52], sc_l + sc_u))

# 7. Script Bold
scb_l, scb_u, _ = get_char_list(0x1D4EA, 0x1D4D0)
scb_map = dict(zip(normal_chars[:52], scb_l + scb_u))

# 8. Sans
sans_l, sans_u, _ = get_char_list(0x1D5BA, 0x1D5A0)
sans_map = dict(zip(normal_chars[:52], sans_l + sans_u))

# 9. Sans Bold
sansb_l, sansb_u, sansb_d = get_char_list(0x1D5EE, 0x1D5D4, 0x1D7EC)
sansb_map = dict(zip(normal_chars, sansb_l + sansb_u + sansb_d))

# 10. Sans Italic
sansi_l, sansi_u, _ = get_char_list(0x1D622, 0x1D608)
sansi_map = dict(zip(normal_chars[:52], sansi_l + sansi_u))

# 11. Sans Bold Italic
sansbi_l, sansbi_u, _ = get_char_list(0x1D656, 0x1D63C)
sansbi_map = dict(zip(normal_chars[:52], sansbi_l + sansbi_u))

# 12. Gothic (Fraktur)
gothic_exceptions = {
    0x1D506: chr(0x212D), 0x1D50B: chr(0x210C), 0x1D50C: chr(0x2111),
    0x1D515: chr(0x211C), 0x1D51D: chr(0x2128),
}
goth_l, goth_u, _ = get_char_list(0x1D51E, 0x1D504, exceptions=gothic_exceptions)
goth_map = dict(zip(normal_chars[:52], goth_l + goth_u))

# 13. Gothic Bold
gothb_l, gothb_u, _ = get_char_list(0x1D586, 0x1D56C)
gothb_map = dict(zip(normal_chars[:52], gothb_l + gothb_u))

# 14. Circles
circ_l = "ⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ"
circ_u = "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏ"
circ_d = "⓪①②③④⑤⑥⑦⑧⑨"
circ_map = dict(zip(normal_chars, circ_l + circ_u + circ_d))

# 15. Dark Circles
dcirc_l = "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩"
dcirc_u = "🅐🅑🅒🅓🅔🅕🅖🅗🅘🅙🅚🅛🅜🅝🅞🅟🅠🅡🅢🅣🅤🅥🅦🅧🅨🅩"
dcirc_d = "⓪❶❷❸❹❺❻❼❽❾"
dcirc_map = dict(zip(normal_chars, dcirc_l + dcirc_u + dcirc_d))

# 16. Small Caps
scaps_l = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
scaps_u = "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘQʀꜱᴛᴜᴠᴡxʏᴢ"
scaps_map = dict(zip(normal_chars[:52], scaps_l + scaps_u))

# 17. Comic (Squares)
sq_u = "".join(chr(0x1F130 + i) for i in range(26))
sq_map = dict(zip(normal_chars[:52], sq_u.lower() + sq_u))

# 18. Tiny (Superscript)
tiny_map = {
    'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ', 'h': 'ʰ',
    'i': 'ⁱ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ', 'm': 'ᵐ', 'n': 'ⁿ', 'o': 'ᵒ', 'p': 'ᵖ',
    'q': 'ᵠ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ', 'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ',
    'y': 'ʸ', 'z': 'ᶻ',
    'A': 'ᴬ', 'B': 'ᴮ', 'C': 'ᶜ', 'D': 'ᴰ', 'E': 'ᴱ', 'F': '𝘍', 'G': 'ᴳ', 'H': 'ᴴ',
    'I': 'ᴵ', 'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ', 'M': 'ᴹ', 'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ',
    'Q': 'ᵠ', 'R': 'ᴿ', 'S': 'ˢ', 'T': 'ᵀ', 'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ', 'X': 'ˣ',
    'Y': 'ʸ', 'Z': 'ᶻ'
}

MAPS = {
    "typewriter": mono_map,
    "outline": outline_map,
    "serif bold": sb_map,
    "serif italic": si_map,
    "serif bold italic": sbi_map,
    "small caps": scaps_map,
    "script": sc_map,
    "script bold": scb_map,
    "tiny": tiny_map,
    "comic": sq_map,
    "sans": sans_map,
    "sans bold": sansb_map,
    "sans italic": sansi_map,
    "sans bold italic": sansbi_map,
    "circles": circ_map,
    "dark circles": dcirc_map,
    "gothic": goth_map,
    "gothic bold": gothb_map,
}

# Reverse mapping for de-stylizing
REVERSE_MAP = {}
for style_name, mapping in MAPS.items():
    for k, v in mapping.items():
        if v not in REVERSE_MAP:
            REVERSE_MAP[v] = k

# Add fallback mappings for spaced text
spaced_map = {}
for i, c in enumerate("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    spaced_map[c] = chr(0xFF41 + i) if c.islower() else chr(0xFF21 + (i - 26))

# Helper Functions
def de_stylize(text: str) -> str:
    clean_text = ""
    for char in text:
        if char in ["\u0330", "\u0332", "\u0333", "\u0336", "\u033f", "\u0347"]:
            continue
        clean_text += REVERSE_MAP.get(char, char)
    return clean_text

def apply_font(text: str, font_name: str) -> str:
    font_name = font_name.lower()
    if font_name == "clouds":
        return "".join(c + "\u0332" for c in de_stylize(text))
    elif font_name == "happy":
        return "".join(c + "\u0336" for c in de_stylize(text))
    elif font_name == "sad":
        return "".join(c + "\u0333" for c in de_stylize(text))
    
    mapping = MAPS.get(font_name)
    if not mapping:
        return text
    
    clean_text = de_stylize(text)
    return "".join(mapping.get(c, c) for c in clean_text)

# Compatibility wrappers for existing code
def small_caps(text: str) -> str:
    return "".join(scaps_map.get(c, c) for c in text)

def fraktur(text: str) -> str:
    return "".join(goth_map.get(c, c) for c in text)

def spaced_text(text: str) -> str:
    return "".join(spaced_map.get(c, c) for c in text)
