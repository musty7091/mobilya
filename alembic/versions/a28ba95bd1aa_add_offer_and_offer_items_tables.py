"""Add offer and offer_items tables

Revision ID: a28ba95bd1aa
Revises: d6b4ffe3ba38
Create Date: 2026-03-08 22:36:34.906217

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a28ba95bd1aa'
down_revision: Union[str, Sequence[str], None] = 'd6b4ffe3ba38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SADECE TEKLİF VE TEKLİF KALEMLERİ EKLENİYOR
    op.add_column('offer_items', sa.Column('item_name', sa.String(), nullable=False))
    op.add_column('offer_items', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('offer_items', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column('offer_items', 'quantity',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('offer_items', 'unit_price',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True)
    op.drop_constraint(op.f('offer_items_offer_id_fkey'), 'offer_items', type_='foreignkey')
    op.create_foreign_key(None, 'offer_items', 'offers', ['offer_id'], ['id'], ondelete='CASCADE')
    op.drop_column('offer_items', 'name')
    op.drop_column('offer_items', 'total_price')
    op.drop_column('offer_items', 'product_id')
    op.add_column('offers', sa.Column('total_price', sa.Float(), nullable=True))
    op.add_column('offers', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column('offers', 'company_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('offers', 'customer_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_index(op.f('ix_offers_company_id'), table_name='offers')
    op.drop_index(op.f('ix_offers_customer_id'), table_name='offers')
    op.drop_constraint(op.f('offers_customer_id_fkey'), 'offers', type_='foreignkey')
    op.drop_constraint(op.f('offers_company_id_fkey'), 'offers', type_='foreignkey')
    op.create_foreign_key(None, 'offers', 'companies', ['company_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'offers', 'customers', ['customer_id'], ['id'], ondelete='CASCADE')
    op.drop_column('offers', 'title')
    op.drop_column('offers', 'total_amount')


def downgrade() -> None:
    """Downgrade schema."""
    # SADECE TEKLİF VE TEKLİF KALEMLERİ GERİ ALINIYOR
    op.add_column('offers', sa.Column('total_amount', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True))
    op.add_column('offers', sa.Column('title', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.drop_constraint(None, 'offers', type_='foreignkey')
    op.create_foreign_key(op.f('offers_company_id_fkey'), 'offers', 'companies', ['company_id'], ['id'])
    op.create_foreign_key(op.f('offers_customer_id_fkey'), 'offers', 'customers', ['customer_id'], ['id'])
    op.create_index(op.f('ix_offers_customer_id'), 'offers', ['customer_id'], unique=False)
    op.create_index(op.f('ix_offers_company_id'), 'offers', ['company_id'], unique=False)
    op.alter_column('offers', 'customer_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('offers', 'company_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('offers', 'updated_at')
    op.drop_column('offers', 'total_price')
    op.add_column('offer_items', sa.Column('product_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('offer_items', sa.Column('total_price', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('offer_items', sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'offer_items', type_='foreignkey')
    op.create_foreign_key(op.f('offer_items_offer_id_fkey'), 'offer_items', 'offers', ['offer_id'], ['id'])
    op.alter_column('offer_items', 'unit_price',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('offer_items', 'quantity',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('offer_items', 'updated_at')
    op.drop_column('offer_items', 'created_at')
    op.drop_column('offer_items', 'item_name')