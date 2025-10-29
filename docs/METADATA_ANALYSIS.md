# Steam Review Metadata Analysis

## Currently Available Data Fields

### Top-Level Metadata (Our custom wrapper)

```json
{
  "appid": 570,
  "language": "all",
  "review_type": "all",
  "purchase_type": "all",
  "total_reviews_collected": 200,
  "pages_fetched": 2,
  "date_collected_utc": "2025-10-16T04:36:49.055851"
}
```

### Query Summary (From Steam API)

```json
{
  "num_reviews": 100 // Reviews per page
}
```

### Per-Review Data (From Steam API)

#### Review Identification

- **recommendationid**: Unique ID for the review
- **language**: Language code (e.g., "english", "schinese", "russian")

#### Author Information

- **steamid**: User's Steam ID
- **num_games_owned**: Number of games in library (0 if private)
- **num_reviews**: Total reviews written by this user
- **playtime_forever**: Total playtime in minutes
- **playtime_last_two_weeks**: Recent playtime in minutes
- **playtime_at_review**: Playtime when review was written (minutes)
- **last_played**: Unix timestamp of last play session

#### Review Content

- **review**: Full review text
- **voted_up**: Boolean - true=positive, false=negative
- **timestamp_created**: Unix timestamp when review was created
- **timestamp_updated**: Unix timestamp when review was last updated

#### Community Engagement

- **votes_up**: Number of "helpful" votes
- **votes_funny**: Number of "funny" votes
- **weighted_vote_score**: Steam's internal vote score (string decimal)
- **comment_count**: Number of comments on the review

#### Purchase & Platform Info

- **steam_purchase**: Boolean - bought on Steam vs external key
- **received_for_free**: Boolean - got game for free
- **written_during_early_access**: Boolean - review from EA period
- **primarily_steam_deck**: Boolean - mainly played on Steam Deck

## What We're Currently Showing

### In Extreme Reviews Tab

#### Data Info Panel

✅ Game title
✅ App ID
✅ Total reviews analyzed
✅ Positive/negative counts (overall)
✅ Date fetched

#### Per-Language Info

✅ Language name
✅ Total reviews for language
✅ Positive/negative counts per language

#### Review Cards

✅ Positive/Negative indicator
✅ Winner badge
✅ Playtime @ review (minutes → hours)
✅ Total playtime (minutes → hours)
✅ Games owned
✅ Review text
✅ Date posted
✅ Helpful votes
✅ Funny votes

## What We're NOT Showing (Available but Unused)

### Author Insights

❌ **num_reviews**: How many reviews this user has written

- Use case: Identify prolific reviewers
- Display: "Reviewer: Wrote X reviews"

❌ **playtime_last_two_weeks**: Recent activity

- Use case: Show if user is still active
- Display: "Still playing: X hrs in last 2 weeks" or "Last active: X days ago"

❌ **last_played**: When they last played

- Use case: Review relevance - is it from active player?
- Display: "Last played: YYYY-MM-DD" or "X days ago"

### Review Metadata

❌ **timestamp_updated**: If review was edited

- Use case: Show if review is original or edited
- Display: "Edited on: YYYY-MM-DD" (if different from created)

❌ **weighted_vote_score**: Steam's quality metric

- Use case: Show review quality/trustworthiness
- Display: "Steam Score: 0.XX" or star rating

❌ **comment_count**: Community discussion

- Use case: Engagement level
- Display: "💬 X comments"

### Purchase Context

❌ **steam_purchase**: Purchase source

- Use case: Distinguish Steam buyers vs key activators
- Display: "🛒 Steam Purchase" or "🔑 Key Activated"

❌ **received_for_free**: Free game indicator

- Use case: Context for review (free = different expectations)
- Display: "🎁 Received for free"

❌ **written_during_early_access**: EA context

- Use case: Historical context - early adopter
- Display: "⚠️ Written during Early Access"

❌ **primarily_steam_deck**: Platform indicator

- Use case: Steam Deck specific insights
- Display: "🎮 Steam Deck Player"

### Calculated Fields (We could add)

❌ **Review age**: Days since posted

- Calculation: now - timestamp_created
- Use case: Recent vs old reviews
- Display: "X days/months/years ago"

❌ **Review freshness**: Is review still relevant?

- Calculation: Compare timestamp_created to last_played
- Use case: Abandoned reviews vs active player reviews
- Display: "Active player" vs "Stopped playing after review"

❌ **Playtime growth**: How much played since review

- Calculation: playtime_forever - playtime_at_review
- Use case: Did they keep playing after review?
- Display: "+X hrs since review" or "Percentage growth"

❌ **Review intensity**: Review length per hour played

