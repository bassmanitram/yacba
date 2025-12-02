"""
Tag management actions for YACBA CLI.

Handles actions for conversation position tagging:
- tag: Create tags
- undo: Undo N messages or restore to a tag
- tags: List all tags with validation
"""

from repl_toolkit import Action, ActionContext, ActionRegistry

from ..tag_manager import TagManager, is_user_input_message
from utils.logging import get_logger

logger = get_logger(__name__)


def find_user_input_positions(messages) -> list:
    """Find positions of actual user input messages (excluding tool results).
    
    Args:
        messages: List of messages
        
    Returns:
        List of positions (indices), newest first
    """
    positions = []
    for i in range(len(messages) - 1, -1, -1):
        if is_user_input_message(messages[i]):
            positions.append(i)
    return positions


def handle_tag(context: ActionContext) -> None:
    """Handle the tag command.
    
    Usage:
        tag - Create anonymous tag at current position
        tag <name> - Create named tag at current position
        tag <name> <position> - Create tag at specific position
    """
    args = context.args
    printer = context.printer
    backend = context.backend
    
    try:
        # Get tag manager from backend
        tag_manager = backend.tag_manager
        agent_proxy = backend.get_agent_proxy()
        messages = agent_proxy.messages
        position = len(messages)
        
        # No args: create anonymous tag
        if not args:
            try:
                tag_name = tag_manager.generate_anonymous_tag(position, messages)
                printer(f"Tag '{tag_name}' created at position {position}")
            except ValueError as e:
                printer(f"Error: {e}")
            return
        
        # One arg: tag current position with given name
        if len(args) == 1:
            tag_name = args[0]
            
            try:
                tag_manager.set_tag(tag_name, position, messages)
                printer(f"Tag '{tag_name}' created at position {position}")
            except ValueError as e:
                printer(f"Error: {e}")
            return
        
        # Two args: tag specific position
        if len(args) == 2:
            tag_name = args[0]
            try:
                position = int(args[1])
            except ValueError:
                printer(f"Error: Position must be a number, got '{args[1]}'")
                return
            
            try:
                tag_manager.set_tag(tag_name, position, messages)
                printer(f"Tag '{tag_name}' created at position {position}")
            except ValueError as e:
                printer(f"Error: {e}")
            return
        
        # Too many args
        printer("Error: tag command takes 0-2 arguments")
        printer("Usage: /tag [name] [position]")
        
    except Exception as e:
        printer(f"Unexpected error in tag command: {e}")
        logger.error("error_in_tag_command", error=str(e))


def handle_undo(context: ActionContext) -> None:
    """Handle the undo command.
    
    Usage:
        undo - Undo last user input message (default: 1)
        undo <N> - Undo N user input messages
        undo <tag> - Restore to tagged position
    """
    args = context.args
    printer = context.printer
    backend = context.backend
    
    try:
        # Get components
        tag_manager = backend.tag_manager
        agent_proxy = backend.get_agent_proxy()
        
        # No args: default to undo 1
        if not args:
            result = handle_undo_n_user_messages(1, agent_proxy, tag_manager)
            printer(result)
            return
        
        arg = args[0]
        
        # Try to parse as number
        try:
            n = int(arg)
            result = handle_undo_n_user_messages(n, agent_proxy, tag_manager)
            printer(result)
        except ValueError:
            # Not a number, treat as tag name
            result = handle_undo_to_tag(arg, agent_proxy, tag_manager)
            printer(result)
    
    except Exception as e:
        printer(f"Unexpected error in undo command: {e}")
        logger.error("error_in_undo_command", error=str(e))


def handle_undo_n_user_messages(n: int, agent_proxy, tag_manager: TagManager) -> str:
    """Undo N user input messages (excluding tool results).
    
    If N exceeds available user messages, clears all messages.
    Removes any tags that become out of scope.
    Recreates __session_start__ if all messages cleared.
    
    Args:
        n: Number of user input messages to remove
        agent_proxy: Agent proxy instance
        tag_manager: TagManager instance
        
    Returns:
        Success/error message
    """
    if n <= 0:
        return "Error: Must undo at least 1 message"
    
    messages = agent_proxy.messages
    current_count = len(messages)
    user_input_positions = find_user_input_positions(messages)
    
    # Determine target position
    if n >= len(user_input_positions):
        # Clear all messages
        target_position = 0
        user_messages_removed = len(user_input_positions)
        total_removed = current_count
        undo_msg = f"Removed all {user_messages_removed} user messages ({total_removed} total messages)"
    else:
        # Get the Nth user input message position from the end
        target_position = user_input_positions[n - 1]
        total_removed = current_count - target_position
        undo_msg = f"Removed last {n} user messages ({total_removed} total messages)"
    
    # Validate target_position is in scope
    if target_position < 0 or target_position > current_count:
        logger.error(
            "invalid_target_position_in_undo",
            target_position=target_position,
            current_count=current_count
        )
        return f"Error: Invalid target position {target_position} (current count: {current_count})"
    
    # Use agent_proxy.truncate_messages_to() for proper disk cleanup
    try:
        success = agent_proxy.truncate_messages_to(target_position)
        if not success:
            logger.error("truncate_messages_to_returned_false")
            return "Error: Failed to truncate messages"
    except ValueError as e:
        logger.error("truncate_messages_to_raised_error", error=str(e))
        return f"Error: {e}"
    except Exception as e:
        logger.error("unexpected_error_in_truncate", error=str(e))
        return f"Error: Unexpected failure during undo: {e}"
    
    # Remove tags that are now out of scope
    removed_tags = tag_manager.remove_tags_beyond_position(target_position)
    
    # Recreate __session_start__ if we cleared everything
    if target_position == 0:
        tag_manager.create_session_start_tag(0)
    
    # Build response message
    if removed_tags:
        tag_msg = f"\nTags removed: {', '.join(removed_tags)}"
        return undo_msg + tag_msg
    
    return undo_msg


