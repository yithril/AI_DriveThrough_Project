"""
ADD_ITEM Agent Node

LangGraph node that parses customer requests for adding items to their order.
Uses LLM with tools to extract menu items, quantities, sizes, and modifications.
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage

from app.agents.state import ConversationWorkflowState
from app.agents.agent_response.add_item_response import AddItemResponse, AddItemContext
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

logger = logging.getLogger(__name__)


def create_add_item_tools(container) -> List:
    """
    Create tools for ADD_ITEM agent
    
    Args:
        container: Dependency injection container
        
    Returns:
        List of tools for the agent
    """
    
    # Get services from container
    menu_service = container.menu_service()
    restaurant_service = container.restaurant_service()
    
    @tool
    async def search_menu_items(query: str) -> str:
        """Search for menu items by name or description. Use this when customers mention items that might not match exactly."""
        try:
            # Get all available items
            items = await menu_service.get_available_items_for_restaurant(1)  # TODO: Get from context
            matching_items = []
            
            query_lower = query.lower()
            for item in items:
                if query_lower in item.lower():
                    matching_items.append(item)
            
            if matching_items:
                return f"Found matching items: {', '.join(matching_items)}"
            else:
                return f"No items found matching '{query}'. Available items: {', '.join(items[:10])}"
        except Exception as e:
            return f"Error searching menu items: {str(e)}"
    
    @tool
    async def get_menu_item_details(item_name: str) -> str:
        """Get detailed information about a specific menu item including available sizes and modifiers."""
        try:
            # Get menu item details
            ingredients = await menu_service.get_menu_item_ingredients(1, item_name)  # TODO: Get restaurant_id from context
            
            if not ingredients:
                return f"Item '{item_name}' not found on menu"
            
            details = []
            for ingredient in ingredients:
                optional_text = " (optional)" if ingredient.get("is_optional") else ""
                allergen_text = f" (allergen: {ingredient.get('allergen_type')})" if ingredient.get("is_allergen") else ""
                cost_text = f" (+${ingredient.get('additional_cost', 0):.2f})" if ingredient.get('additional_cost', 0) > 0 else ""
                details.append(f"{ingredient['name']}{optional_text}{allergen_text}{cost_text}")
            
            return f"Details for {item_name}: {', '.join(details)}"
        except Exception as e:
            return f"Error getting menu item details: {str(e)}"
    
    @tool
    async def get_menu_categories() -> str:
        """Get all available menu categories."""
        try:
            categories = await menu_service.get_menu_categories(1)  # TODO: Get restaurant_id from context
            return f"Available categories: {', '.join(categories)}"
        except Exception as e:
            return f"Error getting menu categories: {str(e)}"
    
    @tool
    async def get_menu_items_by_category(category: str) -> str:
        """Get all menu items in a specific category."""
        try:
            items = await menu_service.get_menu_items_by_category(1, category)  # TODO: Get restaurant_id from context
            return f"Items in {category}: {', '.join(items)}"
        except Exception as e:
            return f"Error getting items for category {category}: {str(e)}"
    
    @tool
    async def check_ingredient_availability(ingredient_name: str) -> str:
        """Check if an ingredient is available to add to menu items and what it costs."""
        try:
            all_ingredients = await menu_service.get_all_ingredients_with_costs(1)  # TODO: Get restaurant_id from context
            for ing in all_ingredients:
                if ing['name'].lower() == ingredient_name.lower():
                    cost_text = f" for ${ing['unit_cost']:.2f}" if ing['unit_cost'] > 0 else " at no extra cost"
                    allergen_text = f" (allergen: {ing['allergen_type']})" if ing['is_allergen'] else ""
                    return f"Yes, {ingredient_name} is available{allergen_text}{cost_text}."
            
            return f"Sorry, {ingredient_name} is not available at this restaurant."
        except Exception as e:
            return f"Error checking ingredient availability: {str(e)}"
    
    @tool
    async def get_restaurant_info() -> str:
        """Get restaurant information including hours, address, and phone."""
        try:
            info = await restaurant_service.get_restaurant_info(1)  # TODO: Get restaurant_id from context
            return f"Restaurant: {info.get('name', 'Unknown')}, Hours: {info.get('hours', 'Unknown')}, Address: {info.get('address', 'Unknown')}"
        except Exception as e:
            return f"Error getting restaurant info: {str(e)}"
    
    # Return the decorated tools
    return [
        search_menu_items,
        get_menu_item_details,
        get_menu_categories,
        get_menu_items_by_category,
        check_ingredient_availability,
        get_restaurant_info
    ]


async def add_item_agent_node(state: ConversationWorkflowState, context: Dict[str, Any]) -> ConversationWorkflowState:
    """
    ADD_ITEM agent node that parses customer requests for adding items to their order.
    
    Args:
        state: Current conversation workflow state
        context: Context containing container and other services
        
    Returns:
        Updated state with parsed items and response
    """
    try:
        # Get container from context
        container = context.get("container")
        if not container:
            raise ValueError("Container not found in context")
        
        # Create tools
        tools = create_add_item_tools(container)
        
        # Set up LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
        # Get menu data for the prompt
        menu_service = container.menu_service()
        available_items = await menu_service.get_available_items_for_restaurant(int(state.restaurant_id))
        restaurant_name = await menu_service.get_restaurant_name(int(state.restaurant_id))
        
        # Create structured prompt
        from app.agents.prompts.add_item_prompts import get_add_item_prompt
        
        # Convert menu items to dict format if they're not already
        menu_items_dict = []
        for item in available_items:
            if hasattr(item, 'to_dict'):
                menu_items_dict.append(item.to_dict())
            elif isinstance(item, dict):
                menu_items_dict.append(item)
            else:
                # Fallback for other types
                menu_items_dict.append({
                    "id": getattr(item, 'id', 0),
                    "name": getattr(item, 'name', 'Unknown'),
                    "price": getattr(item, 'price', 0.0),
                    "description": getattr(item, 'description', '')
                })
        
        # Get restaurant info
        restaurant_info = await menu_service.get_restaurant_name(int(state.restaurant_id))
        
        # Format menu items by category
        menu_categories = await menu_service.get_menu_categories(int(state.restaurant_id))
        menu_items_by_category = await menu_service.get_menu_items_by_category(int(state.restaurant_id))
        
        prompt = get_add_item_prompt(
            user_input=state.normalized_user_input,
            conversation_history=state.conversation_history,
            order_state=state.order_state.__dict__,
            menu_items=menu_items_by_category,
            restaurant_info=restaurant_info
        )
        
        # Set up LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        ).with_structured_output(AddItemResponse, method="function_calling")
        
        # Execute with structured output
        response = await llm.ainvoke(prompt)
        logger.info(f"LLM ADD_ITEM result: {response}")
        
        # DEBUG: Log the result
        print(f"\n🔍 DEBUG - ADD_ITEM AI RESPONSE:")
        print(f"   Response Type: {response.response_type}")
        print(f"   Phrase Type: {response.phrase_type}")
        print(f"   Text: {response.response_text}")
        print(f"   Items to add: {len(response.items_to_add)}")
        for i, item in enumerate(response.items_to_add):
            print(f"     Item {i+1}: ID {item.menu_item_id} x{item.quantity} - {item.size or 'no size'}")
        
        # Update state with the structured response
        state.response_text = response.response_text
        state.response_phrase_type = response.phrase_type
        state.audio_url = None  # Will be generated by voice service
        
        # Store the parsed items for command creation
        state.commands = []
        for item in response.items_to_add:
            state.commands.append({
                "intent": "ADD_ITEM",
                "confidence": response.confidence,
                "slots": {
                    "menu_item_id": item.menu_item_id,
                    "quantity": item.quantity,
                    "size": item.size,
                    "modifiers": item.modifiers,
                    "special_instructions": item.special_instructions
                }
            })
        
        logger.info(f"ADD_ITEM agent processed: {state.normalized_user_input}")
        logger.info(f"Parsed items: {[f'ID {item.menu_item_id} x{item.quantity}' for item in response.items_to_add]}")
        logger.info(f"Commands created: {len(state.commands)}")
        
    except Exception as e:
        logger.error(f"ADD_ITEM agent failed: {e}")
        state.response_text = "I'm sorry, I had trouble understanding your request. Could you please try again?"
        state.response_phrase_type = AudioPhraseType.DIDNT_UNDERSTAND
        state.audio_url = None
    
    return state
