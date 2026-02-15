#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${SCRIPT_DIR}/skills"

usage() {
    cat <<'EOF'
Usage: install.sh <skill-name> [options]

Print a skill's system prompt snippet to stdout for piping or appending.

Skills:
  handoff          Session handoff generation for abnormal endings
  plan-executor    Agent-spawning plan executor with phase orchestration
  debug-triage     Structured debugging with issue tracking and escalation

Options:
  --list           List available skills
  --all            Print all skills (separated by markers)
  -h, --help       Show this help

Examples:
  ./install.sh handoff                    # Print to terminal
  ./install.sh handoff >> ./CLAUDE.md     # Append to CLAUDE.md
  ./install.sh handoff | pbcopy           # macOS clipboard
  ./install.sh --all >> ./CLAUDE.md       # Install everything
EOF
}

list_skills() {
    echo "Available skills:"
    echo ""
    for dir in "${SKILLS_DIR}"/*/; do
        name="$(basename "$dir")"
        if [[ -f "${dir}/SKILL.md" ]]; then
            # Extract first non-empty, non-heading line as description
            desc=$(grep -m1 -v '^\(#\|$\)' "${dir}/SKILL.md" | head -1)
            printf "  %-20s %s\n" "$name" "$desc"
        fi
    done
}

print_skill() {
    local name="$1"
    local skill_file="${SKILLS_DIR}/${name}/SKILL.md"

    if [[ ! -f "$skill_file" ]]; then
        echo "Error: Unknown skill '${name}'" >&2
        echo "Run './install.sh --list' to see available skills." >&2
        exit 1
    fi

    cat "$skill_file"
}

print_all() {
    for dir in "${SKILLS_DIR}"/*/; do
        name="$(basename "$dir")"
        if [[ -f "${dir}/SKILL.md" ]]; then
            echo ""
            echo "<!-- skill: ${name} -->"
            cat "${dir}/SKILL.md"
            echo ""
            echo "<!-- /skill: ${name} -->"
            echo ""
        fi
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
