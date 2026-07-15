file_path = "enviro/fixtures/custom_html_block.json"
with open(file_path) as f:
	text = f.read()

# Vehicle Dashboard
text = text.replace(
	'.env-wrapper { font-family: -apple-system, BlinkMacSystemFont, \\"Segoe UI\\", sans-serif; background: #f9fafb; padding: 20px; border-radius: 8px; }',
	'.env-wrapper { display: flex; flex-direction: column; height: calc(100vh - 140px); font-family: -apple-system, BlinkMacSystemFont, \\"Segoe UI\\", sans-serif; background: #f9fafb; padding: 20px; border-radius: 8px; }\\n        .env-wrapper > div:not(.env-table-container):not(.env-grid) { flex-shrink: 0; }',
)

text = text.replace(
	".env-table-container { background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow-x: auto; border: 1px solid #f1f5f9; }",
	".env-table-container { flex: 1; background: white; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow-y: auto; overflow-x: auto; border: 1px solid #f1f5f9; }",
)

# Site Dashboard
text = text.replace(
	".env-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }",
	".env-grid { flex: 1; display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; overflow-y: auto; overflow-x: hidden; padding-bottom: 20px; align-content: start; }",
)

with open(file_path, "w") as f:
	f.write(text)
