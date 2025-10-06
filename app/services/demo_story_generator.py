"""
Demo Story Generator for testing purposes
This creates enhanced D&D stories without requiring OpenAI API
"""

from typing import Dict, Any
import random

class DemoStoryGenerator:
    """Demo story generator that creates enhanced D&D narratives without API calls"""

    def __init__(self):
        self.enhancement_templates = {
            'combat': [
                "The clash of steel rang through the air as",
                "With a thunderous roar, the battle erupted when",
                "The tension broke like a snapped bowstring as",
                "In a moment of deadly silence before the storm,"
            ],
            'dialogue': [
                "The words hung heavy in the air:",
                "With determination gleaming in their eyes, they declared:",
                "The voice echoed with authority and purpose:",
                "In hushed, urgent tones, the warning came:",
            ],
            'atmosphere': [
                "The ancient stones seemed to whisper of forgotten secrets,",
                "An otherworldly presence filled the chamber,",
                "The very air crackled with magical energy as",
                "Shadows danced ominously across the walls while",
            ]
        }

    def enhance_story(self, original_text: str, session_name: str = "Unknown Session") -> str:
        """Create an enhanced version of the original D&D session text"""

        # Extract key elements
        has_combat = any(word in original_text.lower() for word in ['combat', 'battle', 'attack', 'damage', 'roll', 'initiative'])
        has_dialogue = '"' in original_text or "'" in original_text
        has_magic = any(word in original_text.lower() for word in ['magic', 'spell', 'cast', 'wizard', 'cleric'])

        # Create enhanced narrative
        enhanced_story = f"""# 🎲 Enhanced D&D Story: {session_name}

## ✨ AI-Enhanced Narrative

*The following story has been crafted from your session notes, with enhanced descriptions, dramatic tension, and rich narrative elements that bring your D&D adventure to life.*

---

"""

        # Add atmospheric opening
        if 'keep' in original_text.lower() or 'fortress' in original_text.lower():
            enhanced_story += random.choice(self.enhancement_templates['atmosphere']) + " the ancient fortress loomed before our heroes.\n\n"
        elif 'dungeon' in original_text.lower() or 'cavern' in original_text.lower():
            enhanced_story += random.choice(self.enhancement_templates['atmosphere']) + " the depths beckoned with promise and peril.\n\n"
        else:
            enhanced_story += random.choice(self.enhancement_templates['atmosphere']) + " the adventure began to unfold.\n\n"

        # Process the original text and enhance key moments
        lines = original_text.split('\n')
        in_combat = False

        for line in lines:
            line = line.strip()
            if not line:
                enhanced_story += "\n"
                continue

            # Enhance combat sections
            if any(word in line.lower() for word in ['initiative', 'attack', 'damage', 'combat encounter']):
                if not in_combat:
                    enhanced_story += f"\n{random.choice(self.enhancement_templates['combat'])} "
                    in_combat = True
                enhanced_story += f"**{line}**\n\n"
                enhanced_story += "*The battlefield erupted into controlled chaos, each combatant moving with deadly precision and purpose.*\n\n"

            # Enhance dialogue
            elif '"' in line or line.endswith('"):') or line.endswith("'):"):
                enhanced_story += f"{random.choice(self.enhancement_templates['dialogue'])} \n\n"
                enhanced_story += f"*\"{line.replace('\"', '')}\"*\n\n"

            # Enhance DM descriptions
            elif line.startswith('DM:'):
                enhanced_story += f"**The Dungeon Master's Voice:** {line[3:].strip()}\n\n"
                enhanced_story += "*The scene unfolds with vivid detail, drawing the players deeper into the immersive world.*\n\n"

            # Regular lines
            else:
                enhanced_story += f"{line}\n\n"

        # Add epic conclusion
        enhanced_story += """
---

## 🌟 Session Highlights

**Epic Moments:** This session showcased incredible teamwork, strategic thinking, and memorable roleplay that will be remembered for campaigns to come.

**Character Development:** Each hero grew not just in power, but in the bonds that tie them together as a legendary adventuring party.

**World Building:** The rich tapestry of this fantasy realm continues to unfold, with new mysteries and adventures waiting beyond every door.

*This enhanced narrative captures the spirit and excitement of your D&D session, transforming raw notes into an epic tale worthy of the greatest fantasy adventures.*

---

💡 **Note:** This is a demo enhancement. With a configured OpenAI API key, you would receive even more sophisticated AI-generated improvements including character analysis, plot development, and personalized narrative enhancements.
"""

        return enhanced_story

# Create a global instance for use in the application
demo_generator = DemoStoryGenerator()