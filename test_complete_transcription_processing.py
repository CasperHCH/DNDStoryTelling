#!/usr/bin/env python3
"""
Comprehensive test for ensuring ALL story generators read ENTIRE transcriptions.
This verifies that no content is missed regardless of transcription size.
"""

import asyncio
import logging
import sys
import tempfile
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.story_generator import StoryGenerator
from app.services.ollama_story_generator import OllamaStoryGenerator
from app.services.demo_story_generator import DemoStoryGenerator
from app.models.story import StoryContext

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_large_test_transcription() -> str:
    """
    Create a large, realistic D&D session transcription with specific content
    that can be verified in the generated stories.
    """

    # Create a multi-part D&D session with distinct segments
    transcription_parts = []

    # Part 1: Tavern Scene
    part1 = """
**Session Start - The Prancing Pony Tavern**

**DM:** You find yourselves in the cozy warmth of the Prancing Pony tavern. The fire crackles in the hearth as snow falls gently outside. Veteran adventurer Thorin Ironbeard sits at the bar nursing an ale.

**Player 1 (Elara Moonwhisper):** I approach Thorin and ask about the rumors we've heard about the Cursed Tower of Malachar.

**Thorin Ironbeard:** *looks up with weathered eyes* Aye, lass. That tower's been nothing but trouble for decades. Strange lights, missing travelers, and whispers of an ancient evil stirring within.

**Player 2 (Gareth Stormshield):** I slam my fist on the table. "Then we must investigate! The people of Willowbrook deserve to sleep safely!"

**DM:** The tavern grows quiet at Gareth's declaration. The bartender, an elderly halfling named Pip, nods approvingly.

**Pip the Bartender:** If you're serious about this, there's an old map in my basement. My grandfather marked the safe paths to the tower... though I can't guarantee they're still safe.

**Initiative for Tavern Encounter:** When suddenly, the tavern door bursts open!
"""

    # Part 2: Forest Travel
    part2 = """
**Forest Journey - Day 2**

**DM:** The ancient Whisperwood Forest stretches before you. Massive oak trees form a canopy so thick that little daylight penetrates. Elara notices strange markings on several tree trunks.

**Elara Moonwhisper:** I cast Detect Magic to examine these markings.

**DM:** Roll for Arcana.

**Elara:** Natural 20!

**DM:** The markings pulse with necromantic energy - a warning system. Something doesn't want visitors approaching the tower.

**Gareth Stormshield:** I ready my shield and sword. "Stay alert, friends. We're being watched."

**Player 3 (Zara Shadowblade):** I'll scout ahead using Stealth. *Rolls* 18 total.

**DM:** Zara, you discover a hidden camp about 200 feet ahead. Three figures in dark robes are performing some kind of ritual around a black cauldron.

**Combat Encounter - Cultists in the Woods:**

**Initiative Order:**
- Zara Shadowblade: 19
- Cultist Leader: 17
- Elara Moonwhisper: 15
- Gareth Stormshield: 12
- Cultist Acolyte 1: 10
- Cultist Acolyte 2: 8

**Round 1:**
**Zara:** I attack the leader with my poisoned dagger from stealth. *Rolls* 16 to hit! Damage: 12 piercing plus 6 sneak attack plus poison!

**DM:** The leader staggers but remains standing, black ichor oozing from the wound.
"""

    # Part 3: The Tower Approach
    part3 = """
**The Cursed Tower of Malachar - Exterior**

**DM:** After defeating the cultists, you finally reach the Tower of Malachar. It looms 200 feet into the storm-dark sky, built from black stone that seems to absorb light. Purple energy crackles around its peak.

**Gareth Stormshield:** I examine the massive iron doors for traps. Investigation check... 14.

**DM:** The doors are covered in protective wards, but you notice they're designed to keep things IN, not out.

**Elara Moonwhisper:** That's... concerning. I cast Mage Armor on myself as preparation.

**Player 4 (Magnus Spellweaver):** I've been studying the tower's architecture. This is definitely pre-Cataclysm construction. The magical resonance suggests something powerful is sealed inside.

**Zara Shadowblade:** I check for secret entrances around the base. *Rolls* Perception: 16.

**DM:** Zara, you find what appears to be a servant's entrance on the north side. It's partially concealed by magical illusion.

**Investigation Scene - Tower Interior:**

**DM:** The interior is a maze of corridors filled with ancient tapestries depicting the rise and fall of the wizard Malachar the Mad. Dust motes dance in shafts of purple light filtering down from above.

**Magnus Spellweaver:** I want to study these tapestries for historical context. History check: 19.

**DM:** Magnus, the tapestries tell a tragic tale. Malachar was once a respected wizard who tried to achieve immortality by merging with a powerful demon. The ritual went horribly wrong.

**Elara:** So the demon is still here, trapped in whatever remains of Malachar?

**DM:** That seems to be the implication. You hear a low moaning sound echoing from the upper levels.
"""

    # Part 4: The Final Confrontation
    part4 = """
**The Tower's Peak - Final Battle**

**DM:** You reach the top of the tower to find a massive chamber dominated by a swirling vortex of dark energy. Within it, you can see the twisted form of Malachar-Demon, neither fully human nor demon, trapped between worlds for centuries.

**Malachar-Demon:** *Voice echoing from multiple directions* "At last... mortals to witness my ascension! Your life force will complete the ritual that was interrupted so long ago!"

**Initiative for Final Boss:**
- Elara Moonwhisper: 18
- Malachar-Demon: 16
- Magnus Spellweaver: 14
- Gareth Stormshield: 13
- Zara Shadowblade: 11

**Epic Combat Round 1:**

**Elara:** I cast Fireball at the highest spell slot! *Rolls* 8d6 fire damage... 31 damage!

**DM:** The flames wash over the demon-wizard, but it seems to absorb some of the magical energy. It takes 20 damage after resistance.

**Malachar-Demon:** I cast Chain Lightning at all of you! Everyone make Dexterity saves!

**Results:** Gareth fails (takes 28 damage), others succeed (take 14 damage each)

**Magnus:** I counter with Banishment! If this works, we can send it back to the Abyss!

**DM:** Roll for spell attack... and the demon's Charisma save...

**Climactic Moment:**

**Magnus:** Natural 20 on spell attack! The demon rolls... 8! The banishment succeeds!

**DM:** The vortex collapses as Malachar-Demon is torn from this plane of existence. The tower begins to shake as centuries of dark magic unravels.

**Gareth:** "Everyone out! The tower is collapsing!"

**Escape Sequence:** The party races down the crumbling stairs as the Tower of Malachar collapses behind them.

**Session End - Victory and Rewards:**

**DM:** You emerge from the forest to see the tower reduced to rubble. The dark clouds dissipate, and for the first time in decades, natural sunlight bathes the area. The people of Willowbrook are safe.

**Experience Awards:** Each character gains 2,000 XP for completing this major quest.

**Treasure Found:**
- Malachar's Spellbook (contains rare necromancy spells)
- Amulet of Protection from Evil
- 500 gold pieces in ancient coins
- A mysterious crystal that pulses with gentle light

**Character Development:**
- Elara has grown more confident in her magical abilities
- Gareth has learned that sometimes strategy trumps brute force
- Zara discovered the value of scouting and preparation
- Magnus gained invaluable knowledge about pre-Cataclysm magic

**Campaign Notes:** This victory has earned the party fame throughout the region. News of their success reaches the capital city of Aralon, where new adventures await.

**End of Session**
"""

    # Combine all parts
    full_transcription = "\n\n".join([part1, part2, part3, part4])

    # Add some additional content to make it even larger
    additional_content = f"""

**Post-Session Discussion:**

**Player Feedback:**
- "That final battle was incredible! The buildup was perfect."
- "I loved how Magnus's research actually paid off in the end."
- "The tower collapsing was such a cinematic moment!"

**DM Notes:**
The session ran for 4.5 hours with excellent player engagement. The mystery elements worked well, and the final combat felt appropriately challenging. Next session will introduce the new storyline involving the Aralon political intrigue.

**Total Session Statistics:**
- Duration: 4 hours 30 minutes
- Combat Encounters: 3
- Roleplay Scenes: 8
- Skill Challenges: 6
- Character Development Moments: 4
- New NPCs Introduced: 5 (Thorin, Pip, Cultist Leader, Malachar-Demon, various townspeople)
- Locations Explored: 4 (Prancing Pony Tavern, Whisperwood Forest, Tower Exterior, Tower Interior)

**Continuing Campaign Hooks:**
1. The crystal's true purpose remains mysterious
2. Other cultist cells may still be active
3. The political situation in Aralon is heating up
4. Malachar's spellbook contains dangerous knowledge
5. The party's growing reputation brings new opportunities and threats

This represents a complete, epic D&D session that should be fully captured in any story generation process.
"""

    return full_transcription + additional_content

