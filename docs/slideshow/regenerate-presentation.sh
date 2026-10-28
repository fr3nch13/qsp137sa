#!/bin/sh
# Regenerates the PDF and PPTX exports of every Marp deck (Markdown files with
# `marp: true` front matter) in this directory, writing each next to its source.
#
# Usage: docs/slideshow/regenerate-presentation.sh
#
# Requires Node/npx and a local Chrome, Chromium, or Edge. Set CHROME_PATH if
# the browser is not auto-detected. Override MARP_CLI_VERSION to change the
# Marp CLI release (default: latest).
set -eu

marp_cli_version="${MARP_CLI_VERSION:-latest}"
slideshow_dir="$(cd "$(dirname "$0")" && pwd)"
cd "${slideshow_dir}"

found=0
for deck in *.md; do
    grep -q '^marp: true$' "${deck}" || continue
    found=1
    for format in pdf pptx; do
        echo "Exporting ${deck} -> ${deck%.md}.${format}"
        npx -y "@marp-team/marp-cli@${marp_cli_version}" "${deck}" "--${format}" \
            -o "${deck%.md}.${format}"
    done
done

if [ "${found}" -eq 0 ]; then
    echo "No Marp decks found in ${slideshow_dir}" >&2
    exit 1
fi
