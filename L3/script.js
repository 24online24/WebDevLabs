// App configuration values (strings and numbers).
const shopName = "Bean & Brew";
const menuDataUrl = "menu.json";
const defaultCategory = "All";
const maxAdvanceDays = 60;

// Mutable state used by the UI.
let menuItems = [];
let activeCategory = defaultCategory;

// DOM references with querySelector so we can update the page with JS.
const menuGrid = document.querySelector("#menu-grid");
const menuControls = document.querySelector("#menu-controls");
const reservationForm = document.querySelector("#reservation-form");
const reservationStatus = document.querySelector("#reservation-status");
const themeToggleButton = document.querySelector("#theme-toggle");
const logo = document.querySelector(".logo");

// Function example: transform raw number data into display text.
function formatPrice(price) {
  return `$${price.toFixed(2)}`;
}

// Array + object practice: pull the category field from each menu object,
// deduplicate with Set, then prepend the "All" category.
function getCategories(items) {
  const uniqueCategories = [...new Set(items.map((item) => item.category))];
  return [defaultCategory, ...uniqueCategories];
}

// Filter logic for category buttons.
function getFilteredItems(items, category) {
  if (category === defaultCategory) {
    return items;
  }

  return items.filter((item) => item.category === category);
}

// Template literal builds one card from a single menu object.
function createMenuCard(item) {
  return `
    <article class="menu-card">
      <img src="${item.image}" alt="${item.alt}" loading="lazy" />
      <div class="menu-card-body">
        <h3>${item.name}</h3>
        <p>${item.description}</p>
        <span class="price">${formatPrice(item.price)}</span>
      </div>
    </article>
  `;
}

// Render step: convert an array of objects into HTML.
function renderMenu(items) {
  if (items.length === 0) {
    menuGrid.innerHTML =
      '<p class="menu-status">No items found for this category.</p>';
    return;
  }

  const cardsMarkup = items.map(createMenuCard).join("");
  menuGrid.innerHTML = cardsMarkup;
}

// Build filter buttons dynamically from current data.
function renderFilterControls(categories) {
  const buttonsMarkup = categories
    .map((category) => {
      const isActive = category === activeCategory;
      return `
        <button
          type="button"
          class="filter-btn ${isActive ? "active" : ""}"
          data-category="${category}"
        >
          ${category}
        </button>
      `;
    })
    .join("");

  menuControls.innerHTML = buttonsMarkup;
}

// Single source of truth for changing active filter + rerendering UI.
function setFilter(category) {
  activeCategory = category;
  renderFilterControls(getCategories(menuItems));
  renderMenu(getFilteredItems(menuItems, activeCategory));
}

// Event delegation: one click listener handles all filter buttons.
function setupFilterEvents() {
  menuControls.addEventListener("click", (event) => {
    const button = event.target.closest(".filter-btn");
    if (!button) {
      return;
    }

    const selectedCategory = button.dataset.category;
    setFilter(selectedCategory);
  });
}

// Shared DOM feedback helper for form validation/result messages.
function showReservationMessage(message, type) {
  reservationStatus.textContent = message;
  reservationStatus.classList.remove("success", "error");
  reservationStatus.classList.add(type);
}

// Validation function returns an error string or empty string when valid.
function validateReservation(formData) {
  const guestCount = Number(formData.get("guests"));
  const reservationDateValue = formData.get("date");
  const reservationTimeValue = formData.get("time");

  if (!Number.isInteger(guestCount) || guestCount < 1 || guestCount > 20) {
    return "Guests must be a whole number between 1 and 20.";
  }

  const reservationDateTime = new Date(
    `${reservationDateValue}T${reservationTimeValue}`,
  );

  if (Number.isNaN(reservationDateTime.getTime())) {
    return "Please choose a valid reservation date and time.";
  }

  const now = new Date();
  if (reservationDateTime < now) {
    return "Reservation date/time must be in the future.";
  }

  const maxDate = new Date();
  maxDate.setDate(maxDate.getDate() + maxAdvanceDays);
  if (reservationDateTime > maxDate) {
    return `Reservations can only be made up to ${maxAdvanceDays} days in advance.`;
  }

  return "";
}

// Submit event: prevent default form post, validate, then show feedback.
function setupReservationForm() {
  reservationForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const formData = new FormData(reservationForm);
    const validationError = validateReservation(formData);

    if (validationError) {
      showReservationMessage(validationError, "error");
      return;
    }

    const customerName = formData.get("name");
    const reservationDate = formData.get("date");
    const reservationTime = formData.get("time");
    const guests = formData.get("guests");

    showReservationMessage(
      `Thanks, ${customerName}! Your table for ${guests} at ${shopName} is requested for ${reservationDate} at ${reservationTime}.`,
      "success",
    );

    reservationForm.reset();
  });
}

// Toggle theme class on the body and persist the user's preference.
function setupThemeToggle() {
  const savedTheme = localStorage.getItem("themePreference");
  if (savedTheme === "dark") {
    document.body.classList.add("dark-theme");
  }

  themeToggleButton.addEventListener("click", () => {
    document.body.classList.toggle("dark-theme");
    const theme = document.body.classList.contains("dark-theme")
      ? "dark"
      : "light";
    localStorage.setItem("themePreference", theme);
  });
}

// JSON data loading with fetch + async/await.
async function loadMenuData() {
  try {
    const response = await fetch(menuDataUrl);
    if (!response.ok) {
      throw new Error("Unable to fetch menu data.");
    }

    const data = await response.json();
    if (!Array.isArray(data)) {
      throw new Error("Menu data format is invalid.");
    }

    menuItems = data;
    const categories = getCategories(menuItems);

    renderFilterControls(categories);
    renderMenu(getFilteredItems(menuItems, activeCategory));
  } catch (error) {
    menuGrid.innerHTML =
      '<p class="menu-status">Menu unavailable right now. Please refresh and try again.</p>';
    console.error(error);
  }
}

// Uses variables to keep branding values consistent across the page.
function updateBranding() {
  document.title = `${shopName} — Coffee Shop`;
  logo.textContent = shopName;
}

// App startup sequence.
function initializeApp() {
  updateBranding();
  setupThemeToggle();
  setupFilterEvents();
  setupReservationForm();
  loadMenuData();
}

initializeApp();
