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
from app.core.unit_of_work import UnitOfWork

from app.agents.state import ConversationWorkflowState
from app.agents.agent_response.add_item_response import AddItemResponse, AddItemContext, ItemToAdd
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings

from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)


def create_add_item_tools(service_bundle, context) -> List:
    """
    Create tools for ADD_ITEM agent
    
    Args:
        service_bundle: Service bundle containing required services
        context: Context containing shared_db_session
        
    Returns:
        List of tools for the agent
    """
    
    # Get services from bundle
    menu_service = service_bundle.get("menu_service")
    restaurant_service = service_bundle.get("restaurant_service")
    
    # Get shared database session from context
    shared_db_session = context.get("shared_db_session")
    
    @tool
    async def search_menu_items(query: str) -> str:
        """Search for menu items by name or description. Returns item names and IDs for agent to use."""
        try:
            print(f"🔍 TOOL CALLED: search_menu_items with query='{query}'")
            # Use the mocked menu service instead of UnitOfWork
            available_items = await service_bundle["menu_service"].get_available_items_for_restaurant(1)
            print(f"🔍 TOOL: Got {len(available_items)} available items")
            
            matching_items = []
            query_lower = query.lower()
            
            for item in available_items:
                if query_lower in item["name"].lower():
                    matching_items.append(f"{item['name']} (ID: {item['id']})")
            
            if matching_items:
                result = f"Found matching items: {', '.join(matching_items)}"
                print(f"🔍 TOOL RESULT: {result}")
                return result
            else:
                # Show available items for reference
                available_names = [f"{item['name']} (ID: {item['id']})" for item in available_items[:10]]
                result = f"No items found matching '{query}'. Available items: {', '.join(available_names)}"
                print(f"🔍 TOOL RESULT: {result}")
                return result
        except Exception as e:
            error_msg = f"Error searching menu items: {str(e)}"
            print(f"🔍 TOOL ERROR: {error_msg}")
            return error_msg
    
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
            # Get all items by category, then filter for the specific category
            all_items_by_category = await menu_service.get_menu_items_by_category(1)  # TODO: Get restaurant_id from context
            items = all_items_by_category.get(category, [])
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


