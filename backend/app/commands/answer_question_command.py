"""
Answer question command for AI customer service
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from .base_command import BaseCommand
from ..dto.order_result import OrderResult
from ..services.order_service import OrderService
from ..repository.menu_item_repository import MenuItemRepository
from ..repository.restaurant_repository import RestaurantRepository


class AnswerQuestionCommand(BaseCommand):
    """
    Command to answer customer questions
    Used by AI when customer asks questions about menu, prices, availability, etc.
    """
    
    def __init__(
        self, 
        restaurant_id: int,
        question: str,
        order_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize answer question command
        
        Args:
            restaurant_id: Restaurant ID
            question: Customer's question
            order_id: Optional order ID for order-related questions
            context: Additional context for the question
        """
        super().__init__(restaurant_id, order_id)
        self.question = question
        self.context = context or {}
    
    async def execute(self, db: AsyncSession) -> OrderResult:
        """
        Execute the answer question command
        
        Args:
            db: Database session
            
        Returns:
            OrderResult: Result with answer to the question
        """
        try:
            # Analyze question type and provide appropriate response
            question_lower = self.question.lower()
            
            # Menu-related questions
            if any(keyword in question_lower for keyword in ["menu", "what", "available", "have", "sell"]):
                return await self._answer_menu_question(db)
            
            # Price-related questions
            elif any(keyword in question_lower for keyword in ["price", "cost", "how much", "expensive"]):
                return await self._answer_price_question(db)
            
            # Order-related questions
            elif any(keyword in question_lower for keyword in ["order", "current", "total", "what's in"]):
                return await self._answer_order_question(db)
            
            # Ingredient/allergen questions
            elif any(keyword in question_lower for keyword in ["ingredient", "allergen", "contains", "gluten", "dairy", "nuts"]):
                return await self._answer_ingredient_question(db)
            
            # General restaurant questions
            elif any(keyword in question_lower for keyword in ["hours", "open", "location", "phone", "contact"]):
                return await self._answer_restaurant_question(db)
            
            # Default response for unclear questions
            else:
                return OrderResult.success(
                    "I'd be happy to help! You can ask me about our menu items, prices, ingredients, or your current order. What would you like to know?",
                    data={"question_type": "general", "suggestions": [
                        "What menu items do you have?",
                        "How much does [item] cost?",
                        "What's in my current order?",
                        "Does [item] contain [ingredient]?"
                    ]}
                )
                
        except Exception as e:
            return OrderResult.error(f"Failed to answer question: {str(e)}")
    
    async def _answer_menu_question(self, db: AsyncSession) -> OrderResult:
        """Answer questions about the menu"""
        try:
            menu_item_repo = MenuItemRepository(db)
            available_items = await menu_item_repo.get_available_by_restaurant(self.restaurant_id)
            
            # Group by category for better presentation
            categories = {}
            for item in available_items:
                category_name = item.category.name if item.category else "Other"
                if category_name not in categories:
                    categories[category_name] = []
                categories[category_name].append({
                    "name": item.name,
                    "price": float(item.price),
                    "description": item.description
                })
            
            return OrderResult.success(
                "Here's our current menu:",
                data={
                    "question_type": "menu",
                    "categories": categories,
                    "total_items": len(available_items)
                }
            )
        except Exception as e:
            return OrderResult.error(f"Could not retrieve menu: {str(e)}")
    
    async def _answer_price_question(self, db: AsyncSession) -> OrderResult:
        """Answer questions about prices"""
        try:
            # Extract item name from question (simple keyword matching)
            question_words = self.question.lower().split()
            menu_item_repo = MenuItemRepository(db)
            
            # Look for common price question patterns
            item_name = None
            for i, word in enumerate(question_words):
                if word in ["much", "cost", "price"] and i > 0:
                    # Try to find item name before the price keyword
                    potential_name = " ".join(question_words[max(0, i-2):i])
                    item_name = potential_name.strip()
                    break
            
            if item_name:
                # Search for the specific item
                items = await menu_item_repo.search_menu_items(self.restaurant_id, item_name)
                if items:
                    item = items[0]  # Take first match
                    return OrderResult.success(
                        f"{item.name} costs ${float(item.price):.2f}",
                        data={
                            "question_type": "price",
                            "item": item.to_dict(),
                            "formatted_price": f"${float(item.price):.2f}"
                        }
                    )
            
            # If no specific item found, provide general price range
            available_items = await menu_item_repo.get_available_by_restaurant(self.restaurant_id)
            if available_items:
                prices = [float(item.price) for item in available_items]
                min_price = min(prices)
                max_price = max(prices)
                
                return OrderResult.success(
                    f"Our items range from ${min_price:.2f} to ${max_price:.2f}. Would you like to know the price of a specific item?",
                    data={
                        "question_type": "price_range",
                        "min_price": min_price,
                        "max_price": max_price,
                        "formatted_range": f"${min_price:.2f} - ${max_price:.2f}"
                    }
                )
            
            return OrderResult.error("Could not find pricing information")
            
        except Exception as e:
            return OrderResult.error(f"Could not retrieve price information: {str(e)}")
    
    async def _answer_order_question(self, db: AsyncSession) -> OrderResult:
        """Answer questions about the current order"""
        try:
            if not self.order_id:
                return OrderResult.success(
                    "I don't see an active order. Would you like to start ordering?",
                    data={"question_type": "order", "has_order": False}
                )
            
            order_service = OrderService(db)
            result = await order_service.get_order(self.order_id)
            
            if result.is_success:
                order_data = result.data["order"]
                items = order_data.get("order_items", [])
                
                if not items:
                    return OrderResult.success(
                        "Your order is currently empty. What would you like to add?",
                        data={"question_type": "order", "has_items": False}
                    )
                
                # Format order summary
                item_summary = []
                total_items = 0
                for item in items:
                    menu_item = item.get("menu_item", {})
                    item_summary.append(f"{item['quantity']}x {menu_item.get('name', 'Item')}")
                    total_items += item["quantity"]
                
                return OrderResult.success(
                    f"Your current order has {total_items} items: {', '.join(item_summary)}. Total: ${order_data['total_amount']:.2f}",
                    data={
                        "question_type": "order",
                        "has_items": True,
                        "order": order_data,
                        "item_count": total_items,
                        "total": float(order_data["total_amount"])
                    }
                )
            
            return result
            
        except Exception as e:
            return OrderResult.error(f"Could not retrieve order information: {str(e)}")
    
    async def _answer_ingredient_question(self, db: AsyncSession) -> OrderResult:
        """Answer questions about ingredients and allergens"""
        try:
            # This would typically use the ingredient repository
            # For now, provide a general response
            return OrderResult.success(
                "I can help you with ingredient and allergen information. Please ask about a specific menu item, and I'll let you know what's in it.",
                data={
                    "question_type": "ingredient",
                    "suggestion": "Try asking: 'What's in the Big Mac?' or 'Does the burger contain dairy?'"
                }
            )
        except Exception as e:
            return OrderResult.error(f"Could not retrieve ingredient information: {str(e)}")
    
    async def _answer_restaurant_question(self, db: AsyncSession) -> OrderResult:
        """Answer general restaurant questions"""
        try:
            restaurant_repo = RestaurantRepository(db)
            restaurant = await restaurant_repo.get_by_id(self.restaurant_id)
            
            if restaurant:
                return OrderResult.success(
                    f"Welcome to {restaurant.name}! I can help you with ordering. What would you like to know about our menu?",
                    data={
                        "question_type": "restaurant",
                        "restaurant": restaurant.to_dict()
                    }
                )
            
            return OrderResult.error("Restaurant information not available")
            
        except Exception as e:
            return OrderResult.error(f"Could not retrieve restaurant information: {str(e)}")
    
    def _get_parameters(self) -> dict:
        """Get command parameters"""
        return {
            "question": self.question,
            "context": self.context
        }