def handle_undo_to_tag(
    tag_name: str, 
    agent_proxy, 
    tag_manager: TagManager
) -> str:
    """Undo to a tagged position with validation.
    
    The tagged message is preserved (inclusive).
    Invalid tags are automatically removed.
    
    Args:
        tag_name: Name of tag to undo to
        agent_proxy: Agent proxy instance
        tag_manager: TagManager instance
        
    Returns:
        Success/error message
    """
    tag = tag_manager.get_tag(tag_name)
    
    if tag is None:
        return f"Error: Tag '{tag_name}' not found"
    
    # Validate tag
    messages = agent_proxy.messages
    current_count = len(messages)
    is_valid, error = tag_manager.validate_tag(tag, messages)
    
    if not is_valid:
        # Remove invalid tag
        tag_manager.remove_tag(tag_name)
        return f"Error: Tag '{tag_name}' is no longer valid ({error}). Tag removed."
    
    current_position = current_count
    
    if tag.position == current_position:
        return f"Already at tag '{tag_name}' (position {current_position})"
    
    # Calculate target position - keep messages [0:tag.position+1] (tag.position is inclusive)
    target_position = tag.position + 1
    
    # Validate target_position is in scope
    if target_position < 0 or target_position > current_count:
        logger.error(
            "invalid_target_position_in_tag_undo",
            tag_name=tag_name,
            tag_position=tag.position,
            target_position=target_position,
            current_count=current_count
        )
        return f"Error: Invalid tag position (tag at {tag.position}, current count: {current_count})"
    
    messages_removed = current_count - target_position
    
    # Use agent_proxy.truncate_messages_to() for proper disk cleanup
    try:
        success = agent_proxy.truncate_messages_to(target_position)
        if not success:
            logger.error("truncate_messages_to_returned_false_for_tag", tag_name=tag_name)
            return f"Error: Failed to restore to tag '{tag_name}'"
    except ValueError as e:
        logger.error("truncate_messages_to_raised_error_for_tag", tag_name=tag_name, error=str(e))
        return f"Error: {e}"
    except Exception as e:
        logger.error("unexpected_error_in_tag_undo", tag_name=tag_name, error=str(e))
        return f"Error: Unexpected failure during undo to tag: {e}"
    
    # Remove tags that are now out of scope
    removed_tags = tag_manager.remove_tags_beyond_position(target_position)
    
    result = f"Restored to tag '{tag_name}' (removed {messages_removed} messages)"
    
    # Report removed tags if any
    if removed_tags:
        result += f"\nTags removed: {', '.join(removed_tags)}"
    
    return result


def handle_tags_command(context: ActionContext) -> None:
    """List all tags with validation status.
    
    Invalid tags are automatically removed and reported.
    """
    printer = context.printer
    backend = context.backend
    
    try:
        # Get components
        tag_manager = backend.tag_manager
        agent_proxy = backend.get_agent_proxy()
        messages = agent_proxy.messages
        
        tags = tag_manager.list_tags()
        
        if not tags:
            printer("No tags defined")
            return
        
        lines = ["Current tags:"]
        invalid_tags = []
        
        for tag in tags:
            # Validate each tag
            is_valid, error = tag_manager.validate_tag(tag, messages)
            
            if is_valid:
                timestamp = tag.timestamp.strftime("%H:%M:%S")
                line = f"  {tag.name:20s} → position {tag.position:4d} ({timestamp})"
                lines.append(line)
            else:
                # Show invalid tag details with reason
                timestamp = tag.timestamp.strftime("%H:%M:%S")
                line = f"  {tag.name:20s} → position {tag.position:4d} INVALIDATED: {error}"
                lines.append(line)
                invalid_tags.append(tag.name)
        
        # Auto-remove invalid tags
        for tag_name in invalid_tags:
            tag_manager.remove_tag(tag_name)
        
        if invalid_tags:
            lines.append("")
            lines.append(f"Removed {len(invalid_tags)} invalid tag(s): {', '.join(invalid_tags)}")
        
        printer("\n".join(lines))
        
    except Exception as e:
        printer(f"Error listing tags: {e}")
        logger.error("error_listing_tags", error=str(e))


def register_tag_actions(registry: ActionRegistry) -> None:
    """Register tag management actions."""
    
    tag_action = Action(
        name="tag",
        command="/tag",
        handler=handle_tag,
        category="Tag Management",
        description="Create a conversation position tag",
        command_usage="/tag [name] [position] - Create tag at current or specified position",
    )
    
    undo_action = Action(
        name="undo",
        command="/undo",
        handler=handle_undo,
        category="Tag Management",
        description="Undo user message sequences, or revert to tag",
        command_usage="/undo [N|tag] - Undo last message (default 1), N messages, or restore to tag",
    )
    
    tags_action = Action(
        name="tags",
        command="/tags",
        handler=handle_tags_command,
        category="Tag Management",
        description="List all tags with validation status",
        command_usage="/tags - Show all conversation position tags",
    )
    
    registry.register_action(tag_action)
    registry.register_action(undo_action)
    registry.register_action(tags_action)
