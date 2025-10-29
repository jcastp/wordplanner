"""
Pattern Utilities Module

This module provides functions for configuring writing patterns
for variable daily goal distribution.
"""

from ui_utils import get_menu_choice, get_yes_no


def get_pattern_intensity_config(pattern_type):
    """
    Get pattern intensity configuration from user.

    Args:
        pattern_type: Type of pattern ('valley', 'mountain', 'rising', 'declining', 'random')

    Returns:
        dict: Pattern configuration dictionary with multipliers
    """
    if pattern_type in ["valley", "mountain"]:
        return _get_peak_valley_intensity()
    elif pattern_type in ["rising", "declining"]:
        return _get_slope_intensity(pattern_type)
    elif pattern_type == "random":
        return _get_random_intensity()
    else:
        return {}


def _get_peak_valley_intensity():
    """
    Get intensity configuration for valley/mountain patterns.

    Returns:
        dict: Configuration with peak_multiplier and valley_multiplier
    """
    print("\nPattern intensity (how extreme the variation):")
    print("1. Mild (varies between 0.8x and 1.2x average)")
    print("2. Moderate (varies between 0.7x and 1.5x average) [default]")
    print("3. Extreme (varies between 0.5x and 2.0x average)")

    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()

    if intensity_choice == "1":
        return {'peak_multiplier': 1.2, 'valley_multiplier': 0.8}
    elif intensity_choice == "3":
        return {'peak_multiplier': 2.0, 'valley_multiplier': 0.5}
    else:
        return {'peak_multiplier': 1.5, 'valley_multiplier': 0.7}


def _get_slope_intensity(pattern_type):
    """
    Get intensity configuration for rising/declining patterns.

    Args:
        pattern_type: 'rising' or 'declining'

    Returns:
        dict: Configuration with start_multiplier and end_multiplier
    """
    print("\nPattern intensity:")
    print("1. Mild (varies between 0.8x and 1.2x average)")
    print("2. Moderate (varies between 0.5x and 1.5x average) [default]")
    print("3. Extreme (varies between 0.3x and 2.0x average)")

    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()

    if intensity_choice == "1":
        if pattern_type == "rising":
            return {'start_multiplier': 0.8, 'end_multiplier': 1.2}
        else:
            return {'start_multiplier': 1.2, 'end_multiplier': 0.8}
    elif intensity_choice == "3":
        if pattern_type == "rising":
            return {'start_multiplier': 0.3, 'end_multiplier': 2.0}
        else:
            return {'start_multiplier': 2.0, 'end_multiplier': 0.3}
    else:
        if pattern_type == "rising":
            return {'start_multiplier': 0.5, 'end_multiplier': 1.5}
        else:
            return {'start_multiplier': 1.5, 'end_multiplier': 0.5}


def _get_random_intensity():
    """
    Get intensity configuration for random pattern.

    Returns:
        dict: Configuration with min_multiplier and max_multiplier
    """
    print("\nRandom variation range:")
    print("1. Mild (varies between 0.8x and 1.2x average)")
    print("2. Moderate (varies between 0.5x and 1.5x average) [default]")
    print("3. Extreme (varies between 0.3x and 2.0x average)")

    intensity_choice = input("\nEnter your choice (1-3, or Enter for default): ").strip()

    config = {}
    if intensity_choice == "1":
        config = {'min_multiplier': 0.8, 'max_multiplier': 1.2}
    elif intensity_choice == "3":
        config = {'min_multiplier': 0.3, 'max_multiplier': 2.0}
    else:
        config = {'min_multiplier': 0.5, 'max_multiplier': 1.5}

    # Optional seed for reproducibility
    use_seed = get_yes_no("Use a fixed seed for reproducible randomness?", default='n')
    if use_seed:
        import random
        config['seed'] = random.randint(1, 1000000)

    return config


def choose_writing_pattern():
    """
    Display pattern selection menu and return pattern choice.

    Returns:
        tuple: (pattern_name, pattern_config)
    """
    print("\n" + "=" * 50)
    print("WRITING PATTERN")
    print("=" * 50)
    print("\nHow would you like to distribute your daily word goals?")
    print("\n1. Flat/Steady - Same daily goal every day (default)")
    print("2. Valley - Start high, ease in middle, finish high")
    print("3. Mountain - Start easy, peak in middle, ease at end")
    print("4. Rising - Gradually increase goals over time")
    print("5. Declining - Gradually decrease goals over time")
    print("6. Random - Varied daily goals within a range")
    print("\n0. Skip (use flat pattern)")
    print("=" * 50)

    choice = get_menu_choice("\nEnter your choice (0-6): ", 0, 6)

    pattern_map = {
        0: "flat",
        1: "flat",
        2: "valley",
        3: "mountain",
        4: "rising",
        5: "declining",
        6: "random"
    }
    pattern = pattern_map[choice]

    # Get pattern configuration if needed
    pattern_config = {}
    if pattern != "flat":
        pattern_config = get_pattern_intensity_config(pattern)

    return pattern, pattern_config


def get_pattern_description(pattern_name):
    """
    Get a human-readable description of a pattern.

    Args:
        pattern_name: Name of the pattern

    Returns:
        str: Description of the pattern
    """
    descriptions = {
        'flat': "Steady - Same daily goal every day",
        'valley': "Valley - Start high, ease in middle, finish high",
        'mountain': "Mountain - Start easy, peak in middle, ease at end",
        'rising': "Rising - Gradually increase goals over time",
        'declining': "Declining - Gradually decrease goals over time",
        'random': "Random - Varied daily goals within a range"
    }
    return descriptions.get(pattern_name, pattern_name.capitalize())
