"""
Menu Resolution Agent

Second agent in the pipeline that resolves extracted items against the menu database.
Uses tools for database access and LLM for intelligent matching and suggestions.
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from app.core.config import settings
from app.agents.agent_response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.agents.agent_response.item_extraction_response import ItemExtractionResponse
from app.agents.prompts.menu_resolution_prompts import build_menu_resolution_prompt

logger = logging.getLogger(__name__)


def create_menu_resolution_tools(service_bundle, context) -> List:
    """
    Create tools for Menu Resolution Agent
    
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
        """Search for menu items by name or description. Returns item names for agent to use."""
        try:
            restaurant_id = context.get("restaurant_id", "1")
            print(f"\n🔍 DEBUG - MENU SEARCH TOOL:")
            print(f"   Query: '{query}'")
            print(f"   Restaurant ID: {restaurant_id}")
            
            matching_items = await menu_service.search_menu_items(int(restaurant_id), query)
            print(f"   Matching items found: {len(matching_items)}")
            print(f"   Matching items: {matching_items}")
            
            if not matching_items:
                # Get all available items for context
                all_items = await menu_service.get_available_items_for_restaurant(int(restaurant_id))
                print(f"   All available items: {all_items[:10]}")
                return f"No menu items found matching '{query}'. Available items: {', '.join(all_items[:10])}"
            
            result = f"Found {len(matching_items)} menu items matching '{query}':\n"
            for item in matching_items:
                result += f"- {item}\n"
            
            return result
        except Exception as e:
            print(f"   Error in search_menu_items: {str(e)}")
            return f"Error searching menu items: {str(e)}"
    
    @tool
    async def get_menu_item_details(item_name: str) -> str:
        """Get detailed information about a specific menu item by name."""
        try:
            restaurant_id = context.get("restaurant_id", "1")
            ingredients = await menu_service.get_menu_item_ingredients(int(restaurant_id), item_name)
            
            result = f"Menu item details for '{item_name}':\n"
            if ingredients:
                result += f"- Ingredients: {', '.join([ing['name'] for ing in ingredients])}\n"
            else:
                result += "- No ingredient information available\n"
            
            return result
        except Exception as e:
            return f"Error getting menu item details: {str(e)}"
    
    return [search_menu_items, get_menu_item_details]