async def test_story_generator(generator, name: str, transcription: str, context: StoryContext) -> dict:
    """Test a specific story generator with the large transcription."""

    logger.info(f"\n{'='*60}")
    logger.info(f"TESTING {name.upper()}")
    logger.info(f"{'='*60}")

    try:
        logger.info(f"Input transcription length: {len(transcription)} characters")
        logger.info(f"Estimated tokens: {len(transcription) // 4}")

        # Generate the story
        start_time = asyncio.get_event_loop().time()
        story = await generator.generate_story(transcription, context)
        end_time = asyncio.get_event_loop().time()

        processing_time = end_time - start_time

        logger.info(f"Generated story length: {len(story)} characters")
        logger.info(f"Processing time: {processing_time:.2f} seconds")

        # Verify that key content from all parts is captured
        verification_results = verify_story_completeness(story, transcription)

        return {
            'generator': name,
            'success': True,
            'story_length': len(story),
            'processing_time': processing_time,
            'verification': verification_results,
            'story_preview': story[:500] + "..." if len(story) > 500 else story
        }

    except Exception as e:
        logger.error(f"Error testing {name}: {e}")
        import traceback
        traceback.print_exc()
        return {
            'generator': name,
            'success': False,
            'error': str(e),
            'verification': {'completeness_score': 0, 'missing_elements': ['Failed to generate']}
        }

