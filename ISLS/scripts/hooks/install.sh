#!/bin/sh
# Installs the tracked git hooks in ISLS/scripts/hooks/ into this
# clone's .git/hooks/ (git does not track .git/hooks/ itself, so this
# has to be run once per clone).
#
# Run: sh ISLS/scripts/hooks/install.sh
set -e

repo_root=$(git rev-parse --show-toplevel)
hooks_src="$repo_root/ISLS/scripts/hooks"
hooks_dst="$repo_root/.git/hooks"

for hook in pre-commit; do
    ln -sf "../../ISLS/scripts/hooks/$hook" "$hooks_dst/$hook"
    chmod +x "$hooks_src/$hook"
    echo "installed $hook -> .git/hooks/$hook"
done
