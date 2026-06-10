# Interactive Cartographic Quiz Game Implementation Plan

## Overview
Transform the cartographic quiz from a non-functional prototype into a fully working interactive game with persistent score tracking, multiple guesses per session, and visual feedback.

## Requirements Summary
- **Pure gameplay**: Map markers only, no spoilers
- **Free-text answers**: Flexible name matching with normalization
- **Score display**: "Correct: X | Streak: Y" format
- **Multiple guesses**: No button disable after correct answer
- **SessionStorage persistence**: Survives page navigation in session, clears on refresh
- **Visual feedback**: Flash animation when streak resets to 0
- **Reset button**: Secondary muted gray style
- **Score init**: Updates immediately on page load from sessionStorage

## Implementation Details

### Phase 1: Update `src/cartographic_quiz/map_renderer.py`

**Location**: Lines 75-123 (quiz_html f-string)

**Changes**:

1. **Add CSS Animation Block** (before HTML):
   - Define `@keyframes streak-flash` animation
   - Red highlight pulse effect: rgba(220, 53, 69, 0.3)
   - Duration: 600ms ease-out
   - Class: `.streak-flash` for applying animation

2. **Update HTML Structure**:
   - Keep existing quiz panel and input/button structure
   - Add after `quiz-result` div:
     ```html
     <div id="quiz-stats" style="margin-top: 6px; font-size: 12px; color: #666; font-weight: 600;">
       Correct: <span id="correct-count">0</span> | Streak: <span id="streak-count">0</span>
     </div>
     ```
   - Add Reset Score button (secondary style):
     ```html
     <button id="quiz-reset" style="width: 100%; padding: 6px 8px; border: 0; border-radius: 6px; background: #e0e0e0; color: #555; font-weight: 500; font-size: 12px; cursor: pointer; margin-top: 6px;">Reset Score</button>
     ```

3. **JavaScript Logic Changes**:

   **Initialization Function** (`initializeScore`):
   - Read correctCount and streak from sessionStorage on page load
   - Set default values to "0" if not found
   - Update DOM elements immediately

   **Check Function** (answer validation):
   - On **correct answer**:
     - Increment correctCount and streak in sessionStorage
     - Update DOM elements
     - Show "Correct!" in green (#1b5e20)
     - Clear input field
     - Keep button enabled (remove disabled property)
     - Refocus input field for next guess
   
   - On **wrong answer**:
     - Reset streak to 0 in sessionStorage
     - Update DOM element
     - Show "Not quite. Try again." in red (#b71c1c)
     - Add `streak-flash` class to streak counter
     - Remove class after 600ms animation completes

   **Reset Function** (`resetScore`):
   - Remove correctCount and streak from sessionStorage
   - Reset UI to "0" for both counters
   - Clear result message
   - Clear input field
   - Refocus input field

   **Event Listeners**:
   - Submit button click → check()
   - Input Enter key → check()
   - Reset button click → resetScore()
   - Page load → initializeScore()

4. **Person Name Embedding**:
   - Ensure `{person_name!r}` produces valid JavaScript string
   - No escaping issues should occur with proper f-string handling

### Phase 2: Create `tests/test_map_renderer.py`

**Purpose**: Comprehensive test coverage for quiz functionality

**Test Categories**:

1. **Answer Normalization Tests**:
   - Test basic case insensitivity: "napoleon" vs "Napoleon"
   - Test multi-word names: "mary queen of scots" vs "Mary Queen of Scots"
   - Test accent removal: "josé martí" normalizes correctly
   - Test hyphenated names: "jean-paul sartre" vs "jeanpaul sartre"
   - Test apostrophes: "d'artagnan" vs "dartagnan"
   - Test whitespace collapse: multiple spaces → single space
   - Test punctuation removal: special characters stripped
   - Test edge cases: empty string, numbers, special characters

2. **Quiz Panel HTML Generation Tests**:
   - Verify quiz panel div is generated with correct ID
   - Verify input field exists with ID "quiz-input"
   - Verify submit button exists with ID "quiz-submit"
   - Verify reset button exists with ID "quiz-reset"
   - Verify stats display exists with IDs "correct-count" and "streak-count"
   - Verify initial counter text is "0"
   - Verify result message div exists with ID "quiz-result"

3. **SessionStorage Script Injection Tests**:
   - Verify inline script is present in generated HTML
   - Verify person_name variable is properly set
   - Verify normalize function is defined
   - Verify event listeners are attached to correct elements
   - Verify animation CSS is injected
   - Verify sessionStorage keys match expected names ("correctCount", "streak")

4. **Integration Tests** (if using Playwright/E2E):
   - Generate map for known person (Napoleon)
   - Verify HTML renders without errors
   - Test button click functionality
   - Test keyboard Enter key submission
   - Test answer checking logic
   - Test score increment
   - Test streak reset with animation
   - Test reset button functionality

### Phase 3: Testing & Validation

**Unit Tests**:
```bash
uv run pytest tests/test_map_renderer.py -v
```
- All tests must pass
- Coverage should include all normalization edge cases
- Verify HTML structure and injection

**Manual E2E Testing**:
```bash
uv run cartographic-quiz Napoleon -o test_map.html
# Open test_map.html in browser
```

**Test Scenarios**:
1. ✓ Button responds to click and Enter key
2. ✓ Correct guess increments both counters
3. ✓ Wrong guess resets streak to 0 with flash animation
4. ✓ Score persists when navigating within session
5. ✓ Score resets to 0/0 on page refresh
6. ✓ Reset button clears all scores and input
7. ✓ Multiple consecutive correct guesses increment properly
8. ✓ Streak breaks on wrong answer at any point
9. ✓ Answer matching is case-insensitive and punctuation-agnostic

## Files Modified/Created

| File | Action | Details |
|------|--------|---------|
| `src/cartographic_quiz/map_renderer.py` | Modify | Replace quiz_html block (lines 75-123) |
| `tests/test_map_renderer.py` | Create | New comprehensive test file |

## Implementation Order

1. Modify `map_renderer.py` with complete quiz implementation
2. Create `tests/test_map_renderer.py` with test suite
3. Run unit tests: `uv run pytest tests/test_map_renderer.py -v`
4. Manual testing with sample historical figure
5. Verify all game mechanics and animations work correctly

## Success Criteria

- ✓ All unit tests pass
- ✓ Manual E2E testing confirms all features work
- ✓ Score tracking persists during session
- ✓ Score resets on page refresh
- ✓ Flash animation visible on streak reset
- ✓ Button responds to both click and Enter key
- ✓ Multiple guesses work without button disable
- ✓ Reset button clears all state
- ✓ Answer normalization handles edge cases (accents, hyphens, apostrophes)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| JavaScript timing issue preventing execution | Add defensive null checks and error logging |
| Person name escaping issue in f-string | Use !r format specifier for safe quoting |
| SessionStorage not persisting | Test across page navigations and browser tabs |
| Animation not visible | Use contrasting color and adequate duration |
| DOM elements not found | Verify all IDs match between HTML and JavaScript |

## Notes

- Answer normalization logic (lines 86-90) is already solid and shouldn't need changes
- The existing JavaScript structure (IIFE) is good for encapsulation
- SessionStorage is appropriate for session-scoped scoring (not persisting across browser close)
- CSS animation is injected via `<style>` tag within quiz_html
- All event listeners use defensive programming (null checks, safe element access)
