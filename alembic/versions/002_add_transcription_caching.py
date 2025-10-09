"""Add transcription caching support

Revision ID: 002
Revises: 001
Create Date: 2025-10-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'  # Replace with actual previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    """Add user_id and file_hash columns to audio_transcriptions table."""

    # Add new columns to audio_transcriptions table
    with op.batch_alter_table('audio_transcriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('file_hash', sa.String(length=64), nullable=True))

        # Add indexes for better performance
        batch_op.create_index('ix_audio_transcriptions_user_id', ['user_id'])
        batch_op.create_index('ix_audio_transcriptions_file_hash', ['file_hash'])

        # Add foreign key constraint
        batch_op.create_foreign_key(
            'fk_audio_transcriptions_user_id',
            'users',
            ['user_id'],
            ['id']
        )

    # Update existing records to have a default user_id if needed
    # Note: In production, you may want to handle this differently
    op.execute("UPDATE audio_transcriptions SET user_id = 1 WHERE user_id IS NULL")
    op.execute("UPDATE audio_transcriptions SET file_hash = 'legacy' WHERE file_hash IS NULL")

    # Make columns non-nullable after updating existing data
    with op.batch_alter_table('audio_transcriptions', schema=None) as batch_op:
        batch_op.alter_column('user_id', nullable=False)
        batch_op.alter_column('file_hash', nullable=False)


def downgrade():
    """Remove transcription caching columns."""

    with op.batch_alter_table('audio_transcriptions', schema=None) as batch_op:
        # Drop indexes
        batch_op.drop_index('ix_audio_transcriptions_file_hash')
        batch_op.drop_index('ix_audio_transcriptions_user_id')

        # Drop foreign key constraint
        batch_op.drop_constraint('fk_audio_transcriptions_user_id', type_='foreignkey')

        # Drop columns
        batch_op.drop_column('file_hash')
        batch_op.drop_column('user_id')