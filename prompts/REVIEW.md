# Codex Review Prompt

Review the current branch against `AGENTS.md` and its task acceptance gates.

Focus on concrete failure modes: private binaries in Git, non-reproducible build steps, hard-coded IDs outside manifests, unguarded ROM writes, address/RAM/save overlap, generated-file hand edits, missing tests, and claims unsupported by reports. Run the checks, fix issues directly, and leave the branch in a mergeable state. Do not return a review-only response when the defects are fixable.
