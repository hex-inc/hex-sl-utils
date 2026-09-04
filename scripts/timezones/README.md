# Timezone mapping generation

Translates IANA timezone names to the Windows names required by MS SQL Server.
The committed mapping is generated from the Unicode CLDR commit that was current
when HexSL introduced the mapping, so builds remain reproducible.

Regenerate the mapping from the repository root:

```bash
just build-timezones
```

Check that the committed artifact matches the pinned CLDR source:

```bash
just verify-timezones
```

Both commands require network access to the pinned Unicode CLDR source. To
update CLDR, change `CLDR_COMMIT` in `generate_iana_to_windows.py`, regenerate
the mapping, and review the resulting data changes.
