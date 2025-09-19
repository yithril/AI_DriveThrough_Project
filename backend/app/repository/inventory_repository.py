"""
Inventory repository for data access operations
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .base_repository import BaseRepository
from ..models.inventory import Inventory


class InventoryRepository(BaseRepository[Inventory]):
    """
    Repository for Inventory model with inventory-specific operations
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__(Inventory, db)
    
    async def get_by_ingredient(self, ingredient_id: int) -> Optional[Inventory]:
        """
        Get inventory for a specific ingredient
        
        Args:
            ingredient_id: Ingredient ID
            
        Returns:
            Inventory or None: Inventory instance if found
        """
        return await self.get_by_field("ingredient_id", ingredient_id)
    
    async def get_low_stock_items(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Get all inventory items that are low on stock
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of low stock inventory items
        """
        result = await self.db.execute(
            select(Inventory)
            .where(
                Inventory.is_active == True,
                Inventory.current_stock <= Inventory.min_stock_level
            )
            .order_by(Inventory.current_stock)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_out_of_stock_items(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Get all inventory items that are out of stock
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of out of stock inventory items
        """
        result = await self.db.execute(
            select(Inventory)
            .where(
                Inventory.is_active == True,
                Inventory.current_stock <= 0
            )
            .order_by(Inventory.last_updated)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_active_inventory(self, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Get all active inventory items
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of active inventory items
        """
        return await self.get_all_by_filter({"is_active": True}, skip, limit)
    
    async def get_inventory_with_ingredient(self, inventory_id: int) -> Optional[Inventory]:
        """
        Get inventory with ingredient details loaded
        
        Args:
            inventory_id: Inventory ID
            
        Returns:
            Inventory or None: Inventory with ingredient if found
        """
        return await self.get_by_id_with_relations(inventory_id, ["ingredient"])
    
    async def search_by_supplier(self, supplier: str, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Search inventory items by supplier
        
        Args:
            supplier: Supplier name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of inventory items from the supplier
        """
        result = await self.db.execute(
            select(Inventory)
            .where(Inventory.supplier.ilike(f"%{supplier}%"))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_cost_range(self, min_cost: float, max_cost: float, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Get inventory items within a cost per unit range
        
        Args:
            min_cost: Minimum cost per unit
            max_cost: Maximum cost per unit
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of inventory items within cost range
        """
        result = await self.db.execute(
            select(Inventory)
            .where(
                Inventory.cost_per_unit >= min_cost,
                Inventory.cost_per_unit <= max_cost,
                Inventory.cost_per_unit.isnot(None)
            )
            .order_by(Inventory.cost_per_unit)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_high_value_items(self, min_total_value: float, skip: int = 0, limit: int = 100) -> List[Inventory]:
        """
        Get inventory items with high total value
        
        Args:
            min_total_value: Minimum total inventory value
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Inventory]: List of high value inventory items
        """
        result = await self.db.execute(
            select(Inventory)
            .where(
                Inventory.cost_per_unit * Inventory.current_stock >= min_total_value,
                Inventory.cost_per_unit.isnot(None)
            )
            .order_by(Inventory.cost_per_unit * Inventory.current_stock.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def count_active_items(self) -> int:
        """
        Count active inventory items
        
        Returns:
            int: Number of active inventory items
        """
        return await self.count({"is_active": True})
    
    async def count_low_stock_items(self) -> int:
        """
        Count low stock inventory items
        
        Returns:
            int: Number of low stock inventory items
        """
        result = await self.db.execute(
            select(Inventory.id)
            .where(
                Inventory.is_active == True,
                Inventory.current_stock <= Inventory.min_stock_level
            )
        )
        return len(result.scalars().all())
    
    async def count_out_of_stock_items(self) -> int:
        """
        Count out of stock inventory items
        
        Returns:
            int: Number of out of stock inventory items
        """
        result = await self.db.execute(
            select(Inventory.id)
            .where(
                Inventory.is_active == True,
                Inventory.current_stock <= 0
            )
        )
        return len(result.scalars().all())
    
    async def get_total_inventory_value(self) -> float:
        """
        Calculate total inventory value
        
        Returns:
            float: Total value of all inventory
        """
        result = await self.db.execute(
            select(Inventory.cost_per_unit * Inventory.current_stock)
            .where(
                Inventory.is_active == True,
                Inventory.cost_per_unit.isnot(None)
            )
        )
        values = result.scalars().all()
        return sum(float(value) for value in values if value is not None)
