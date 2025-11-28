"""Update user roles to USER and ADMIN

Revision ID: c4e8f9a1b2d3
Revises: b9f3a2c4d5e6
Create Date: 2024-11-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c4e8f9a1b2d3'
down_revision: Union[str, Sequence[str], None] = '2357eca0c4e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Update roles from ADMIN/MANAGER/EMPLOYEE to USER/ADMIN."""

    # Step 1: Add a temporary column with varchar type
    op.execute("ALTER TABLE users ADD COLUMN role_new VARCHAR(20)")

    # Step 2: Copy and transform data (ADMIN stays ADMIN, others become USER)
    op.execute("""
        UPDATE users 
        SET role_new = CASE 
            WHEN role = 'ADMIN' THEN 'ADMIN'
            ELSE 'USER'
        END
    """)

    # Step 3: Drop the old column
    op.execute("ALTER TABLE users DROP COLUMN role")

    # Step 4: Create new enum type with USER and ADMIN
    op.execute("CREATE TYPE userroles_new AS ENUM ('USER', 'ADMIN')")

    # Step 5: Add role column back with new enum type
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN role userroles_new 
        NOT NULL 
        DEFAULT 'USER'
    """)

    # Step 6: Copy data from temporary column
    op.execute("""
        UPDATE users 
        SET role = role_new::userroles_new
    """)

    # Step 7: Drop temporary column
    op.execute("ALTER TABLE users DROP COLUMN role_new")

    # Step 8: Drop old enum type and rename new one
    op.execute("DROP TYPE userroles")
    op.execute("ALTER TYPE userroles_new RENAME TO userroles")


def downgrade() -> None:
    """Downgrade schema - Revert back to old roles."""

    # Step 1: Add temporary column
    op.execute("ALTER TABLE users ADD COLUMN role_old VARCHAR(20)")

    # Step 2: Copy and transform data (USER becomes EMPLOYEE, ADMIN stays ADMIN)
    op.execute("""
        UPDATE users 
        SET role_old = CASE 
            WHEN role = 'ADMIN' THEN 'ADMIN'
            ELSE 'EMPLOYEE'
        END
    """)

    # Step 3: Drop the role column
    op.execute("ALTER TABLE users DROP COLUMN role")

    # Step 4: Create old enum type
    op.execute("CREATE TYPE userroles_old AS ENUM ('ADMIN', 'MANAGER', 'EMPLOYEE')")

    # Step 5: Add role column back with old enum
    op.execute("""
        ALTER TABLE users 
        ADD COLUMN role userroles_old 
        NOT NULL 
        DEFAULT 'ADMIN'
    """)

    # Step 6: Copy data from temporary column
    op.execute("""
        UPDATE users 
        SET role = role_old::userroles_old
    """)

    # Step 7: Drop temporary column
    op.execute("ALTER TABLE users DROP COLUMN role_old")

    # Step 8: Drop new enum and rename old one
    op.execute("DROP TYPE userroles")
    op.execute("ALTER TYPE userroles_old RENAME TO userroles")

