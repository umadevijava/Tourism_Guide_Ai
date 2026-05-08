"""Add chat history tables

Revision ID: add_chat_history_001
Revises: 040b0da03c42
Create Date: 2026-05-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'add_chat_history_001'
down_revision: Union[str, Sequence[str], None] = '040b0da03c42'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - create chat history tables."""
    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.PrimaryKeyConstraint('session_id')
    )
    
    # Create chat_messages table
    op.create_table(
        'chat_messages',
        sa.Column('id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('session_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('answer', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('rag_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reasoning_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('web_search_mode', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
    )
    
    # Create indexes for better query performance
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id'])
    op.create_index('ix_chat_messages_timestamp', 'chat_messages', ['timestamp'])
    op.create_index('ix_chat_sessions_updated_at', 'chat_sessions', ['updated_at'])


def downgrade() -> None:
    """Downgrade schema - drop chat history tables."""
    op.drop_index('ix_chat_sessions_updated_at', table_name='chat_sessions')
    op.drop_index('ix_chat_messages_timestamp', table_name='chat_messages')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
