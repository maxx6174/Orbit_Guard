# Project explanation (simple English)

**The story.** We send a small robot spaceship (a probe) to another planet. It measures things like temperature, air
pressure and radiation and sends them to scientists on Earth by radio. Sometimes the radio link breaks. Normally only
Earth tries to fix it - and Earth is far away and cannot see what is wrong inside the probe.

**Our idea.** Put a small "AI guardian" inside the probe. It is called **ORBIT-GUARD**. When the link breaks, the guardian
looks at the probe's battery, antenna and radio, guesses what is wrong, and tries a fix - for example switching to a
backup antenna mode or saving battery power. At the same time Earth keeps trying its own fixes. Two helpers are better than one.

**While the link is broken** the probe keeps measuring and saves the data. When the link comes back it sends everything it
saved, so scientists do not lose the missing readings.

**Is it real?** No. It is a computer simulation that runs on a laptop. The planet, the probe, the radio and the data are
all pretend ("SIMULATED PLANETARY DATA"). It shows the *idea*; it does not prove it would work in space.

**Is the AI cheating?** The numbers on the comparison page come from running the simulation, not from typing them in.
Sometimes ORBIT-GUARD helps a lot (broken antenna), sometimes not at all (the planet physically blocks the signal) - the
project shows both honestly.

**How the AI decides.** It (1) estimates what is probably wrong, (2) gives each possible fix a score based on how likely it
is to help and how costly it is, (3) tries the best one, (4) checks whether the link came back, and (5) if not, learns that
fix did not work and tries the next best.
