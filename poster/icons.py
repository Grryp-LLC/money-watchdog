"""Engraving-style line icons for the mugshot slot (no brand logos; trademark-safe)."""

def _svg(body: str) -> str:
    return ('<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" '
            'fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" '
            'stroke-linejoin="round">' + body + '</svg>')

ICONS = {
    "streaming": _svg('<rect x="30" y="60" width="140" height="95" rx="10"/>'
                      '<path d="M75 40l25 20 25-20"/><path d="M88 88v38l32-19z" fill="currentColor"/>'
                      '<path d="M70 172h60"/>'),
    "music": _svg('<path d="M78 145V55l80-18v90"/><circle cx="60" cy="145" r="20"/>'
                  '<circle cx="140" cy="127" r="20"/><path d="M78 80l80-18"/>'),
    "cloud": _svg('<path d="M55 140h95a32 32 0 0 0 0-64 48 48 0 0 0-92 10 28 28 0 0 0-3 54z"/>'
                  '<path d="M100 150v-45M82 122l18-18 18 18"/>'),
    "fitness": _svg('<path d="M60 100h80"/><rect x="36" y="70" width="22" height="60" rx="5"/>'
                    '<rect x="142" y="70" width="22" height="60" rx="5"/><path d="M26 85v30M174 85v30"/>'),
    "phone": _svg('<rect x="62" y="28" width="76" height="144" rx="12"/><path d="M88 46h24"/>'
                  '<circle cx="100" cy="152" r="6" fill="currentColor"/>'),
    "bank": _svg('<path d="M30 80l70-40 70 40z"/><path d="M45 88v60M78 88v60M122 88v60M155 88v60"/>'
                 '<path d="M30 160h140M24 176h152"/>'),
    "shopping": _svg('<path d="M45 70h110l-10 100H55z"/><path d="M75 80V60a25 25 0 0 1 50 0v20"/>'),
    "news": _svg('<rect x="35" y="40" width="130" height="120" rx="6"/><path d="M55 65h90M55 88h40M55 108h40M55 128h90"/>'
                 '<rect x="108" y="84" width="37" height="30"/>'),
    "software": _svg('<rect x="28" y="45" width="144" height="110" rx="8"/><path d="M28 70h144"/>'
                     '<path d="M80 95l-18 18 18 18M120 95l18 18-18 18M108 88l-16 50"/>'),
    "food": _svg('<path d="M65 35v50a15 15 0 0 0 30 0V35M80 35v130"/><path d="M135 165V35c-18 10-22 40-22 65h22"/>'),
    "utility": _svg('<path d="M112 25L55 110h40l-8 65 58-88h-40z"/>'),
    "insurance": _svg('<path d="M100 28l60 22v45c0 38-26 64-60 77-34-13-60-39-60-77V50z"/><path d="M75 100l18 18 34-36"/>'),
    "telecom": _svg('<path d="M100 170V90"/><circle cx="100" cy="80" r="10"/><path d="M70 50a42 42 0 0 0 0 60M130 50a42 42 0 0 1 0 60M50 30a70 70 0 0 0 0 100M150 30a70 70 0 0 1 0 100"/>'),
    "gaming": _svg('<path d="M55 70h90a30 30 0 0 1 29 38l-10 35a15 15 0 0 1-26 5l-18-20H80l-18 20a15 15 0 0 1-26-5l-10-35a30 30 0 0 1 29-38z"/>'
                   '<path d="M65 100h24M77 88v24"/><circle cx="128" cy="95" r="5" fill="currentColor"/><circle cx="142" cy="110" r="5" fill="currentColor"/>'),
    "delivery": _svg('<path d="M25 60h95v80H25zM120 85h32l23 25v30h-55"/><circle cx="55" cy="150" r="14"/><circle cx="145" cy="150" r="14"/>'),
    "generic": _svg('<circle cx="100" cy="100" r="68"/><circle cx="100" cy="100" r="54" stroke-width="3"/>'
                    '<path d="M122 76c-6-9-15-12-24-12-13 0-22 7-22 17 0 24 48 14 48 38 0 11-10 18-24 18-11 0-21-4-27-13M100 50v100"/>'),
}

def icon(category: str) -> str:
    return ICONS.get((category or "generic").lower(), ICONS["generic"])
