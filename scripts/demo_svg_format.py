"""Shared Rich SVG export format for public demo assets.

KeySurgeon's public demo bitmaps should read as a Windows terminal surface, not
macOS chrome or a platform-neutral mockup. Rich's default SVG title bar uses
traffic-light controls, so this template draws a restrained Windows-style frame
with square minimize/maximize/close controls.
"""

WINDOWS_TERMINAL_SVG_FORMAT = """<svg class="rich-terminal keysurgeon-demo" viewBox="0 0 {terminal_width} {terminal_height}" xmlns="http://www.w3.org/2000/svg">
<!-- Generated with Rich: https://www.textualize.io -->
<style>
@font-face {{
    font-family: "JetBrains Mono";
    src: local("JetBrains Mono"), local("JetBrainsMono-Regular");
    font-style: normal;
    font-weight: 400;
}}
@font-face {{
    font-family: "JetBrains Mono";
    src: local("JetBrains Mono Bold"), local("JetBrainsMono-Bold");
    font-style: normal;
    font-weight: 700;
}}
.{unique_id}-matrix {{
    font-family: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
    font-size: {char_height}px;
    line-height: {line_height}px;
    font-variant-east-asian: full-width;
}}
.{unique_id}-title {{
    font-family: "Segoe UI", "JetBrains Mono", sans-serif;
    font-size: 13px;
    fill: #d8dee9;
}}
.{unique_id}-control {{
    stroke: #d8dee9;
    stroke-width: 1.35;
    fill: none;
    stroke-linecap: square;
}}
.{unique_id}-close {{
    stroke: #ff5a4d;
}}
{styles}
</style>
<defs>
    <clipPath id="{unique_id}-clip-terminal">
      <rect x="0" y="0" width="{terminal_width}" height="{terminal_height}" rx="8" />
    </clipPath>
    {lines}
</defs>
<rect fill="#10151c" x="0" y="0" width="{terminal_width}" height="{terminal_height}" rx="8" />
<rect fill="#1b222c" x="0" y="0" width="{terminal_width}" height="34" rx="7" />
<rect fill="#10151c" x="0" y="30" width="{terminal_width}" height="5" />
<text x="16" y="22" class="{unique_id}-title">KeySurgeon - Windows Terminal</text>
<g transform="translate({terminal_width}, 0)">
    <path class="{unique_id}-control" d="M -104 18 H -94" />
    <rect class="{unique_id}-control" x="-68" y="12" width="10" height="10" />
    <path class="{unique_id}-control {unique_id}-close" d="M -31 12 L -21 22 M -21 12 L -31 22" />
</g>
<g clip-path="url(#{unique_id}-clip-terminal)">
    <g transform="translate(0, 36)">
    {backgrounds}
    <g class="{unique_id}-matrix">
    {matrix}
    </g>
    </g>
</g>
</svg>
"""

# Backward-compatible name for existing render scripts.
CHROMELESS_SVG_FORMAT = WINDOWS_TERMINAL_SVG_FORMAT
