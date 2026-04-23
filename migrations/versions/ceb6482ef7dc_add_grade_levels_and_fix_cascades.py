"""add_grade_levels_and_fix_cascades

Revision ID: ceb6482ef7dc
Revises: b3fcf0c40f8c
Create Date: 2026-04-22 19:32:15.182896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ceb6482ef7dc'
down_revision = 'b3fcf0c40f8c'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create grade_levels table (if not exists - idempotent)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'grade_levels' not in existing_tables:
        op.create_table('grade_levels',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('campus_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('order_num', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['campus_id'], ['campuses.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('campus_id', 'name', name='uq_gradelevel_campus_name')
        )
        op.create_index(op.f('ix_grade_levels_campus_id'), 'grade_levels', ['campus_id'], unique=False)

    # 2. Add level_id column to grades table (if not exists)
    existing_columns = [c['name'] for c in inspector.get_columns('grades')]
    if 'level_id' not in existing_columns:
        with op.batch_alter_table('grades', schema=None) as batch_op:
            batch_op.add_column(sa.Column('level_id', sa.Integer(), nullable=True))
            batch_op.create_index(batch_op.f('ix_grades_level_id'), ['level_id'], unique=False)
            batch_op.create_foreign_key('fk_grades_level_id', 'grade_levels', ['level_id'], ['id'], ondelete='SET NULL')


def downgrade():
    with op.batch_alter_table('grades', schema=None) as batch_op:
        batch_op.drop_constraint('fk_grades_level_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_grades_level_id'))
        batch_op.drop_column('level_id')

    op.drop_index(op.f('ix_grade_levels_campus_id'), table_name='grade_levels')
    op.drop_table('grade_levels')
