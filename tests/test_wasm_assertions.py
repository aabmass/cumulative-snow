import re

from playwright.sync_api import Page, expect


def test_load_plots(page: Page, port: int) -> None:
    page.goto(f"http://127.0.0.1:{port}")
    expect.set_options(timeout=60_000)
    expect(page.get_by_role("strong")).to_contain_text(
        "Select a station from the map or dropdown below"
    )
    expect(page.get_by_role("region", name="Map")).to_be_visible()
    page.get_by_test_id("marimo-plugin-searchable-dropdown").locator("div").filter(
        has_text=re.compile(r"^--$")
    ).click()
    page.get_by_test_id("marimo-plugin-searchable-dropdown").locator("div").filter(
        has_text=re.compile(r"^--$")
    ).click()
    page.get_by_placeholder("Search...").click()
    page.get_by_placeholder("Search...").fill("Boston")
    page.get_by_role("option", name="MA - BOSTON", exact=True).click()
    expect(page.get_by_text("WINTER_YEAR").first).to_be_visible()

    # Expect each of the plots to be visible
    for child_idx in range(2, 7):
        expect(
            page.locator(
                f"marimo-ui-element:nth-child({child_idx}) > marimo-plotly > .marimo > .contents > .w-full > .plot-container"
            )
        ).to_be_visible()
