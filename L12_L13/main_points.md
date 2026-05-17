Finalize the project by extending the current Svelte + FastAPI application into a role-based business management system with both public-facing and staff-facing workflows.

1. Authentication & Authorization

- Add staff authentication so the project supports secure login/logout flows instead of a fully public management UI.
- Introduce at least two protected roles:
  - `manager`: can review customer submissions, confirm or cancel bookings, update operational details, and track day-to-day activity.
  - `admin`: has all manager permissions plus content management and staff account management.
- Store passwords securely with hashing, never in plain text, and enforce permissions in FastAPI dependencies instead of relying on frontend checks alone.

2. Backend Expansion

- Extend the database with a `User` model and any extra workflow fields needed for staff operations, such as `status`, `notes`, or `updated_at`.
- Keep public endpoints for browsing offerings and creating customer submissions, but add protected endpoints for staff-only actions.
- Build API routes for authentication, current-user lookup, booking or request management, and catalog CRUD operations.

3. Frontend Architecture

- Evolve the current single public-facing Svelte page into a small multi-view application with clear separation between customer and staff features.
- Break the UI into reusable components such as `LoginForm.svelte`, `PublicCatalog.svelte`, `BookingForm.svelte`, `BookingTable.svelte`, and `CatalogEditor.svelte`.
- Use Svelte state, bindings, and conditional rendering to show different screens and actions based on the signed-in user's role.

4. Catalog Administration

- Allow admins to add, edit, delete, and feature customer-facing items from a protected dashboard.
- Validate fields like name, category, price, description, and image or media URL on both the frontend and backend.
- Ensure updates made by admins are reflected immediately in the public catalog without manual DOM manipulation.

5. Booking and Operations Management

- Let managers and admins view all customer bookings, reservations, or requests in a staff dashboard rather than only accepting submissions.
- Add workflow states such as `pending`, `confirmed`, `completed`, and `cancelled`.
- Support staff actions like filtering records by date or status, editing details, adding internal notes, and cancelling or confirming requests.

6. User Experience, Security, and Testing

- Provide clear loading, success, and error states for login, catalog updates, and booking-related actions.
- Protect private routes and API endpoints so unauthorized users cannot access staff-only tools.
- Expand automated tests to cover authentication, role-based permissions, catalog CRUD behavior, and workflow status updates.
