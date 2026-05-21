import logging
import asyncio
import re
import threading
import time
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


def _run_filing_sync(
    lirs_username: str,
    lirs_password: str,
    tax_data: dict,
    tax_year: int,
    accommodation: dict,
    result_container: list
):
    screenshot_path = f"filing_preview_{tax_year}.png"
    last_error = ""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Filing attempt {attempt} of {MAX_RETRIES}")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # ── Login ──────────────────────────────────────────────────────
                page.goto("https://etax.lirs.net/login/", timeout=30000)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                page.get_by_placeholder("There should be a prefix 'N-' or 'C-'").fill(lirs_username)
                page.locator("input[type='password']").fill(lirs_password)
                page.get_by_role("button", name="Login").click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                logger.info("Logged in successfully")

                # ── Navigate to returns ────────────────────────────────────────
                page.goto("https://etax.lirs.net/user/returns", timeout=30000)
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # ── Click FILE RETURNS HERE ────────────────────────────────────
                page.get_by_role("button", name="FILE RETURNS HERE").click()
                page.wait_for_load_state("networkidle")
                time.sleep(2)

                # ── Select tax year ────────────────────────────────────────────
                page.locator(".md-select").first.click()
                time.sleep(2)
                page.locator(".md-list-item").filter(has_text=str(tax_year)).first.click()
                time.sleep(2)
                logger.info(f"Selected year {tax_year}")

                # ── Helper: fill text input by DOM index ───────────────────────
                def fill(index: int, value) -> None:
                    try:
                        f = page.locator("input.md-input").nth(index)
                        f.click()
                        f.press("Control+a")
                        f.press("Delete")
                        f.type(str(value))
                        logger.info(f"Filled input[{index}] = {value}")
                    except Exception as e:
                        logger.warning(f"Could not fill input[{index}]: {e}")

                # ── Helper: fill date field via calendar picker ────────────────
                def fill_date(index: int, value: str) -> None:
                    try:
                        parts = value.split("-")
                        target_year = parts[0]        # kept as str for .filter(has_text=)
                        target_month = int(parts[1])  # 1-based int
                        target_day = int(parts[2])

                        MONTHS = [
                            "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
                            "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
                        ]
                        target_month_name = MONTHS[target_month - 1]

                        # Step 1: Open calendar
                        page.locator("input.md-input").nth(index).click()
                        time.sleep(1)

                        # Step 2: Open year list and click target year — month grid appears immediately
                        page.locator(".md-datepicker-year-select").click()
                        time.sleep(1)
                        page.locator(".md-datepicker-year-button").filter(
                            has_text=target_year
                        ).click()
                        time.sleep(1)

                        # Step 3: Month grid is now visible — click target month directly
                        page.locator(".md-datepicker-month-button").filter(
                            has_text=target_month_name
                        ).click()
                        time.sleep(1)

                        # Step 4: Day grid is now visible — exact match to avoid "1" hitting "10", "21", etc.
                        page.locator(".md-datepicker-day-button").filter(
                            has_text=re.compile(rf"^\s*{target_day}\s*$")
                        ).first.click()
                        time.sleep(1)

                        logger.info(f"Selected date {value}")

                    except Exception as e:
                        logger.warning(f"Could not select date input[{index}]: {e}")

                # ── Helper: select ownership type dropdown ─────────────────────
                def select_ownership_type(value: str) -> None:
                    try:
                        page.locator(".md-select").nth(1).click()
                        time.sleep(1)
                        page.locator(".md-list-item").filter(has_text=value).first.click()
                        time.sleep(1)
                        logger.info(f"Selected Ownership Type = {value}")
                    except Exception as e:
                        logger.warning(f"Could not select ownership type: {e}")

                # ── Tab 1 — Income ─────────────────────────────────────────────
                logger.info("Filling Tab 1 — Income")
                income = tax_data.get("income_breakdown", {})

                fill(4,  income.get("salary_income", "0"))
                fill(5,  "0")   # Commission
                fill(6,  income.get("freelance_income", "0"))
                fill(7,  "0")   # Allowance
                fill(8,  tax_data.get("pension_deduction", "0"))
                fill(9,  "0")   # Annuity
                fill(10, "0")   # Gratuities
                fill(11, income.get("other_income", "0"))
                fill(12, income.get("dividend_income", "0"))
                fill(13, income.get("interest_income", "0"))
                fill(14, income.get("rent_income", "0"))

                page.get_by_role("button", name="NEXT").click()
                time.sleep(2)

                # ── Tab 2 — Accommodation ──────────────────────────────────────
                logger.info("Filling Tab 2 — Accommodation")

                fill(15, accommodation.get("address", ""))
                fill(16, accommodation.get("accommodation_type", ""))
                select_ownership_type(accommodation.get("ownership_type", "Tenant"))
                fill(18, accommodation.get("owner_name", "N/A"))
                fill(19, accommodation.get("owner_payer_id", ""))
                fill(20, accommodation.get("owner_address", "N/A"))
                fill(21, accommodation.get("rent_paid", "0"))
                fill(22, accommodation.get("rent_paid_by_employer", "0"))
                fill_date(23, accommodation.get("date_started", f"{tax_year}-01-01"))
                fill_date(24, accommodation.get("date_end", f"{tax_year}-12-31"))

                page.get_by_role("button", name="NEXT").click()
                time.sleep(2)

                # ── Tab 3 — Support Staff (skip) ───────────────────────────────
                logger.info("Skipping Tab 3 — Support Staff")
                page.get_by_role("button", name="NEXT").click()
                time.sleep(2)

                # ── Tab 4 — Assets (skip) ──────────────────────────────────────
                logger.info("Skipping Tab 4 — Assets")
                page.get_by_role("button", name="NEXT").click()
                time.sleep(2)

                # ── Tab 5 — Reliefs — STOP AND SCREENSHOT ─────────────────────
                logger.info("Reached Tab 5 — taking screenshot before submission")
                page.screenshot(path=screenshot_path, full_page=True)
                browser.close()

            result_container.append({
                "status": "pending_confirmation",
                "screenshot": screenshot_path,
                "message": "Filing ready. Verify the screenshot then call /api/v1/filing/confirm to submit.",
                "attempts": attempt,
            })
            return  # success — exit retry loop

        except Exception as e:
            last_error = str(e)
            logger.error(f"Attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(3)

    # All attempts exhausted
    result_container.append({
        "status": "error",
        "message": f"Filing failed after {MAX_RETRIES} attempts. Last error: {last_error}",
    })


async def run_filing(
    lirs_username: str,
    lirs_password: str,
    tax_data: dict,
    tax_year: int,
    accommodation: dict,
) -> dict:
    result_container = []

    thread = threading.Thread(
        target=_run_filing_sync,
        args=(
            lirs_username,
            lirs_password,
            tax_data,
            tax_year,
            accommodation,
            result_container,
        )
    )
    thread.start()
    await asyncio.get_event_loop().run_in_executor(None, thread.join)

    if result_container:
        return result_container[0]

    return {"status": "error", "message": "Filing thread produced no result"}