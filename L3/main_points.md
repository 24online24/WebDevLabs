Showcase how JavaScript can be used in the browser. For example:

- Variables, types, functions, arrays, objects
- DOM manipulation: `querySelector`, event listeners
- JSON as a data format

1. Data variables, functions, arrays/objects

- App-level variables like shop name, default category, and config values in script.js.
- Reusable functions for:
  - price formatting (`formatPrice`)
  - category extraction (`getCategories`)
  - filtering (`getFilteredItems`)
  - dynamic card markup (`createMenuCard`)

2. JSON data format + dynamic rendering

- Create menu.json with menu items as an array of objects.
- Replace hardcoded menu cards with JS-rendered cards loaded from `fetch("menu.json")`.
- Rendering now targets `#menu-grid` in index.html.

3. DOM manipulation + event listeners

- Filter controls container in index.html and dynamically render category buttons from JSON categories.
- Implement click listeners for filtering in script.js using `querySelector` and delegated events.
- Navbar theme toggle button and wire it with `addEventListener`.

4. Theme toggle

- Toggle button in index.html.
- Dark theme CSS variable overrides and component styles in style.css.
- Theme preference is persisted with `localStorage` in script.js.

5. Reservation form event + validation

- Form/status hooks in index.html.
- Intercept submit with `preventDefault()`.
- Validation for:
  - guest count range
  - valid date/time
  - future date/time
  - max advance booking window
- Displays success/error feedback message in the DOM via script.js, styled in style.css.
