#!/usr/bin/env bash
# Legacy snippet-mode installer for the claude-skills marketplace.
#
# Prints a skill's SKILL.md to stdout for piping into CLAUDE.md.
# For full plugin install (with agents/commands/scripts) use:
#   /plugin marketplace add mattwwarren/claude-skills
#   /plugin install <plugin>@claude-skills
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="${SCRIPT_DIR}/plugins"

# Find SKILL.md by skill name across all plugins.
find_skill_file() {
    local name="$1"
    local match
    match=$(find "${PLUGINS_DIR}" -mindepth 4 -maxdepth 4 \
        -type f -path "*/skills/${name}/SKILL.md" 2>/dev/null | head -1)
    [[ -n "${match}" ]] && echo "${match}"
}

# Iterate all SKILL.md files in plugin-name order, skill-name order.
each_skill() {
    find "${PLUGINS_DIR}" -mindepth 4 -maxdepth 4 \
        -type f -name SKILL.md -path "*/skills/*/SKILL.md" 2>/dev/null | sort
}

list_skills() {
    while read -r skill_file; do
        [[ -z "${skill_file}" ]] && continue
        local skill_dir plugin_dir name plugin desc
        skill_dir="$(dirname "${skill_file}")"
        plugin_dir="$(dirname "$(dirname "${skill_dir}")")"
        name="$(basename "${skill_dir}")"
        plugin="$(basename "${plugin_dir}")"
        # Description: prefer frontmatter, fall back to first prose line.
        desc=$(awk '
            /^---$/ { in_fm = !in_fm; next }
            in_fm && /^description:/ { sub(/^description: */, ""); print; exit }
        ' "${skill_file}")
        if [[ -z "${desc}" ]]; then
            desc=$(grep -m1 -v '^\(#\|---\|$\)' "${skill_file}" | head -1)
        fi
        printf "%-20s [%s] %s\n" "${name}" "${plugin}" "${desc}"
    done < <(each_skill)
}

usage() {
    cat <<'EOF'
Usage: install.sh <skill-name> [options]

Print a skill's SKILL.md to stdout for piping or appending to CLAUDE.md.

For full plugin installation (agents, commands, scripts), use Claude Code's
plugin marketplace instead:

  /plugin marketplace add mattwwarren/claude-skills
  /plugin install review-pipeline@claude-skills

Skills (auto-discovered):
EOF
    list_skills | sed 's/^/  /'
    cat <<'EOF'

Options:
  --list           List available skills with descriptions
  --all            Print all skills (separated by markers)
  -h, --help       Show this help

Examples:
  ./install.sh handoff                    # Print to terminal
  ./install.sh handoff >> ./CLAUDE.md     # Append to CLAUDE.md
  ./install.sh handoff | pbcopy           # macOS clipboard
  ./install.sh --all >> ./CLAUDE.md       # Install everything
EOF
}

print_skill() {
    local name="$1"
    local skill_file
    skill_file="$(find_skill_file "${name}")"

    if [[ -z "${skill_file}" ]]; then
        echo "Error: Unknown skill '${name}'" >&2
        echo "Run './install.sh --list' to see available skills." >&2
        exit 1
    fi

    cat "${skill_file}"
}

print_all() {
    while read -r skill_file; do
        [[ -z "${skill_file}" ]] && continue
        local name
        name="$(basename "$(dirname "${skill_file}")")"
        echo ""
        echo "<!-- skill: ${name} -->"
        cat "${skill_file}"
        echo ""
        echo "<!-- /skill: ${name} -->"
        echo ""
    done < <(each_skill)
}

if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

case "$1" in
    --list)
        list_skills
        ;;
    --all)
        print_all
        ;;
    -h|--help)
        usage
        ;;
    *)
        print_skill "$1"
        ;;
esac