- Calculation: len(review) / (playtime_at_review / 60)
- Use case: Passionate vs casual reviewers
- Display: Could categorize as detailed/brief

## Enhancement Suggestions

### Priority 1: High Value, Easy Implementation

1. **Comment Count** (`comment_count`)

   - Where: Review card footer
   - Display: `💬 Comments: {comment_count}`
   - Why: Shows engagement, popular reviews

2. **Playtime After Review** (calculated)

   - Where: Stats line in review card
   - Display: `📈 Played {delta} hrs more after review`
   - Why: Shows commitment - did they keep playing?

3. **Steam Purchase Indicator** (`steam_purchase`)

   - Where: Review card header or footer
   - Display: Small icon 🛒 or 🔑
   - Why: Context for review validity

4. **Review Age** (calculated)
   - Where: Footer next to date
   - Display: `Posted: {date} ({X} months ago)`
   - Why: Relevance context

### Priority 2: Medium Value, Moderate Effort

5. **Active Player Status** (`playtime_last_two_weeks` + `last_played`)

   - Where: Author stats line
   - Display: `🎮 Still playing (X hrs recently)` or `⏸️ Last played {date}`
   - Why: Review relevance

6. **Reviewer Profile** (`num_reviews`)

   - Where: Author stats
   - Display: `✍️ Written {num_reviews} reviews`
   - Why: Identify expert/prolific reviewers

7. **Steam Deck Badge** (`primarily_steam_deck`)

   - Where: Card header
   - Display: `🎮 Steam Deck Review` (if true)
   - Why: Platform-specific insights

8. **Weighted Vote Score** (`weighted_vote_score`)
   - Where: Footer with votes
   - Display: Convert to star rating (1-5) or percentage
   - Why: Steam's quality metric

### Priority 3: Advanced Features

9. **Review Edit Indicator** (compare `timestamp_created` vs `timestamp_updated`)

   - Where: Footer
   - Display: `✏️ Edited {X} days after posting` (if different)
   - Why: Transparency

10. **Early Access Badge** (`written_during_early_access`)

    - Where: Card header
    - Display: `⚠️ Early Access Review`
    - Why: Historical context

11. **Free Game Indicator** (`received_for_free`)
    - Where: Purchase context area
    - Display: `🎁 Free`
    - Why: Bias awareness

### Priority 4: Analytics/Filtering

12. **Filter by Active Players Only**

    - Condition: `playtime_last_two_weeks > 0`
    - Why: Most relevant reviews

13. **Filter by Steam Purchases Only**

    - Condition: `steam_purchase == true`
    - Why: More invested players

14. **Sort by Engagement**

    - Metric: `votes_up + votes_funny + comment_count`
    - Why: Find most discussed reviews

15. **Filter by Review Quality**
    - Metric: `weighted_vote_score > threshold`
    - Why: High-quality reviews only

## Recommended Implementation Plan

### Phase 1: Quick Wins (30 mins)

Add to review cards:

- Comment count
- Playtime growth since review
- Review age

### Phase 2: Context Indicators (1 hour)

Add badges/icons:

- Steam purchase vs key
- Steam Deck player
- Still active indicator

### Phase 3: Advanced Stats (2 hours)

Add detailed metrics:

- Reviewer profile (num_reviews)
- Vote quality score visualization
- Edit history
- Early access badge

### Phase 4: Filtering & Sorting (3 hours)

Add UI controls:

- Filter by activity status
- Filter by purchase type
- Sort by engagement/quality
- Date range filtering

## Data Quality Notes

### Known Issues

1. **num_games_owned = 0**: User has private profile
2. **playtime_last_two_weeks = 0**: Not played recently OR private
3. **weighted_vote_score**: String that needs float conversion
4. **last_played**: Can be in future due to timezone/system clock issues

### Missing Data Handling

- Use `get()` with defaults for all fields
- Display "Private" or "N/A" for 0 values where appropriate
- Graceful degradation if fields missing

## Sample Enhanced Display

```
🏆 👍 Positive Review - WINNER!
⏱️ Playtime @ Review: 1,028.7 hrs 🌟  |  📊 Total Playtime: 1,568.0 hrs  |  🎮 Games: 84
📈 Played 539.3 hrs more after review  |  ✍️ Reviewer has written 10 reviews
🛒 Steam Purchase  |  🎮 Still active (14.6 hrs recently)

[Review text...]

📅 Posted: 2022-11-01 (3 years ago)  |  👍 Helpful: 1,518  |  😄 Funny: 645  |  💬 Comments: 70
⭐ Quality Score: 98.6%
```

This would give users MUCH more context about each review!
