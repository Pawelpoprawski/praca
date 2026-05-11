"""Drugi przebieg: dodaj font-display do h1/h2 + drobne dekoracyjne fixy."""
import re
import os

SKIP = {
    "app/page.tsx",
    "app/layout.tsx",
    "app/regulamin/page.tsx",
    "app/polityka-prywatnosci/page.tsx",
    "app/login/page.tsx",
    "app/register/page.tsx",
    "app/register/worker/page.tsx",
    "app/register/employer/page.tsx",
    "app/reset-password/page.tsx",
    "app/verify-email/[token]/page.tsx",
    "app/providers.tsx",
    "components/layout/Header.tsx",
    "components/layout/Footer.tsx",
    "components/auth/AuthUI.tsx",
}

# Drobne fixy
SWAPS = [
    # Heading H1/H2 z font-bold ale bez font-display -> dodaj font-display
    # Match tylko gdy juz nie ma font-display
    (r'(<h1\s+className="(?![^"]*font-display)[^"]*?\b)(font-bold|font-extrabold)\b', r'\1\2 font-display'),
    (r'(<h2\s+className="(?![^"]*font-display)[^"]*?\b)(font-bold|font-extrabold|font-semibold)\b', r'\1\2 font-display'),

    # Drobne dekoracje
    (r'🇨🇭\s*Czy wiesz, że', "Czy wiesz, że"),
    (r'🇵🇱\s*', ""),
    (r'🇨🇭\s*', ""),

    # Floating / noise / emoji decoration removal in JobDetail-style headers
    # (kept conservative)

    # text-gray-900 in font-bold + font-display heading -> navy
    (r'(font-display[^"]*?)text-gray-900', r'\1text-[#0D2240]'),
]

src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
os.chdir(src_dir)

count_swaps = {p: 0 for p, _ in SWAPS}
files_changed = 0

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
    for f in files:
        if not f.endswith(".tsx"):
            continue
        rel = os.path.relpath(os.path.join(root, f))
        rel_posix = rel.replace(os.sep, "/")
        if rel_posix in SKIP:
            continue
        try:
            with open(rel, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            continue
        original = content
        for pat, repl in SWAPS:
            new_content, n = re.subn(pat, repl, content)
            if n > 0:
                count_swaps[pat] += n
                content = new_content
        if content != original:
            with open(rel, "w", encoding="utf-8") as fh:
                fh.write(content)
            files_changed += 1

print(f"Files changed: {files_changed}")
for p, c in sorted(count_swaps.items(), key=lambda x: -x[1]):
    if c > 0:
        print(f"  {c:3d}  {p}")
