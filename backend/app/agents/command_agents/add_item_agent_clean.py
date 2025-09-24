"""
ADD_ITEM agent that parses customer requests for adding items to their order.
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.core.config import settings
from app.agents.agent_response.add_item_response import AddItemResponse, ItemToAdd
from app.agents.prompts.add_item_prompts import get_add_item_prompt
from app.constants.audio_phrases import AudioPhraseType

logger = logging.getLogger(__name__)


async def add_item_agent(user_input: str, context: Dict[str, Any]) -> AddItemResponse:
    """
    ADD_ITEM agent node that parses customer requests for adding items to their order.
    
    Args:
        user_input: The user's input string
        context: Context dictionary containing services and session info
        
    Returns:
        AddItemResponse: Structured response with items to add
    """
    try:
        # Extract context
        container = context.get("container")
        service_factory = context.get("service_factory")
        shared_db_session = context.get("shared_db_session")
        conversation_history = context.get("conversation_history", [])
        order_state = context.get("order_state", {})
        restaurant_id = context.get("restaurant_id", "1")
        
        # Get services
        menu_service = service_factory.create_menu_service(shared_db_session)
        
        # Get menu data
        menu_items_by_category = await menu_service.get_menu_items_by_category(int(restaurant_id))
        restaurant_info = await menu_service.get_restaurant_name(int(restaurant_id))
        
        # Create tools for the agent
        def create_add_item_tools(context):
            """Create tools for the ADD_ITEM agent"""
            async def search_menu_items(query: str) -> str:
                """Search for menu items by name or description. Returns item names and IDs for agent to use."""
                try:
                    # Use the mocked menu service instead of UnitOfWork
                    available_items = await service_bundle["menu_service"].get_available_items_for_restaurant(1)
                    
                    matching_items = []
                    query_lower = query.lower()
                    
                    for item in available_items:
                        if query_lower in item["name"].lower():
                            matching_items.append(f"{item['name']} (ID: {item['id']})")
                    
                    if matching_items:
                        return f"Found matching items: {', '.join(matching_items)}"
                    else:
                        available_names = [item["name"] for item in available_items]
                        return f"No items found matching '{query}'. Available items: {', '.join(available_names)}"
                        
                except Exception as e:
                    return f"Error searching menu items: {e}"
            
            async def get_menu_items_by_category(category: str) -> str:
                """Get all items in a specific category"""
                try:
                    items = await service_bundle["menu_service"].get_menu_items_by_category(1)
                    if category.lower() in items:
                        return f"Items in {category}: {', '.join(items[category.lower()])}"
                    else:
                        return f"Category '{category}' not found. Available categories: {', '.join(items.keys())}"
                except Exception as e:
                    return f"Error getting category items: {e}"
            
            async def get_menu_item_details(item_name: str) -> str:
                """Get details about a specific menu item"""
                try:
                    items = await service_bundle["menu_service"].get_available_items_for_restaurant(1)
                    for item in items:
                        if item_name.lower() in item["name"].lower():
                            return f"Item: {item['name']}, Price: ${item['price']}, Description: {item['description']}"
                    return f"Item '{item_name}' not found"
                except Exception as e:
                    return f"Error getting item details: {e}"
            
            async def get_menu_categories() -> str:
                """Get all available menu categories"""
                try:
                    categories = await service_bundle["menu_service"].get_menu_categories(1)
                    return f"Available categories: {', '.join(categories)}"
                except Exception as e:
                    return f"Error getting categories: {e}"
            
            return [
                search_menu_items,
                get_menu_items_by_category,
                get_menu_item_details,
                get_menu_categories
            ]
        
        # Create service bundle for tools
        service_bundle = {
            "menu_service": menu_service,
            "restaurant_service": service_factory.create_restaurant_service(shared_db_session)
        }
        
        # Create tools
        tools = create_add_item_tools(context)
        
        # Create prompt
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
        
        # Create agent prompt
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

        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", agent_system_prompt),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent with structured output
        agent = create_openai_functions_agent(llm, tools, agent_prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Bind structured output to the agent executor
        agent_executor = agent_executor.with_structured_output(AddItemResponse)
        
        # Execute with tools and get structured output
        add_item_response = await agent_executor.ainvoke({
            "input": user_input,
            "conversation_history": conversation_history
        })
        
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
        from app.constants.audio_phrases import AudioPhraseType
        from app.agents.agent_response.add_item_response import AddItemResponse, ItemToAdd
        
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
