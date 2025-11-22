"""Add users table and user_id to contacts

Revision ID: b9f3a2c4d5e6
Revises: 8cf186d1314a
Create Date: 2025-11-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b9f3a2c4d5e6'
down_revision: Union[str, Sequence[str], None] = '8cf186d1314a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=True),
        sa.Column('last_name', sa.String(length=50), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('ADMIN', 'MANAGER', 'EMPLOYEE', name='userroles'),
                  nullable=False, server_default='ADMIN'),
        sa.Column('is_confirmed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('avatar', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Drop the unique constraint on contacts.email (since multiple users can have contacts with same email)
    op.drop_index('ix_contacts_email', table_name='contacts')
    op.create_index(op.f('ix_contacts_email'), 'contacts', ['email'], unique=False)

    # Add user_id column to contacts table
    op.add_column('contacts', sa.Column('user_id', sa.Integer(), nullable=True))

    # Create a default user for existing contacts (if any)
    # First, create a default user
    op.execute("""
        INSERT INTO users (email, first_name, last_name, hashed_password, role, is_confirmed)
        VALUES ('default@example.com', 'Default', 'User', 
                '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5cXCnq6YBqfIi',
                'ADMIN', true)
        ON CONFLICT (email) DO NOTHING
    """)

    # Update existing contacts to have the default user_id
    op.execute("""
        UPDATE contacts 
        SET user_id = (SELECT id FROM users WHERE email = 'default@example.com' LIMIT 1)
        WHERE user_id IS NULL
    """)

    # Make user_id not nullable
    op.alter_column('contacts', 'user_id', nullable=False)

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_contacts_user_id_users',
        'contacts', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop foreign key constraint
    op.drop_constraint('fk_contacts_user_id_users', 'contacts', type_='foreignkey')

    # Drop user_id column from contacts
    op.drop_column('contacts', 'user_id')

    # Restore unique constraint on contacts.email
    op.drop_index(op.f('ix_contacts_email'), table_name='contacts')
    op.create_index('ix_contacts_email', 'contacts', ['email'], unique=True)

    # Drop users table
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')

    # Drop enum type
    op.execute('DROP TYPE userroles')

