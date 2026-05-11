"""Batch swap Tailwind color/radius tokens to Hays palette across .tsx files."""
import re
import os
import sys

# Pliki do pominiecia (juz Hays-style)
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
}

# Kolejnosc waina - bardziej specyficzne najpierw
SWAPS = [
    # Czerwone gradienty -> flat corporate red albo navy
    (r"bg-gradient-to-r from-red-600 via-red-700 to-red-900", "bg-[#E1002A]"),
    (r"bg-gradient-to-r from-red-600 to-red-900", "bg-[#E1002A]"),
    (r"bg-gradient-to-r from-red-600 to-red-700", "bg-[#E1002A]"),
    (r"bg-gradient-to-br from-red-600 via-red-700 to-red-900", "bg-[#0D2240]"),
    (r"bg-gradient-to-br from-red-600 to-red-700", "bg-[#0D2240]"),
    (r"bg-gradient-to-br from-red-50 to-red-100", "bg-[#FFF0F3]"),
    (r"bg-gradient-to-br from-red-100 to-red-200", "bg-[#FFE0E6]"),
    (r"bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50", "bg-[#F5F6F8]"),
    (r"bg-gradient-to-br from-gray-50 to-white", "bg-[#F5F6F8]"),
    (r"bg-gradient-to-r from-blue-600 to-indigo-600", "bg-[#0D2240]"),

    # Red color tokens
    (r"text-red-50\b", "text-[#FFF0F3]"),
    (r"text-red-100\b", "text-white/85"),
    (r"text-red-200\b", "text-white/70"),
    (r"text-red-600\b", "text-[#E1002A]"),
    (r"text-red-700\b", "text-[#B8001F]"),
    (r"text-red-800\b", "text-[#7A0014]"),
    (r"bg-red-50\b", "bg-[#FFF0F3]"),
    (r"bg-red-100\b", "bg-[#FFE0E6]"),
    (r"bg-red-500\b", "bg-[#E1002A]"),
    (r"bg-red-600\b", "bg-[#E1002A]"),
    (r"bg-red-700\b", "bg-[#B8001F]"),
    (r"hover:bg-red-50\b", "hover:bg-[#FFF0F3]"),
    (r"hover:bg-red-100\b", "hover:bg-[#FFE0E6]"),
    (r"hover:bg-red-700\b", "hover:bg-[#B8001F]"),
    (r"hover:text-red-600\b", "hover:text-[#E1002A]"),
    (r"hover:text-red-700\b", "hover:text-[#B8001F]"),
    (r"border-red-200\b", "border-[#FFC2CD]"),
    (r"border-red-300\b", "border-[#E1002A]/40"),
    (r"border-red-400\b", "border-[#E1002A]"),
    (r"border-red-500\b", "border-[#E1002A]"),
    (r"hover:border-red-200\b", "hover:border-[#E1002A]/30"),
    (r"hover:border-red-400\b", "hover:border-[#E1002A]"),
    (r"focus:ring-red-500\b", "focus:ring-[#E1002A]/20"),
    (r"focus:border-red-500\b", "focus:border-[#E1002A]"),
    (r"focus-visible:ring-red-500\b", "focus-visible:ring-[#E1002A]"),
    (r"ring-red-500\b", "ring-[#E1002A]"),

    # Roundedness - Hays max rounded-lg
    (r"rounded-2xl\b", "rounded-lg"),
    (r"rounded-3xl\b", "rounded-lg"),

    # Headings: text-gray-900 in font-bold context (heading) -> navy
    # Tight match: only when paired with text-3xl/4xl/2xl + font-bold
    (r'(text-(?:2xl|3xl|4xl|5xl)[^"]*?)text-gray-900', r"\1text-[#0D2240]"),
]

src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
os.chdir(src_dir)

count_swaps = {p: 0 for p, _ in SWAPS}
files_changed = 0
files_scanned = 0
SEP = os.sep

for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
    for f in files:
        if not f.endswith(".tsx"):
            continue
        rel = os.path.relpath(os.path.join(root, f))
        rel_posix = rel.replace(SEP, "/")
        if rel_posix in SKIP:
            continue
        files_scanned += 1
        try:
            with open(rel, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception as e:
            print(f"  SKIP read err: {rel}: {e}")
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

print(f"Files scanned: {files_scanned}")
print(f"Files changed: {files_changed}")
print()
print("Swap counts (top hits):")
for pat, cnt in sorted(count_swaps.items(), key=lambda x: -x[1]):
    if cnt > 0:
        print(f"  {cnt:4d}  {pat}")
