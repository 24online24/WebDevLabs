// App configuration values (strings and numbers).
const shopName = "Bean & Brew";
const apiBaseUrl = "http://localhost:8000/api";
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
async function setFilter(category) {
  activeCategory = category;
  renderFilterControls(getCategories(menuItems));
  menuGrid.innerHTML = '<p class="menu-status">Loading menu...</p>';

  try {
    const items = await fetchMenuData(activeCategory);
    renderMenu(items);
  } catch (error) {
    menuGrid.innerHTML =
      '<p class="menu-status">Menu unavailable right now. Please refresh and try again.</p>';
    console.error(error);
  }
}

// Event delegation: one click listener handles all filter buttons.
function setupFilterEvents() {
  menuControls.addEventListener("click", async (event) => {
    const button = event.target.closest(".filter-btn");
    if (!button) {
      return;
    }

    const selectedCategory = button.dataset.category;
    await setFilter(selectedCategory);
  });
}

// Shared DOM feedback helper for form validation/result messages.
function showReservationMessage(message, type) {
  reservationStatus.textContent = message;
  reservationStatus.classList.remove("success", "error");
  reservationStatus.classList.add(type);
}

function formatApiErrorDetail(detail) {
  const fieldName = detail.loc?.[detail.loc.length - 1];
  if (!fieldName) {
    return detail.msg;
  }

  const label = fieldName.replaceAll("_", " ");
  return `${label}: ${detail.msg}`;
}

async function getApiErrorMessage(response) {
  try {
    const data = await response.json();

    if (Array.isArray(data.detail)) {
      return data.detail.map(formatApiErrorDetail).join(" ");
    }

    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch (error) {
    console.error(error);
  }

  return "Unable to submit reservation right now. Please try again.";
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
  reservationForm.addEventListener("submit", async (event) => {
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
    const guests = Number(formData.get("guests"));
    const reservationPayload = {
      contact_name: String(customerName).trim(),
      contact_email: String(formData.get("email")).trim(),
      date: reservationDate,
      time: reservationTime,
      guest_count: guests,
      special_requests: String(formData.get("notes")).trim() || null,
    };

    try {
      const response = await fetch(`${apiBaseUrl}/reservations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(reservationPayload),
      });

      if (response.status !== 201) {
        const errorMessage = await getApiErrorMessage(response);
        showReservationMessage(errorMessage, "error");
        return;
      }

      const savedReservation = await response.json();
      showReservationMessage(
        `Thanks, ${customerName}! Reservation #${savedReservation.id} for ${guests} guests at ${shopName} is confirmed for ${reservationDate} at ${reservationTime}.`,
        "success",
      );
      reservationForm.reset();
    } catch (error) {
      showReservationMessage(
        "Unable to reach the reservation service right now. Please try again.",
        "error",
      );
      console.error(error);
    }
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

function buildMenuUrl(category = defaultCategory) {
  const url = new URL(`${apiBaseUrl}/menu`);

  if (category !== defaultCategory) {
    url.searchParams.set("category", category);
  }

  return url.toString();
}

async function fetchMenuData(category = defaultCategory) {
  const response = await fetch(buildMenuUrl(category));
  if (!response.ok) {
    throw new Error("Unable to fetch menu data.");
  }

  const data = await response.json();
  if (!Array.isArray(data)) {
    throw new Error("Menu data format is invalid.");
  }

  return data;
}

// JSON data loading with fetch + async/await.
async function loadMenuData() {
  try {
    menuItems = await fetchMenuData();
    const categories = getCategories(menuItems);

    renderFilterControls(categories);
    renderMenu(menuItems);
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
