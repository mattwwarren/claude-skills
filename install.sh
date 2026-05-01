#!/usr/bin/env bash
set -euo pipefail

#
# install.sh -- legacy helper for printing SKILL.md bodies to stdout.
#
# Prefer the Claude Code marketplace install path:
#
#     /plugin marketplace add mattwwarren/claude-skills
#     /plugin install session-management@claude-skills
#
# This script is kept for users who want to paste skill text directly into a
# project's CLAUDE.md. It walks plugins/*/skills/<name>/SKILL.md.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="${SCRIPT_DIR}/plugins"

usage() {
    cat <<'EOF'
Usage: install.sh <skill-name> [options]

Print a skill's SKILL.md body to stdout for piping or appending.

Options:
  --list           List available skills across all plugins
  --all            Print every skill (separated by markers)
  -h, --help       Show this help

Examples:
  ./install.sh handoff                    # Print to terminal
  ./install.sh handoff >> ./CLAUDE.md     # Append to CLAUDE.md
  ./install.sh handoff | pbcopy           # macOS clipboard
  ./install.sh --all >> ./CLAUDE.md       # Install everything

Prefer the marketplace install path:

  /plugin marketplace add mattwwarren/claude-skills
  /plugin install <plugin-name>@claude-skills
EOF
}

# Find the SKILL.md path for a given skill name across plugins. Echoes path or
# nothing.
find_skill() {
    local name="$1"
    local match
    for plugin_dir in "${PLUGINS_DIR}"/*/; do
        match="${plugin_dir}skills/${name}/SKILL.md"
        if [[ -f "$match" ]]; then
            echo "$match"
            return 0
        fi
    done
    return 1
}

list_skills() {
    echo "Available skills:"
    echo ""
    for plugin_dir in "${PLUGINS_DIR}"/*/; do
        plugin_name="$(basename "$plugin_dir")"
        skills_dir="${plugin_dir}skills"
        [[ -d "$skills_dir" ]] || continue
        echo "  [${plugin_name}]"
        for skill_dir in "${skills_dir}"/*/; do
            name="$(basename "$skill_dir")"
            skill_file="${skill_dir}SKILL.md"
            [[ -f "$skill_file" ]] || continue
            # First non-empty, non-frontmatter, non-heading line as description.
            desc=$(awk '
                /^---$/ { in_fm = !in_fm; next }
                in_fm   { next }
                /^#/    { next }
                NF      { print; exit }
            ' "$skill_file")
            printf "    %-20s %s\n" "$name" "$desc"
        done
        echo ""
    done
}

print_skill() {
    local name="$1"
    local skill_file
    if ! skill_file="$(find_skill "$name")"; then
        echo "Error: Unknown skill '${name}'" >&2
        echo "Run './install.sh --list' to see available skills." >&2
        exit 1
    fi
    cat "$skill_file"
}

print_all() {
    for plugin_dir in "${PLUGINS_DIR}"/*/; do
        skills_dir="${plugin_dir}skills"
        [[ -d "$skills_dir" ]] || continue
        for skill_dir in "${skills_dir}"/*/; do
            name="$(basename "$skill_dir")"
            skill_file="${skill_dir}SKILL.md"
            [[ -f "$skill_file" ]] || continue
            echo ""
            echo "<!-- skill: ${name} -->"
            cat "$skill_file"
            echo ""
            echo "<!-- /skill: ${name} -->"
            echo ""
        done
    done
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
