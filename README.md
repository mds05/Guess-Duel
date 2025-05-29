# Guess Duel

**Guess Duel** is a two-player, turn-based number guessing game built using Python and PyGame, developed as part of the [Amazon Q CLI Game Challenge](https://community.aws/).

One player (the Attacker) sets a secret number, while the other player (the Defender) must guess it correctly to survive. Each incorrect guess reduces the Defender’s HP. The game offers multiple difficulty levels and a progressive level system within each category, making it both challenging and rewarding.

---

## Features

- Three difficulty categories: Easy, Medium, and Hard
- Five levels per category, increasing in difficulty with each level
- Hint system introduced in levels 3, 4, and 5
- Defender HP system that adds pressure to each guess
- Sound effects and transition animations for an interactive experience
- Resizable game window with dynamic UI adjustment
- Champion screen displayed upon successful completion of all levels in a category

## Gameplay Overview
The Attacker secretly selects a number based on the current level. The Defender attempts to guess the number within a limited number of attempts. Each incorrect guess reduces the Defender's HP. In levels 3 to 5, hints are provided after two wrong guesses. If the Defender successfully guesses the number, they move on to the next level. After completing all five levels in a category, the player is declared the Champion of that category.

## Screenshots

## Built With
-Python 3

-PyGame

-Amazon Q CLI

## Acknowledgments
Thanks to Amazon Q CLI for streamlining the development experience and helping bring this game to life. Much of the game's logic, structure, and polish were built through iterative prompting and refinement using Q CLI.
