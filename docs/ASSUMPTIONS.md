# Assumptions, limitations and future work

## Assumptions (all configurable or editable)

- Grid emission factor defaults to 0.82 kg CO2e per kWh. This is a starting value; **check the
  latest official CEA figure** and set `WATTWISE_EMISSION_FACTOR` before presenting.
- Transport factor defaults to 0.17 kg CO2e per km (assumed average petrol car).
- Solar defaults: 5.0 peak sun hours per day, performance ratio 0.78, 10 m2 of roof per kW,
  Rs 60,000 per kW installed, 30 days per month. These are placeholders. The cost figure in
  particular must be replaced with real quotes. Users can change all four in the UI.
- The recommendation threshold of 100 kWh per person per month is a rule of thumb for this
  prototype, not an official benchmark.
- One reading per user per month. Saving the same month again updates it.
- "Today" for missions is the server's date.

## What is deliberately not done

- No live consumption measurement, appliance detection or grid alerts. All data is user-entered.
- No subsidy values, scheme terms or vendor names. The solar page links to official portals so
  users can check them directly.
- No AI output. The AI Energy Coach is not connected, and the UI says so.
- Resource links: only the home pages of a few official bodies are included. **Please open each link
  once before the demo** in case a site has moved.

## Limitations

- **No login.** Profiles are selected from a list, so anyone using the app can switch profiles. This
  is fine for a demo, not for real users. If login is added, use hashed passwords (for example
  Werkzeug `generate_password_hash`) and server-side sessions.
- The browser remembers the last selected profile in `localStorage` (a convenience only; all data
  lives in SQLite).
- Leaderboard names are free text and not unique.
- Development server only; not hardened for production deployment.
- The frontend has no automated tests (backend logic and API are covered).
- Solar location is echoed back only. No weather or irradiance data is used.
- Recharts 2.x is used; a newer major version exists.

## AI Energy Coach: how it could be added

Before writing any code, confirm with the organisers: the API endpoint, authentication method,
whether a hosted model or a dataset is provided, rate limits, and whether Tamil is supported. Then:

1. Add the confirmed URL and key to `.env` (never to frontend code).
2. Add a backend endpoint that sends only the user's saved figures and returns the model's text.
3. Show the output labelled as AI-generated, next to (not in place of) the rule-based suggestions.
4. If the call fails or times out, show the existing "not available" message. The rest of the app
   must keep working.

## Future enhancements

- Login with hashed passwords and sessions; per-user privacy.
- Weekly consumption entries and a real week-over-week comparison.
- Bill photo or CSV import.
- Household groups or ward-level community goals.
- Tamil and other regional-language interface.
- Official emission-factor updates and tariff slabs.
- Frontend tests and deployment configuration.

## Demo checklist

1. Fresh start, onboarding with one reading, dashboard fills.
2. Add a second month, show change and chart; switch metric and range.
3. Enter an invalid value to show the error message.
4. Complete a mission; try again to show the duplicate is refused.
5. Run `flask --app app seed-demo`, show leaderboard with "Demo data" tags.
6. Change a solar assumption and recalculate.
7. Restart the backend and show data is still there.
8. Be ready to explain every formula (My Footprint and Solar pages list them).
