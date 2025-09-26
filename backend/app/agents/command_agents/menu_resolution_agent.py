"""
Menu Resolution Agent

Second agent in the pipeline that resolves extracted items against the menu database.
Uses direct service calls + LLM for intelligent matching and disambiguation.
"""

import logging
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.agents.agent_response.menu_resolution_response import MenuResolutionResponse, ResolvedItem
from app.agents.agent_response.item_extraction_response import ItemExtractionResponse

logger = logging.getLogger(__name__)


async def menu_resolution_agent(extraction_response: ItemExtractionResponse, context: Dict[str, Any]) -> MenuResolutionResponse:
    """
    Menu Resolution Agent - Second agent in the pipeline.
    
    Resolves extracted items against the menu database using direct service calls + LLM reasoning.
    Uses database for fast pre-filtering, LLM only for disambiguation.
    
    Args:
        extraction_response: Response from Item Extraction Agent
        context: Context containing services and database session
        
    Returns:
        MenuResolutionResponse with resolved items
    """
    try:
        print(f"\n🔍 DEBUG - MENU RESOLUTION AGENT:")
        print(f"   Success: {extraction_response.success}")
        print(f"   Confidence: {extraction_response.confidence}")
        print(f"   Items extracted: {len(extraction_response.extracted_items)}")
        
        if not extraction_response.success or not extraction_response.extracted_items:
            return MenuResolutionResponse(
                success=False,
                confidence=0.0,
                resolved_items=[],
                needs_clarification=True,
                clarification_questions=["No items were extracted from your request."]
            )
        
        # Get services from context
        menu_service = context.get("menu_service")
        shared_db_session = context.get("shared_db_session")
        restaurant_id = int(context.get("restaurant_id", "1"))
        
        print(f"   🔍 DEBUG - MenuResolutionAgent context:")
        print(f"   Menu service: {menu_service}")
        print(f"   DB session: {shared_db_session}")
        print(f"   Restaurant ID: {restaurant_id}")
        
        if not menu_service or not shared_db_session:
            print(f"   ❌ Missing menu_service or shared_db_session")
            return MenuResolutionResponse(
                success=False,
                confidence=0.0,
                resolved_items=[],
                needs_clarification=True,
                clarification_questions=["There was an error accessing the menu. Please try again later."]
            )
        
        # Set up LLM for disambiguation only
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
        resolved_items = []
        needs_clarification = False
        clarification_questions = []
        
        # Process each extracted item
        for extracted_item in extraction_response.extracted_items:
            print(f"🔍 Processing: {extracted_item.item_name}")
            
            # Direct database search (fast pre-filtering)
            matches = await menu_service.search_menu_items(restaurant_id, extracted_item.item_name)
            print(f"   Database found: {[item.name for item in matches]}")
            
            if len(matches) == 0:
                # No matches - item unavailable
                print(f"   ❌ No matches - item unavailable")
                resolved_items.append(ResolvedItem(
                    item_name=extracted_item.item_name,
                    quantity=extracted_item.quantity,
                    size=extracted_item.size,
                    modifiers=extracted_item.modifiers,
                    special_instructions=extracted_item.special_instructions,
                    menu_item_id=0,
                    resolved_name=None,
                    confidence=0.0,
                    is_ambiguous=False,
                    suggested_options=[],
                    clarification_question=f"Sorry, we don't have {extracted_item.item_name} on our menu"
                ))
                
            elif len(matches) == 1:
                # Single match - success!
                menu_item = matches[0]  # We now have the full object
                print(f"   ✅ Single match - success: {menu_item.name} (ID: {menu_item.id})")
                resolved_items.append(ResolvedItem(
                    item_name=extracted_item.item_name,
                    quantity=extracted_item.quantity,
                    size=extracted_item.size,
                    modifiers=extracted_item.modifiers,
                    special_instructions=extracted_item.special_instructions,
                    menu_item_id=menu_item.id,
                    resolved_name=menu_item.name,
                    confidence=0.9,
                    is_ambiguous=False,
                    suggested_options=[],
                    clarification_question=None
                ))
                    
            else:
                # Multiple matches - use LLM for disambiguation
                print(f"   🤔 Multiple matches found: {[item.name for item in matches]}")
                
                # Use helper function for LLM disambiguation
                best_match = await _disambiguate_with_llm(matches, extracted_item.item_name)
                
                if best_match == "CLARIFICATION_NEEDED":
                    # LLM determined clarification is needed
                    print(f"   ❓ LLM determined clarification needed")
                    needs_clarification = True
                    clarification_questions.append(f"Did you mean: {', '.join([item.name for item in matches[:3]])}?")
                    resolved_items.append(ResolvedItem(
                        item_name=extracted_item.item_name,
                        quantity=extracted_item.quantity,
                        size=extracted_item.size,
                        modifiers=extracted_item.modifiers,
                        special_instructions=extracted_item.special_instructions,
                        menu_item_id=0,
                        resolved_name=None,
                        confidence=0.5,
                        is_ambiguous=True,
                        suggested_options=[item.name for item in matches[:3]],
                        clarification_question=f"Did you mean: {', '.join([item.name for item in matches[:3]])}?"
                    ))
                else:
                    # LLM found a good match
                    print(f"   ✅ LLM selected: '{best_match}'")
                    selected_item = next((item for item in matches if item.name == best_match), None)
                    if selected_item:
                        resolved_items.append(ResolvedItem(
                            item_name=extracted_item.item_name,
                            quantity=extracted_item.quantity,
                            size=extracted_item.size,
                            modifiers=extracted_item.modifiers,
                            special_instructions=extracted_item.special_instructions,
                            menu_item_id=selected_item.id,
                            resolved_name=selected_item.name,
                            confidence=0.8,
                            is_ambiguous=False,
                            suggested_options=[],
                            clarification_question=None
                        ))
                    else:
                        # LLM returned something not in matches - treat as clarification needed
                        print(f"   ⚠️ LLM returned invalid match, treating as clarification needed")
                        needs_clarification = True
                        clarification_questions.append(f"Did you mean: {', '.join([item.name for item in matches[:3]])}?")
                        resolved_items.append(ResolvedItem(
                            item_name=extracted_item.item_name,
                            quantity=extracted_item.quantity,
                            size=extracted_item.size,
                            modifiers=extracted_item.modifiers,
                            special_instructions=extracted_item.special_instructions,
                            menu_item_id=0,
                            resolved_name=None,
                            confidence=0.5,
                            is_ambiguous=True,
                            suggested_options=[item.name for item in matches[:3]],
                            clarification_question=f"Did you mean: {', '.join([item.name for item in matches[:3]])}?"
                        ))
        
        # Create final response
        # Success if we have resolved items (even if some are unavailable or ambiguous)
        success = len(resolved_items) > 0
        confidence = 0.9 if success and not needs_clarification else 0.7
        
        print(f"🔍 DEBUG - MENU RESOLUTION AGENT:")
        print(f"   Success: {success}")
        print(f"   Confidence: {confidence}")
        print(f"   Items resolved: {len(resolved_items)}")
        for i, item in enumerate(resolved_items):
            print(f"     Item {i+1}: '{item.item_name}' → {item.resolved_name or 'None'} (ambiguous: {item.is_ambiguous}, unavailable: {item.is_unavailable})")
        
        return MenuResolutionResponse(
            success=success,
            confidence=confidence,
            resolved_items=resolved_items,
            needs_clarification=needs_clarification,
            clarification_questions=clarification_questions
        )
            
    except Exception as e:
        print(f"🔍 DEBUG - Menu resolution agent failed: {e}")
        logger.error(f"Menu resolution agent failed: {e}")
        return MenuResolutionResponse(
            success=False,
            confidence=0.0,
            resolved_items=[],
            needs_clarification=True,
            clarification_questions=["There was an error accessing the menu. Please try again later."]
        )


