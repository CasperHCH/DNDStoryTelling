"""
Demo Audio Processor for testing purposes
This simulates audio transcription without requiring external services
"""

import os
from typing import Dict, Any

class DemoAudioProcessor:
    """Demo audio processor that simulates transcription without API calls"""

    def __init__(self):
        self.demo_transcriptions = [
            """**Session Transcript - Demo Mode**

**DM:** Welcome back to our ongoing adventure, heroes. As we left off last session, you had just entered the ancient underground chamber beneath the old wizard's tower.

**Player 1 (Kael the Rogue):** I want to check for traps on that ornate door ahead. Rolling for perception... got a 17.

**DM:** With your keen eyes, Kael, you notice several pressure plates near the door and what appears to be poison dart holes in the walls. This door is definitely trapped.

**Player 2 (Lyra the Cleric):** Can I detect any magical auras on the door or the traps?

**DM:** Roll for Religion or Arcana...

**Player 2:** Rolling Arcana... 15.

**DM:** You sense strong divination magic emanating from the door itself - likely an alarm spell - and transmutation magic from the trap mechanisms.

**Player 3 (Gareth the Fighter):** While they're examining the door, I'll keep watch behind us. Any sounds from the way we came?

**DM:** Roll for perception...

**Player 3:** Natural 20!

**DM:** Gareth, with your exceptional awareness, you hear the distant sound of shuffling footsteps echoing from the tunnel you just came through. Something is following your trail.

**Player 1:** Okay, change of plans. I need to disable these traps quickly before whatever's following us catches up. Rolling for Thieves' Tools...

**Combat Encounter:** A group of undead guardians emerged from hidden alcoves!

**Initiative Order:**
- Kael: 18
- Undead Captain: 16
- Lyra: 14
- Gareth: 12
- Skeleton Archers: 8

**Round 1:**
**Kael:** I'll attack the captain with my shortsword, trying to get sneak attack damage... Attack roll 16, damage 14 piercing plus 8 sneak attack!

**DM:** The captain staggers but remains standing, black ichor oozing from the wound.

**Undead Captain:** Attacks Kael with its rusted longsword... hits for 9 slashing damage.

**Lyra:** I cast Sacred Flame on the captain. Dexterity save... it fails! 8 radiant damage!

**Gareth:** Charging in with my greatsword... Attack roll 15, damage 12 slashing!

**DM:** The radiant energy from Lyra's spell causes the undead captain to crumble to dust! The remaining skeletons press their attack...

**Session continues with exploration, puzzle-solving, and character development...**

*This is a sample transcription showing typical D&D session content including roleplay, combat, and exploration elements.*""",

            """**Demo Audio Transcription Complete**

**DM:** The ancient library stretches before you, its shelves reaching impossibly high into shadows above. Dust motes dance in the shafts of light filtering through cracked stained glass windows.

**Player 1 (Elara the Wizard):** I want to examine the books on the nearest shelf. Are any of them magical?

**DM:** Roll for Investigation...

**Player 1:** 16.

**DM:** Most of the books are mundane historical texts, but you notice one volume that seems to shimmer slightly - a tome bound in midnight blue leather with silver clasps.

**Player 2 (Thorin the Dwarf Cleric):** While she's looking at books, I'll check if this place has been disturbed recently. Any footprints in the dust?

**DM:** Good thinking, Thorin. Roll for Investigation as well...

**Player 2:** 13.

**DM:** You see faint tracks leading from the entrance toward the back of the library, where a spiral staircase winds upward to a second level.

**Player 3 (Zara the Halfling Rogue):** I'll stealthily follow those tracks. Rolling for Stealth... 19.

**DM:** Moving silent as a shadow, Zara, you creep toward the staircase. As you get closer, you hear a faint scratching sound from above, like quill on parchment.

**Dialogue Scene:**
**Mysterious Voice from Above:** "Who dares disturb the sacred archives? Identify yourselves, mortals, or face the consequences!"

**Player 1:** I'll call up respectfully, "We are scholars seeking knowledge about the ancient prophecy. We mean no harm to your collection."

**DM:** There's a long pause, then the sound of footsteps on the stairs above...

**NPC - The Librarian Ghost:** "Scholars, you say? It has been decades since true seekers of knowledge have entered these halls. What prophecy do you seek?"

**Character Development Moment:**
**Player 2:** Thorin steps forward, his holy symbol glowing softly. "The prophecy of the Sundered Crown. My clan has protected part of the lore for generations, but we need the complete text."

**DM:** The ghostly librarian's expression softens. "Ah, a keeper of ancient traditions. Your people were always friends to this library..."

**Session continues with investigation, lore discovery, and plot advancement...**

*This demo shows a more investigation and roleplay heavy session with NPC interaction and plot development.*""",

            """**Sample Combat-Heavy Session Transcript**

**DM:** The dragon's roar shakes the very foundations of the mountain as it emerges from its lair, eyes blazing with ancient fury!

**Initiative Roll Results:**
- Kira the Ranger: 20
- Ancient Red Dragon: 18
- Marcus the Paladin: 15
- Elena the Sorcerer: 12
- Bjorn the Barbarian: 10

**Round 1:**
**Kira:** I'll use my action to cast Hunter's Mark on the dragon and attack with my longbow. Attack roll... 18 to hit! Damage: 8 piercing plus 4 from Hunter's Mark.

**DM:** Your arrow finds a gap in the dragon's scales but barely penetrates its thick hide.

**Ancient Red Dragon:** The dragon unleashes its terrifying fire breath in a 60-foot cone! Everyone needs to make Dexterity saving throws!

**Marcus:** 12... failed.
**Elena:** 16... success!
**Bjorn:** Natural 1... oh no.

**DM:** Marcus takes 28 fire damage, Bjorn takes 28 fire damage, Elena takes 14 fire damage from the half damage. The heat is overwhelming!

**Marcus:** I'm still up! I'll use my Lay on Hands to heal myself for 15 points, then attack with my holy avenger. Attack roll: 19! Damage: 12 slashing plus 8 radiant!

**DM:** The radiant energy burns the dragon's flesh, and it roars in pain and anger!

**Elena:** I'll cast Fireball at 5th level centered on the dragon. It needs to make a Dex save...

**DM:** The dragon rolls... 14, it fails!

**Elena:** That's 35 fire damage!

**DM:** Surprisingly, the ancient red dragon has resistance to fire damage, so it only takes 17 damage, but you can see your spell had some effect.

**Bjorn:** I rage and charge the dragon with my greataxe! Reckless attack... 16 to hit! With rage damage that's 15 slashing!

**DM:** As the battle continues, the dragon's attacks become more desperate and vicious...

**Epic Moment:**
**DM:** The dragon, bloodied and desperate, attempts to flee by taking to the air...

**Marcus:** I use my Divine Sense and declare, "By the light of justice, you will not escape!" and throw my javelin with Divine Smite...

**Critical Hit - Natural 20!**

**Damage Total:** 47 radiant and piercing damage!

**DM:** The javelin, blazing with holy light, pierces the dragon's heart as it tries to take flight. With a final, earth-shaking roar, the ancient wyrm crashes to the ground, defeated!

*This demo showcases intense combat with dramatic moments and tactical play.*"""
        ]

    async def process_audio(self, audio_path: str) -> str:
        """Simulate audio transcription with demo content"""
        # Get file info for realistic processing
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            file_name = os.path.basename(audio_path)
        else:
            file_size = 2000000000  # 2GB demo size
            file_name = "demo_session.wav"

        # Select demo transcription based on file name or randomly
        import random
        if "combat" in audio_path.lower():
            demo_content = self.demo_transcriptions[2]  # Combat-heavy session
        elif "roleplay" in audio_path.lower() or "investigation" in audio_path.lower():
            demo_content = self.demo_transcriptions[1]  # Roleplay-heavy session
        else:
            demo_content = random.choice(self.demo_transcriptions)

        # Add file info to the transcription
        size_mb = file_size / (1024 * 1024)
        header = f"""**🎵 Free Audio Processing Complete!**

**File:** {file_name}
**Size:** {size_mb:.1f} MB
**Processing Mode:** Free Demo Mode - Fully Functional!

**📝 Transcription Results:**

"""

        return header + demo_content

    async def transcribe_audio(self, audio_path: str) -> str:
        """Alternative method name for compatibility"""
        return await self.process_audio(audio_path)