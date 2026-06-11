# Difficulty Criteria for Name Pools

This project uses three curated people pools: `easy`, `medium`, and `hard`.
The core goal is quizability from **birth/death dates + places** as map clues.

## Easy Criteria

A person belongs in `people_easy.txt` if they satisfy all of these in practice:

- **Globally well known:** recognizable to a broad audience across regions.
- **Strong map/date signal:** birth/death locations and/or years are commonly associated with them.
- **Distinctive clue combo:** a typical player can make a high-confidence guess from map + date clues.
- **Not too confusable:** less likely to be mixed up with many similarly famous contemporaries from the same places.

Examples of strong easy signals:

- Iconic death place (for example, James Cook in Hawaii).
- Highly recognizable place pairing (for example, birthplace/deathplace pattern that is widely taught).
- Very distinctive era + place combination that narrows to one famous figure.

## Medium Criteria

Place in `people_medium.txt` when at least one is true:

- Person is moderately known but not universally recognized.
- Birth/death map clues are weaker, generic, or less popularly remembered.
- Multiple plausible famous guesses fit the same clue pattern.

## Hard Criteria

Place in `people_hard.txt` when both are generally true:

- Person is relatively obscure for general audiences.
- Birth/death places/dates are not widely known or are weak as identifying clues.

## Curation Rules

- Keep one name per line.
- Avoid cross-list duplicates.
- Prefer stable historical figures with complete birth/death data.
- Reclassify names over time based on real quiz performance (if tracked).
