"""
Question Agent - Handles customer questions about the restaurant, menu, and orders
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.agents.state import ConversationWorkflowState
from app.agents.agent_response.question_response import QuestionResponse
from app.agents.prompts.question_prompts import get_question_prompt
from app.constants.audio_phrases import AudioPhraseType
from app.core.config import settings
from app.services.menu_service import MenuService
from app.services.restaurant_service import RestaurantService

logger = logging.getLogger(__name__)


def create_question_tools(menu_service: MenuService, restaurant_service: RestaurantService, restaurant_id: int) -> List:
    """
    Create tools for the question agent to query restaurant information.
    
    Args:
        menu_service: Menu service instance
        restaurant_service: Restaurant service instance
        restaurant_id: Restaurant ID
        
    Returns:
        List of LangChain tools
    """
    
    @tool
    async def get_ingredients_for_item(item_name: str) -> str:
        """Get ingredients for a specific menu item. Use this when customers ask about what's in a dish or if they can modify ingredients."""
        try:
            ingredients = await menu_service.get_menu_item_ingredients(restaurant_id, item_name)
            if not ingredients:
                return f"No ingredients found for '{item_name}'"
            
            ingredient_list = []
            for ing in ingredients:
                optional_text = " (optional)" if ing.get("is_optional") else ""
                allergen_text = f" (allergen: {ing.get('allergen_type')})" if ing.get("is_allergen") else ""
                cost_text = f" (+${ing.get('additional_cost', 0):.2f})" if ing.get('additional_cost', 0) > 0 else ""
                ingredient_list.append(f"{ing['name']}{optional_text}{allergen_text}{cost_text}")
            
            return f"Ingredients for {item_name}: {', '.join(ingredient_list)}"
        except Exception as e:
            return f"Error getting ingredients for {item_name}: {str(e)}"
    
    @tool
    async def get_menu_categories() -> str:
        """Get all available menu categories (like Burgers, Sides, Drinks, etc.)"""
        try:
            categories = await menu_service.get_menu_categories(restaurant_id)
            return f"Menu categories: {', '.join(categories)}"
        except Exception as e:
            return f"Error getting menu categories: {str(e)}"
    
    @tool
    async def get_restaurant_hours() -> str:
        """Get restaurant operating hours"""
        try:
            hours = await restaurant_service.get_restaurant_hours(restaurant_id)
            return f"Restaurant hours: {hours}"
        except Exception as e:
            return f"Error getting restaurant hours: {str(e)}"
    
    @tool
    async def get_restaurant_address() -> str:
        """Get restaurant address and location"""
        try:
            address = await restaurant_service.get_restaurant_address(restaurant_id)
            return f"Restaurant address: {address}"
        except Exception as e:
            return f"Error getting restaurant address: {str(e)}"
    
    @tool
    async def get_restaurant_phone() -> str:
        """Get restaurant phone number"""
        try:
            phone = await restaurant_service.get_restaurant_phone(restaurant_id)
            return f"Restaurant phone: {phone}"
        except Exception as e:
            return f"Error getting restaurant phone: {str(e)}"
    
    @tool
    async def check_ingredient_availability(ingredient_name: str) -> str:
        """Check if an ingredient is available to add to menu items and what it costs."""
        try:
            all_ingredients = await menu_service.get_all_ingredients_with_costs(restaurant_id)
            for ing in all_ingredients:
                if ing['name'].lower() == ingredient_name.lower():
                    cost_text = f" for ${ing['unit_cost']:.2f}" if ing['unit_cost'] > 0 else " at no extra cost"
                    allergen_text = f" (allergen: {ing['allergen_type']})" if ing['is_allergen'] else ""
                    return f"Yes, {ingredient_name} is available{allergen_text}{cost_text}."
            
            return f"Sorry, {ingredient_name} is not available at this restaurant."
        except Exception as e:
            return f"Error checking ingredient availability: {str(e)}"
    
    # Return the decorated tools
    return [
        get_ingredients_for_item,
        get_menu_categories,
        get_restaurant_hours,
        get_restaurant_address,
        get_restaurant_phone,
        check_ingredient_availability
    ]


async def question_agent_node(state: ConversationWorkflowState, context: Dict[str, Any]) -> ConversationWorkflowState:
    """
    Question Agent - Answers customer questions about restaurant, menu, and orders.
    
    Args:
        state: Current conversation workflow state
        context: Context containing container and other services
        
    Returns:
        Updated conversation workflow state with response
    """
    try:
        container = context.get("container")
        if not container:
            logger.error("Container not found in context")
            state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
            state.response_phrase_type = AudioPhraseType.ERROR_MESSAGE
            state.audio_url = None
            return state

        # Get services from container
        voice_service = container.voice_service()
        menu_service: MenuService = container.menu_service()
        restaurant_service: RestaurantService = container.restaurant_service()

        # Create tools for the agent
        tools = create_question_tools(menu_service, restaurant_service, int(state.restaurant_id))
        
        # Create LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
        # Create agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful drive-thru assistant specializing in answering customer questions about the restaurant, menu, and their order.

You have access to tools to get specific information. Use these tools when customers ask about:
- Ingredients in menu items (use get_ingredients_for_item)
- Menu categories (use get_menu_categories) 
- Restaurant hours (use get_restaurant_hours)
- Restaurant location (use get_restaurant_address)
- Restaurant phone (use get_restaurant_phone)

Always answer questions helpfully and accurately. If you don't know something, use the appropriate tool to find out.

Keep responses to 1-2 sentences and maintain a friendly tone."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        agent = create_openai_functions_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Get AI response using tools
        result = await agent_executor.ainvoke({
            "input": state.user_input,
            "conversation_history": state.conversation_history
        })
        logger.info(f"LLM question result: {result}")

        # Extract response from agent result
        response_text = result.get("output", "I'm sorry, I couldn't process your request.")
        
        # Debug output
        print(f"\n🔍 DEBUG - QUESTION AI RESPONSE:")
        print(f"   Response Text: {response_text}")
        print(f"   Full Result: {result}")

        # Update state with response
        state.response_text = response_text
        state.response_phrase_type = AudioPhraseType.LLM_GENERATED  # Tool-based responses are always custom
        state.custom_response_text = response_text

        # Generate audio
        state.audio_url = await voice_service.generate_audio(
            phrase_type=AudioPhraseType.LLM_GENERATED,
            restaurant_id=state.restaurant_id,
            custom_text=response_text
        )

        logger.info(f"Generated question response: {response_text[:100]}...")

    except Exception as e:
        logger.error(f"Question agent generation failed: {str(e)}")
        state.response_text = "I'm sorry, I had trouble processing your request. Please try again."
        state.response_phrase_type = AudioPhraseType.ERROR_MESSAGE
        state.audio_url = None

    return state
