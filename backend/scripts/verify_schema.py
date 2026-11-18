import sys
import os
sys.path.insert(0, "backend")

from app.core.database import sync_engine
from sqlalchemy import inspect

inspector = inspect(sync_engine)
tables = inspector.get_table_names()

print("=" * 60)
print("   CLINICFLOW RELATIONAL DATABASE SCHEMA VERIFICATION   ")
print("=" * 60)

for t in sorted(tables):
    print(f"\n[TABLE] {t.upper()}")
    cols = inspector.get_columns(t)
    for c in cols:
        nullable = "NULLABLE" if c.get("nullable") else "NOT NULL"
        pk = " [PK]" if c.get("primary_key") else ""
        print(f"  • {c['name']:<24} : {str(c['type']):<18} {nullable}{pk}")

    fks = inspector.get_foreign_keys(t)
    if fks:
        print("  Foreign Key Constraints:")
        for fk in fks:
            print(f"    └── {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

    indexes = inspector.get_indexes(t)
    if indexes:
        print("  Indexes & Uniqueness:")
        for idx in indexes:
            unq = "UNIQUE INDEX" if idx.get("unique") else "INDEX"
            print(f"    └── {unq}: {idx['name']} ({', '.join(idx['column_names'])})")

print("\n" + "=" * 60)
print(f"Total verified tables: {len(tables)}")
print("=" * 60)
