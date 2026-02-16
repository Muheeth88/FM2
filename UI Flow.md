# UI Flow

# 🖥 COMPLETE UI FLOW

---

# SCREEN 1 — Dashboard

Shows:

| Session | Features | Migrated | Failed | Conflicted | Needs Update | PR Status |

---

# SCREEN 2 — New Migration Wizard

1. Framework select
2. Repo input
3. Analyze

---

# SCREEN 3 — Feature Selection

Table:

| Feature | Status | Last Migrated | Conflict | Needs Update |

Badges:

- MIGRATED (green)
- NEEDS_UPDATE (yellow)
- CONFLICTED (red)
- NOT_MIGRATED (gray)

Bulk select options.

---

# SCREEN 4 — Migration Progress

Live step tracking:

| Feature | Current Step | Status |

---

# SCREEN 5 — Migration Summary

After generation:

```
Features Migrated:3Files Added:12Files Modified:5Insertions:+420Deletions:-110
```

Buttons:

- View Diff
- Raise PR
- Abort

---

# SCREEN 6 — Diff Viewer

Left:

File list with change stats.

Right:

Unified diff view.

Filter:

- Only added
- Only modified
- Only deleted

---

# SCREEN 7 — PR Summary

After PR:

Show:

- PR URL
- Branch
- Files changed
- Validation summary