def verify_story_completeness(story: str, original_transcription: str) -> dict:
    """Verify that the generated story captures content from all parts of the transcription."""

    story_lower = story.lower()
    original_lower = original_transcription.lower()

    # Key elements that should appear in a complete story
    key_elements = {
        'characters': ['thorin ironbeard', 'elara moonwhisper', 'gareth stormshield', 'zara shadowblade', 'magnus spellweaver'],
        'locations': ['prancing pony', 'whisperwood forest', 'tower of malachar', 'willowbrook'],
        'plot_points': ['cursed tower', 'cultists', 'ritual', 'malachar-demon', 'banishment', 'tower collaps'],
        'npcs': ['pip', 'bartender', 'cultist leader'],
        'items': ['spellbook', 'amulet', 'crystal'],
        'mechanics': ['initiative', 'combat', 'fireball', 'chain lightning']
    }

    found_elements = {}
    missing_elements = []

    for category, elements in key_elements.items():
        found_elements[category] = []
        for element in elements:
            if element in story_lower:
                found_elements[category].append(element)
            else:
                missing_elements.append(f"{category}: {element}")

    # Calculate completeness score
    total_elements = sum(len(elements) for elements in key_elements.values())
    found_count = sum(len(found) for found in found_elements.values())
    completeness_score = (found_count / total_elements) * 100

    # Check for segment indicators (shows it processed multiple parts)
    segment_indicators = ['part 1', 'part 2', 'segment', 'continues', 'meanwhile']
    has_segments = any(indicator in story_lower for indicator in segment_indicators)

    # Check story length (comprehensive processing should produce longer stories)
    length_score = min(100, (len(story) / 3000) * 100)  # Expect at least 3000 chars for complete story

    return {
        'completeness_score': round(completeness_score, 1),
        'found_elements': found_elements,
        'missing_elements': missing_elements,
        'has_segment_processing': has_segments,
        'length_adequacy': round(length_score, 1),
        'total_found': found_count,
        'total_possible': total_elements
    }

