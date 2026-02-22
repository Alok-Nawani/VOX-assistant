import parsedatetime
from datetime import datetime
from typing import Optional, Tuple

def extract_datetime(text: str) -> Optional[Tuple[datetime, datetime]]:
    """Extract date and time information from natural language text
    
    Args:
        text: Natural language text containing date/time information
        
    Returns:
        Tuple of (start_time, end_time) as datetime objects, or None if no time found
    """
    cal = parsedatetime.Calendar()
    
    try:
        # Try to extract time info
        start_struct, start_parsed = cal.parse(text)
        
        if start_parsed == 0:
            return None
            
        start_time = datetime(*start_struct[:6])
        
        # Look for duration/end time after the start time
        remaining_text = text[text.lower().find(start_time.strftime("%I:%M %p").lower()):]
        end_struct = None
        
        # Check for duration words
        duration_words = ["for", "until", "till", "to"]
        for word in duration_words:
            if word in remaining_text.lower():
                duration_text = remaining_text[remaining_text.lower().find(word):]
                end_struct, end_parsed = cal.parse(duration_text)
                if end_parsed > 0:
                    break
                    
        if end_struct:
            end_time = datetime(*end_struct[:6])
        else:
            # Default to 1 hour duration
            end_time = start_time.replace(hour=start_time.hour + 1)
            
        return start_time, end_time
        
    except Exception:
        return None