async def menu_resolution_agent(extraction_response: ItemExtractionResponse, context: Dict[str, Any]) -> MenuResolutionResponse:
    """
    Resolve extracted items against the menu database.
    
    This is the second agent in the pipeline - it uses tools for database access
    and LLM for intelligent matching and suggestion generation.
    
    Args:
        extraction_response: Response from the item extraction agent
        context: Context containing services and database session
        
    Returns:
        MenuResolutionResponse with resolved items and menu IDs
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
        tools = create_menu_resolution_tools(service_bundle, context)
        
        # Set up LLM
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
        # Get restaurant_id from context
        restaurant_id = context.get("restaurant_id", "1")
        
        # Build the prompt with extraction results
        prompt = build_menu_resolution_prompt(extraction_response, restaurant_id)
        
        # Create agent with tools
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a menu resolution assistant. Use the available tools to resolve menu items and provide structured output."),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        agent = create_openai_tools_agent(llm, tools, agent_prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        
        # Execute the resolution
        result = await agent_executor.ainvoke({"input": prompt})
        
        # Parse the agent response manually
        resolution_response = _parse_agent_response(result["output"], extraction_response)
        
        # DEBUG: Log the result
        print(f"\n🔍 DEBUG - MENU RESOLUTION AGENT:")
        print(f"   Success: {resolution_response.success}")
        print(f"   Confidence: {resolution_response.confidence}")
        print(f"   Items resolved: {len(resolution_response.resolved_items)}")
        for i, item in enumerate(resolution_response.resolved_items):
            print(f"     Item {i+1}: '{item.item_name}' → ID: {item.menu_item_id} (ambiguous: {item.is_ambiguous})")
        
        return resolution_response
        
    except Exception as e:
        logger.error(f"Menu resolution agent failed: {e}")
        print(f"🔍 DEBUG - Resolution agent exception: {e}")
        
        # Return error response
        return MenuResolutionResponse(
            success=False,
            confidence=0.0,
            resolved_items=[
                ResolvedItem(
                    item_name="unknown",
                    quantity=1,
                    menu_item_id=0,
                    is_ambiguous=True,
                    confidence=0.0
                )
            ],
            needs_clarification=True,
            clarification_questions=["I'm sorry, I had trouble processing your request. Could you please try again?"]
        )


def _parse_agent_response(agent_output: str, extraction_response: ItemExtractionResponse) -> MenuResolutionResponse:
    """
    Parse the agent's structured JSON output into a MenuResolutionResponse.
    
    Args:
        agent_output: Raw text output from the agent
        extraction_response: Original extraction response for context
        
    Returns:
        MenuResolutionResponse with parsed data
    """
    try:
        import json
        import re
        
        # Extract JSON from the agent output (look for ```json blocks)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', agent_output, re.DOTALL)
        if not json_match:
            # Try to find JSON without code blocks
            json_match = re.search(r'(\{.*"resolved_items".*?\})', agent_output, re.DOTALL)
        
        if json_match:
            try:
                agent_json = json.loads(json_match.group(1))
                
                # Parse the structured response from the agent
                resolved_items = []
                for agent_item in agent_json.get("resolved_items", []):
                    resolved_item = ResolvedItem(
                        item_name=agent_item.get("item_name", ""),
                        quantity=agent_item.get("quantity", 1),
                        size=agent_item.get("size"),
                        modifiers=agent_item.get("modifiers", []),
                        special_instructions=agent_item.get("special_instructions"),
                        menu_item_id=agent_item.get("menu_item_id", 0),
                        resolved_name=agent_item.get("resolved_name"),
                        is_ambiguous=agent_item.get("is_ambiguous", False),
                        is_unavailable=agent_item.get("is_unavailable", False),
                        confidence=agent_item.get("confidence", 0.5),
                        suggested_options=agent_item.get("suggested_options", []),
                        clarification_question=agent_item.get("clarification_question")
                    )
                    resolved_items.append(resolved_item)
                
                return MenuResolutionResponse(
                    success=agent_json.get("success", True),
                    confidence=agent_json.get("confidence", 0.5),
                    resolved_items=resolved_items,
                    needs_clarification=agent_json.get("needs_clarification", False),
                    clarification_questions=agent_json.get("clarification_questions", [])
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from agent: {e}")
                # Fall back to default parsing
                pass
        
        # Fallback: Create response based on extraction if JSON parsing fails
        resolved_items = []
        for extracted_item in extraction_response.extracted_items:
            # Default to ambiguous if we can't parse the agent's response
            resolved_item = ResolvedItem(
                item_name=extracted_item.item_name,
                quantity=extracted_item.quantity,
                size=extracted_item.size,
                modifiers=extracted_item.modifiers,
                special_instructions=extracted_item.special_instructions,
                menu_item_id=0,
                is_ambiguous=True,
                is_unavailable=False,
                confidence=extracted_item.confidence,
                suggested_options=["Please check the menu for available items"],
                clarification_question=f"Could you clarify what you mean by '{extracted_item.item_name}'?"
            )
            resolved_items.append(resolved_item)
        
        return MenuResolutionResponse(
            success=True,
            confidence=0.5,
            resolved_items=resolved_items,
            needs_clarification=True,
            clarification_questions=["Please specify the exact items you'd like from our menu"]
        )
        
    except Exception as e:
        logger.error(f"Failed to parse agent response: {e}")
        return MenuResolutionResponse(
            success=False,
            confidence=0.0,
            resolved_items=[],
            needs_clarification=True,
            clarification_questions=["I'm sorry, I had trouble processing your request. Could you please try again?"]
        )