async def _disambiguate_with_llm(matches: List[Any], user_request: str) -> str:
    """
    Use LLM to disambiguate between multiple matches.
    
    Args:
        matches: List of MenuItem objects that matched
        user_request: Original user request
        
    Returns:
        Selected item name or "CLARIFICATION_NEEDED"
    """
    try:
        from app.commands.command_type_schema import CommandType
        clarification_needed = CommandType.CLARIFICATION_NEEDED.value
        
        prompt = f"""
        User requested: "{user_request}"
        Found these menu items: {[item.name for item in matches]}
        
        Which one did they mean? Consider:
        - Fuzzy matching and context
        - Most common/popular choice
        - Return the exact menu item name
        
        IMPORTANT: Only choose a specific item if there's a clear, obvious choice.
        If the matches are equally valid (like "French Fries" vs "Large French Fries"), 
        return "{clarification_needed}" instead of guessing.
        
        Just return the best match name or "{clarification_needed}", nothing else.
        """
        
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            api_key=settings.OPENAI_API_KEY
        )
        
        response = await llm.ainvoke(prompt)
        best_match = response.content.strip().strip('"').strip("'")
        print(f"   🧠 LLM chose: {best_match}")
        
        return best_match
        
    except Exception as e:
        print(f"   ❌ LLM disambiguation failed: {e}")
        return "CLARIFICATION_NEEDED"