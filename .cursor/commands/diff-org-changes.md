Compare metadata in a Salesforce org with local source (for orgs without source tracking).

**Full diff (all files):**
```bash
./scripts/diff-org-changes.sh <org-alias>
```

**Single-file diff:**
```bash
./scripts/diff-org-changes.sh <org-alias> <file-path>
```
File path is relative to `src/main/default/`, e.g. `classes/cfp_getDataMovementsFromMetadata.cls` or `flows/cfp_addDefaultDMsToFuncProcess.flow-meta.xml`.

**Input Context:** User provides org alias (default `home-denispoc`) and optionally a file path for single-file diff.