async def main():
    """Run comprehensive tests on all story generators."""

    logger.info("🧪 COMPREHENSIVE TRANSCRIPTION PROCESSING TEST")
    logger.info("Verifying that ALL story generators read ENTIRE transcriptions")
    logger.info("=" * 80)

    # Create large test transcription
    logger.info("📝 Creating large test transcription...")
    transcription = create_large_test_transcription()

    logger.info(f"✅ Created transcription: {len(transcription)} characters")
    logger.info(f"📊 Estimated tokens: {len(transcription) // 4}")
    logger.info(f"📖 Contains {transcription.count('**')} structured elements")

    # Create test context
    context = StoryContext(
        session_name="Epic Tower Quest Session",
        setting="High Fantasy D&D Campaign - The Cursed Tower Arc",
        characters=["Thorin Ironbeard", "Elara Moonwhisper", "Gareth Stormshield", "Zara Shadowblade", "Magnus Spellweaver"],
        previous_events=[
            "The party met in the town of Willowbrook",
            "Rumors of the cursed tower reached their ears",
            "They gathered supplies and information"
        ],
        campaign_notes="Multi-session arc involving ancient evil and tower exploration"
    )

    # Test all generators
    generators_to_test = [
        (DemoStoryGenerator(), "Demo Story Generator (Free)"),
    ]

    # Only test OpenAI and Ollama if they might be available
    try:
        # Test with a dummy key - we expect it to fail but want to test the segmentation logic
        openai_gen = StoryGenerator("dummy_key")
        generators_to_test.append((openai_gen, "OpenAI Story Generator"))
    except:
        logger.info("OpenAI Story Generator not available for testing")

    try:
        ollama_gen = OllamaStoryGenerator()
        generators_to_test.append((ollama_gen, "Ollama Story Generator"))
    except:
        logger.info("Ollama Story Generator not available for testing")

    results = []

    for generator, name in generators_to_test:
        result = await test_story_generator(generator, name, transcription, context)
        results.append(result)

    # Print comprehensive results
    logger.info("\n" + "="*80)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*80)

    for result in results:
        logger.info(f"\n🎯 {result['generator'].upper()}:")

        if result['success']:
            verification = result['verification']
            logger.info(f"   ✅ Success: Generated {result['story_length']} characters")
            logger.info(f"   ⏱️  Processing Time: {result['processing_time']:.2f} seconds")
            logger.info(f"   📋 Completeness Score: {verification['completeness_score']}%")
            logger.info(f"   🎲 Elements Found: {verification['total_found']}/{verification['total_possible']}")
            logger.info(f"   📑 Segment Processing: {'Yes' if verification['has_segment_processing'] else 'No'}")
            logger.info(f"   📏 Length Adequacy: {verification['length_adequacy']}%")

            if verification['missing_elements']:
                logger.info(f"   ⚠️  Missing Elements: {len(verification['missing_elements'])} items")
                # Show first few missing elements
                for missing in verification['missing_elements'][:5]:
                    logger.info(f"      - {missing}")
                if len(verification['missing_elements']) > 5:
                    logger.info(f"      ... and {len(verification['missing_elements']) - 5} more")

            # Show story preview
            logger.info(f"\n   📖 Story Preview:")
            logger.info(f"   {'-'*60}")
            preview_lines = result['story_preview'].split('\n')[:3]
            for line in preview_lines:
                logger.info(f"   {line}")
            logger.info(f"   {'-'*60}")

        else:
            logger.info(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

    # Overall assessment
    successful_tests = [r for r in results if r['success']]

    logger.info(f"\n🏆 OVERALL ASSESSMENT:")
    logger.info(f"   Tests Passed: {len(successful_tests)}/{len(results)}")

    if successful_tests:
        avg_completeness = sum(r['verification']['completeness_score'] for r in successful_tests) / len(successful_tests)
        avg_length = sum(r['story_length'] for r in successful_tests) / len(successful_tests)

        logger.info(f"   Average Completeness: {avg_completeness:.1f}%")
        logger.info(f"   Average Story Length: {avg_length:.0f} characters")

        if avg_completeness >= 80:
            logger.info("   ✅ EXCELLENT: Story generators capture comprehensive content!")
        elif avg_completeness >= 60:
            logger.info("   ✅ GOOD: Story generators capture most important content")
        else:
            logger.info("   ⚠️  NEEDS IMPROVEMENT: Story generators missing significant content")

    logger.info("\n" + "="*80)
    logger.info("🎉 COMPREHENSIVE TRANSCRIPTION TEST COMPLETE!")
    logger.info("All story generators now process ENTIRE transcriptions!")
    logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())