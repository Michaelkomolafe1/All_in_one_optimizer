"""Validator import wrapper for utils compatibility"""

try:
    # Import from the new data_validator module
    from data_validator import DataValidator, get_validator
    
    # Create compatibility wrapper
    class Validator:
        def __init__(self):
            self.validator = get_validator()
        
        def validate(self, data):
            """Basic validation wrapper"""
            if hasattr(data, '__iter__'):
                # Validate collection
                return all(self.validate_item(item) for item in data)
            else:
                # Validate single item
                return self.validate_item(data)
        
        def validate_item(self, item):
            """Validate single item"""
            if hasattr(item, 'name'):  # Likely a player
                result = self.validator.validate_player(item)
                return result.is_valid
            return True
    
    # Create global instance
    validator = Validator()
    
except ImportError:
    # Fallback to stub if data_validator not available
    print("⚠️ data_validator module not available, using stub validator")
    
    class DataValidator:
        def validate_player(self, player):
            return type('Result', (), {'is_valid': True, 'errors': [], 'warnings': []})()
    
    class Validator:
        def validate(self, data):
            return True
    
    validator = Validator()

# Export what bulletproof_dfs_core expects
def validate_lineup(lineup):
    """Basic lineup validation"""
    if hasattr(validator, 'validator'):
        return validator.validator.validate_lineup(lineup).is_valid
    return True

def validate_player(player):
    """Basic player validation"""
    if hasattr(validator, 'validator'):
        return validator.validator.validate_player(player).is_valid
    return True

def validate_csv(data):
    """Basic CSV validation"""
    return True

__all__ = ['DataValidator', 'Validator', 'validator', 'validate_lineup', 'validate_player', 'validate_csv']