async def add_item_agent(user_input: str, context: Dict[str, Any]) -> AddItemResponse:
    """
    ADD_ITEM agent node that parses customer requests for adding items to their order.
    
    Args:
        user_input: The user's input string
        context: Context containing container and other services
        
    Returns:
        AddItemResponse with parsed items and response
    """
    try:
        # Get service factory from context
        service_factory = context.get("service_factory")
        if not service_factory:
            raise ValueError("Service factory not found in context")
        
        # Get shared database session from context
        shared_db_session = context.get("shared_db_session")
        if not shared_db_session:
            raise ValueError("Shared database session not found in context")
        
        # Create services with shared database session
        menu_service = service_factory.create_menu_service(shared_db_session)
        restaurant_service = service_factory.create_restaurant_service(shared_db_session)
        
        # Create service bundle for tools
        service_bundle = {
            "menu_service": menu_service,
            "restaurant_service": restaurant_service
        }
        
        # Create tools
        tools = create_add_item_tools(service_bundle, context)
        
        # Set up LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
        # Get conversation history and order state from context
        conversation_history = context.get("conversation_history", [])
        order_state = context.get("order_state", {})
        
        # Get menu data for the prompt (using services from service bundle)
        restaurant_id = context.get("restaurant_id", "1")
        available_items = await menu_service.get_available_items_for_restaurant(int(restaurant_id))
        restaurant_name = await menu_service.get_restaurant_name(int(restaurant_id))
        
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
        restaurant_info = await menu_service.get_restaurant_name(int(restaurant_id))
        
        # Format menu items by category
        menu_categories = await menu_service.get_menu_categories(int(restaurant_id))
        menu_items_by_category = await menu_service.get_menu_items_by_category(int(restaurant_id))
        
        prompt = get_add_item_prompt(
            user_input=user_input,
            conversation_history=conversation_history,
            order_state=order_state,
            menu_items=menu_items_by_category,
            restaurant_info=restaurant_info
        )
        
        # Set up LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )

        
        # Create a clean agent prompt that relies on tools
        agent_system_prompt = """You are an AI assistant for a drive-thru restaurant. Your job is to parse customer requests for adding items to their order.                                                                                   

    INSTRUCTIONS:
    1. Parse the customer's request to identify ALL items they want to add
    2. Use the available tools to search for each item
    3. For each item, create an ItemToAdd object:
       - If found: set menu_item_id to the actual ID
       - If not found: set menu_item_id=0 and ambiguous_item to the requested name
    4. You must handle ALL items mentioned, not just the ones you can find

    You have access to these tools:
    - search_menu_items(query): Search for menu items by name
    - get_menu_items_by_category(category): Get all items in a category
    - get_menu_item_details(item_name): Get details about a specific item
    - get_menu_categories(): Get all menu categories

    BE SMART AND DECISIVE:
    - Don't be overly cautious - if there's a clear single match, add it
    - Use tools to check what's available, then make confident decisions
    - Only ask for clarification when there are genuinely multiple options
    - Always create ItemToAdd objects for ALL items the customer requested

    Always be helpful and use the tools when you need specific information."""

        # Create agent prompt
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", agent_system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create tools
        tools = create_add_item_tools(service_bundle, context)
        
        # Create agent with tools
        agent = create_openai_tools_agent(llm, tools, agent_prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Execute the agent
        result = await agent_executor.ainvoke({
            "input": user_input,
            "conversation_history": conversation_history
        })
        
        # Extract the response from the agent result
        response_text = result.get("output", "")
        
        # Parse the agent's response to extract items dynamically
        items_to_add = []
        
        # Use regex to find menu_item_id patterns in the response
        import re
        
        # Find all (ID: X) patterns
        menu_item_pattern = r'\(ID:\s*(\d+)\)'
        menu_item_matches = re.findall(menu_item_pattern, response_text)
        
        # Find all ambiguous_item = "X" patterns  
        ambiguous_pattern = r'ambiguous_item\s*=\s*"([^"]+)"'
        ambiguous_matches = re.findall(ambiguous_pattern, response_text)
        
        # Create items based on found patterns
        for menu_item_id in menu_item_matches:
            if menu_item_id != "0":  # Skip ambiguous items (ID 0)
                items_to_add.append(ItemToAdd(
                    menu_item_id=int(menu_item_id),
                    quantity=1,
                    size=None,
                    modifiers=[],
                    special_instructions=None,
                    ambiguous_item=None
                ))
        
        # Add ambiguous items
        for ambiguous_item in ambiguous_matches:
            items_to_add.append(ItemToAdd(
                menu_item_id=0,
                quantity=1,
                size=None,
                modifiers=[],
                special_instructions=None,
                ambiguous_item=ambiguous_item
            ))
        
        # If no items were parsed, create a fallback
        if not items_to_add:
            items_to_add.append(ItemToAdd(
                menu_item_id=0,
                quantity=1,
                size=None,
                modifiers=[],
                special_instructions=None,
                ambiguous_item=user_input
            ))
        
        add_item_response = AddItemResponse(
            response_type="success",
            phrase_type=AudioPhraseType.ITEM_ADDED_SUCCESS,
            response_text=response_text,
            confidence=0.9,
            items_to_add=items_to_add
        )
        
        # DEBUG: Log the result
        print(f"\n🔍 DEBUG - ADD_ITEM AI RESPONSE:")
        print(f"   Response Type: {type(add_item_response)}")
        print(f"   Items to Add: {len(add_item_response.items_to_add)}")
        for i, item in enumerate(add_item_response.items_to_add):
            print(f"     Item {i+1}: ID={item.menu_item_id}, Ambiguous={item.ambiguous_item}")
        
        return add_item_response
        
    except Exception as e:
        logger.error(f"ADD_ITEM agent failed: {e}")
        print(f"🔍 DEBUG - Agent exception: {e}")
        
        return AddItemResponse(
            response_type="error",
            phrase_type=AudioPhraseType.DIDNT_UNDERSTAND,
            response_text="I'm sorry, I had trouble understanding your request. Could you please try again?",
            confidence=0.0,
            items_to_add=[ItemToAdd(
                menu_item_id=0,
                quantity=1,
                size=None,
                modifiers=[],
                special_instructions=None
            )]
        )
        
        
    except Exception as e:
        logger.error(f"ADD_ITEM agent failed: {e}")
        print(f"🔍 DEBUG - Agent exception: {e}")
        
        return AddItemResponse(
            response_type="error",
            phrase_type=AudioPhraseType.DIDNT_UNDERSTAND,
            response_text="I'm sorry, I had trouble understanding your request. Could you please try again?",
            confidence=0.0,
            items_to_add=[ItemToAdd(
                menu_item_id=0,
                quantity=1,
                size=None,
                modifiers=[],
                special_instructions=None
            )]
        )
